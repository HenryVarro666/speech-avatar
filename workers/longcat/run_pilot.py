"""Pinned native LongCat single-GPU CLI with observation-only E1b hooks."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_common import append_result, check_gpu, digest, open_job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job', required=True)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    root, manifest, trial = open_job(args.job)
    assert trial['backend'] == 'longcat-avatar-v15-int8-distill'
    run = root/'runs'/trial['trial_id']/f'attempt-{args.attempt:03d}'
    run.mkdir(parents=True, exist_ok=False)
    source = root/'vendor/LongCat-Video'
    config = manifest['backends'][trial['backend']]
    record = {**trial, 'attempt': args.attempt, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'pid': os.getpid(), 'manifest_sha256': digest(root/'manifest.json'),
              'worker_sha256': digest(Path(__file__)), 'model_manifest_sha256': digest(root/'model_manifest.json'),
              'first_saved_frame_s': None, 'first_completed_segment_file_s': None,
              'status': 'failed', 'human_av_review': None, 'stages': []}
    start = time.perf_counter()
    try:
        sys.path.insert(0, str(source))
        os.chdir(run)
        import soundfile as sf
        import torch
        torch.set_num_threads(4)
        # NCCL's initial context may not appear in NVML's compute-process list.
        # Register ownership before the long CPU-only weight load, so the other
        # experiment's existing PID-based idle checks can see this reservation.
        reservation = torch.empty(1, device='cuda:0')
        torch.cuda.synchronize()
        selected = os.environ['CUDA_VISIBLE_DEVICES']
        for _ in range(10):
            snapshot = check_gpu()
            if any(line.split(',')[0].strip() == selected and
                   int(line.split(',')[1]) == os.getpid() for line in snapshot.splitlines()):
                record['gpu_reservation_observed'] = True
                break
            time.sleep(0.2)
        else:
            raise RuntimeError('GPU reservation was not visible to the shared PID-based idle check')
        print('GPU_RESERVATION_REGISTERED', os.getpid(), selected, flush=True)
        import run_demo_avatar_single_audio_to_video as upstream

        original_extract = upstream.extract_vocal_from_speech

        def observe_vocals(*positional, **keywords):
            path = original_extract(*positional, **keywords)
            if path:
                saved = run/'conditioning-vocals.wav'
                shutil.copyfile(path, saved)
                info = sf.info(saved)
                record['separator_audio'] = {'path': str(saved.relative_to(root)),
                    'sha256': digest(saved), 'sample_rate_hz': info.samplerate,
                    'duration_s': info.duration, 'known_offset_s': None}
            return path

        upstream.extract_vocal_from_speech = observe_vocals
        original_embedding = upstream.LongCatVideoAvatarPipeline.get_audio_embedding

        def observe_embedding(self, speech_array, *positional, **keywords):
            saved = run/'conditioning-padded.wav'
            rate = keywords['sample_rate']
            sf.write(saved, speech_array, rate, subtype='FLOAT')
            record['conditioning_audio'] = {'path': str(saved.relative_to(root)),
                'sha256': digest(saved), 'sample_rate_hz': rate, 'duration_s': len(speech_array)/rate,
                'transform': 'native vocal separation, librosa16k resample, native zero padding to generated coverage'}
            return original_embedding(self, speech_array, *positional, **keywords)

        upstream.LongCatVideoAvatarPipeline.get_audio_embedding = observe_embedding
        for method in ['generate_ai2v', 'generate_avc']:
            original = getattr(upstream.LongCatVideoAvatarPipeline, method)

            def observed(self, *positional, _original=original, _name=method, **keywords):
                check_gpu()
                torch.cuda.synchronize()
                began = time.perf_counter()
                value = _original(self, *positional, **keywords)
                torch.cuda.synchronize()
                record['stages'].append({'name': _name, 'wall_s': time.perf_counter()-began})
                return value

            setattr(upstream.LongCatVideoAvatarPipeline, method, observed)
        original_save = upstream.save_video_ffmpeg

        def observe_save(*positional, **keywords):
            value = original_save(*positional, **keywords)
            if record['first_completed_segment_file_s'] is None:
                record['first_completed_segment_file_s'] = time.perf_counter()-start
            return value

        upstream.save_video_ffmpeg = observe_save
        inputs = run/'input.json'
        inputs.write_text(json.dumps({'prompt': config['prompt'], 'cond_image': str(root/trial['image_path']),
                                     'cond_audio': {'person1': str(root/trial['audio_path'])}}))
        options = SimpleNamespace(input_json=str(inputs),
            checkpoint_dir=str(root/'weights/LongCat-Video-Avatar-1.5'), context_parallel_size=1,
            stage_1='ai2v', num_inference_steps=8, text_guidance_scale=1.0, audio_guidance_scale=1.0,
            resolution='480p', num_segments=trial['num_segments'], output_dir=str(run/'render'),
            model_type='avatar-v1.5', use_distill=True, use_int8=True, ref_img_index=10, mask_frame_range=3)
        upstream.generate(options)
        torch.cuda.synchronize()
        check_gpu()
        native = run/'render'/f"video_continue_{trial['num_segments']}.mp4"
        if not native.exists():
            raise RuntimeError('native continuation output missing')
        target = root/trial['planned_output_path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        shutil.copyfile(native, target)
        record.update(status='rendered_pending_validation', output_sha256=digest(target),
            peak_torch_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_torch_reserved_mib=torch.cuda.max_memory_reserved()/2**20)
    except Exception as error:
        record['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        record['worker_wall_s'] = time.perf_counter()-start
        record['timing_scope'] = 'before heavy imports to completed output copy; includes all model loads, native separation, both segments and encoding; observation hooks synchronize CUDA'
        append_result(root, record)
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
