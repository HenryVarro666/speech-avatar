"""E1b MuseTalk entry; keeps the original E1 worker and outputs untouched."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
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
    assert trial['backend'] == 'musetalk-v15'
    run = root / 'runs' / trial['trial_id'] / f'attempt-{args.attempt:03d}'
    run.mkdir(parents=True, exist_ok=False)
    result = run / 'render'
    result.mkdir()
    source = root / 'vendor/MuseTalk'
    record = {**trial, 'attempt': args.attempt, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'pid': os.getpid(), 'manifest_sha256': digest(root/'manifest.json'),
              'worker_sha256': digest(Path(__file__)), 'first_saved_frame_s': None,
              'status': 'failed', 'human_av_review': None}
    start = time.perf_counter()
    try:
        sys.path[:0] = [str(source), str(source/'musetalk/utils')]
        os.chdir(source)
        import numpy as np
        import torch
        torch.set_num_threads(4)
        random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.cuda.manual_seed_all(42)
        import scripts.inference as upstream
        import cv2
        config = run/'inference.json'
        config.write_text(json.dumps({trial['trial_id']: {
            'video_path': str(root/trial['reference_path']),
            'audio_path': str(root/trial['audio_path']),
            'result_name': trial['trial_id']+'.mp4'}}))
        original_write = cv2.imwrite

        def observed_write(filename, *positional, **keywords):
            success = original_write(filename, *positional, **keywords)
            if success and str(filename).startswith(str(result)) and record['first_saved_frame_s'] is None:
                record['first_saved_frame_s'] = time.perf_counter() - start
            return success

        cv2.imwrite = observed_write
        check_gpu()
        options = SimpleNamespace(ffmpeg_path='/data/speech-avatar-exx-20261020/bin', gpu_id=0,
            vae_type='sd-vae', unet_config='models/musetalkV15/musetalk.json',
            unet_model_path='models/musetalkV15/unet.pth', whisper_dir='models/whisper',
            inference_config=str(config), bbox_shift=0, result_dir=str(result), extra_margin=10,
            fps=25, audio_padding_length_left=2, audio_padding_length_right=2, batch_size=8,
            output_vid_name=None, use_saved_coord=False, saved_coord=False, use_float16=True,
            parsing_mode='jaw', left_cheek_width=90, right_cheek_width=90, version='v15')
        upstream.main(options)
        torch.cuda.synchronize()
        check_gpu()
        output = result/'v15'/(trial['trial_id']+'.mp4')
        if not output.exists():
            raise RuntimeError('upstream did not produce the final video')
        target = root/trial['planned_output_path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        shutil.copyfile(output, target)
        record.update(status='rendered_pending_validation', output_sha256=digest(target),
            peak_torch_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_torch_reserved_mib=torch.cuda.max_memory_reserved()/2**20)
    except Exception as error:
        record['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        record['worker_wall_s'] = time.perf_counter()-start
        record['timing_scope'] = 'before heavy imports to completed output copy; includes all model loads, rendering and encoding; excludes process startup'
        append_result(root, record)
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
