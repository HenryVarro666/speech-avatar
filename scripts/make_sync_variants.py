"""Versioned E1c sync derivatives: delay picture, keep accepted speech PCM."""
import hashlib
import json
from pathlib import Path
import subprocess
import wave


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def video_info(path):
    data = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)]))
    stream = next(s for s in data['streams'] if s['codec_type']=='video')
    if stream['avg_frame_rate']!='25/1' or stream['pix_fmt']!='yuv420p':
        raise ValueError('This experiment requires25fps/yuv420p source')
    return stream['width'], stream['height']


def raw_frames(path):
    width, height = video_info(path)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                   '-map', '0:v:0', '-pix_fmt', 'yuv420p',
                                   '-f', 'rawvideo', '-'], stderr=subprocess.PIPE)
    size = width*height*3//2
    assert len(raw)%size==0
    return [raw[i:i+size] for i in range(0, len(raw), size)]


def make_variant(video, audio, target, derived_wav, video_delay_ms):
    video, audio, target, derived_wav = map(Path, [video, audio, target, derived_wav])
    if target.exists() or derived_wav.exists():
        raise FileExistsError('Never overwrite a sync derivative')
    if video_delay_ms not in [0, 40, 80]:
        raise ValueError('Only frozen0/40/80ms picture delays are allowed')
    padding = video_delay_ms//40
    original = raw_frames(video)
    with wave.open(str(audio), 'rb') as source:
        params = source.getparams()
        if (params.nchannels, params.sampwidth, params.framerate)!=(1, 2, 24000):
            raise ValueError('Keep accepted24k monoPCM16 speech')
        speech = source.readframes(params.nframes)
    if abs(params.nframes/24000-len(original)/25)>1/24000:
        raise ValueError('Source waveform and picture must cover the same duration')
    target.parent.mkdir(parents=True, exist_ok=True)
    derived_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(derived_wav), 'wb') as out:
        out.setparams(params)
        out.writeframes(speech+b'\0'*(padding*960*2))
    command = ['ffmpeg', '-v', 'error', '-n', '-i', str(video), '-i', str(derived_wav),
               '-map', '0:v:0', '-map', '1:a:0', '-vf',
               f'tpad=start={padding}:start_mode=clone', '-c:v', 'libx264', '-crf', '0',
               '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '320k',
               '-ar', '24000', '-movflags', '+faststart', str(target)]
    subprocess.run(command, capture_output=True, check=True)
    actual = raw_frames(target)
    if actual[padding:]!=original or not all(f==original[0] for f in actual[:padding]):
        raise ValueError('Derived picture changed a source frame')
    return {'parent_video_sha256': sha(video), 'parent_audio_sha256': sha(audio),
            'output_sha256': sha(target), 'derived_wav_sha256': sha(derived_wav),
            'video_delay_ms': video_delay_ms, 'video_padding_frames': padding,
            'source_frame_count': len(original), 'derived_frame_count': len(actual),
            'source_audio_samples': params.nframes, 'appended_zero_samples': padding*960,
            'all_source_video_frames_identical': True, 'source_speech_pcm_unchanged': True,
            'derived_duration_s': (len(original)+padding)/25,
            'codec': 'losslessH264/yuv420p; AAC320k24kHz; source PCM preserved in derivativeWAV',
            'time_mapping': 'video_source_t -> output_t+delay; source_audio_t -> output_t',
            'command': command}


def main():
    root = Path(__file__).resolve().parents[1]
    parent = root/'experiments/2026-10-20-e1b-full-expression'
    exp = root/'experiments/2026-10-21-e1c-controlled-expression'
    ledger = exp/'sync_variants.json'
    if ledger.exists():
        raise FileExistsError('Preserve existing calibration ledger')
    manifest = json.loads((parent/'manifest.json').read_text())
    rows = []
    for trial in manifest['trials']:
        if not trial['backend'].startswith('longcat'):
            continue
        role = 'female' if trial['avatar_id']=='avatar-a' else 'male'
        for delay in [0, 40, 80]:
            ident = f'{role}-video-delay-{delay:03d}ms'
            target = root/'outputs/e1c/qsync'/(ident+'.mp4')
            wav = root/'data/private/e1c/qsync'/(ident+'.wav')
            row = make_variant(root/trial['planned_output_path'], root/trial['audio_path'],
                               target, wav, delay)
            rows.append({'id': ident, 'role': role, 'parent_trial_id': trial['trial_id'],
                         'output_path': str(target.relative_to(root)),
                         'derived_wav_path': str(wav.relative_to(root)), **row})
            print(json.dumps({'id': ident, 'frames': row['derived_frame_count'],
                              'duration': row['derived_duration_s']}), flush=True)
    ledger.write_text(json.dumps({'status': 'prepared_pending_user_sync_preference',
        'script_sha256': sha(__file__), 'gpu_model_generations': 0, 'variants': rows}, indent=2)+'\n')


if __name__=='__main__':
    main()
