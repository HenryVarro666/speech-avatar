"""Local-only final integrity checks; no inference or remote access."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
OLD = ROOT / 'experiments/2026-10-20-e1b-full-expression'
sys.path.insert(0, str(ROOT / 'scripts'))
import make_sync_variants as sync


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def pcm(path):
    with wave.open(str(path), 'rb') as f:
        return f.getparams(), f.readframes(f.getnframes())


def audio(path):
    return np.frombuffer(subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-ar', '16000', '-ac', '1',
        '-f', 's16le', '-'], stderr=subprocess.PIPE), dtype='<i2')


def corr(a, b):
    n = min(len(a), len(b))
    return float(np.corrcoef(a[:n], b[:n])[0, 1])


manifest = read(EXP / 'manifest.json')
assert sha(EXP / 'manifest.json') == (EXP / 'manifest.sha256').read_text().split()[0]
assert sha(EXP / 'QUALITY_PROTOCOL.md') == (EXP / 'QUALITY_PROTOCOL.sha256').read_text().split()[0]
assert sha(ROOT / 'experiments/2026-10-20-e0/manifest.json') == manifest['e0_manifest_sha256']
assert sha(EXP / 'audio_review.json') == manifest['audio_review_sha256']
assert sha(OLD / 'audio_review.json') == manifest['audio_review_sha256']
lock = read(OLD / 'quality-review-v1/INPUT_LOCK.json')
assert all(sha(ROOT / p) == h for p, h in lock['files'].items())
old_e1 = [json.loads(x) for x in (ROOT / 'experiments/2026-10-20-e1-musetalk/trials.jsonl').read_text().splitlines()]
assert len(old_e1) == 12
assert all(sha(ROOT / x['output_path']) == x['output_sha256'] for x in old_e1)
parent = read(OLD / 'manifest.json')
assert manifest['roles'] == parent['roles']
key = 'longcat-avatar-v15-int8-distill'
assert {k: v for k, v in manifest['backends'][key].items() if k != 'prompt'} == {
    k: v for k, v in parent['backends'][key].items() if k != 'prompt'}
assert manifest['backends'][key]['prompt'] != parent['backends'][key]['prompt']
for t in manifest['trials']:
    for field in ['audio', 'image', 'reference']:
        assert sha(ROOT / t[field + '_path']) == t[field + '_sha256']
    inp = read(EXP / 'executed_inputs' / (t['trial_id'] + '.json'))
    assert inp['prompt'] == manifest['backends'][key]['prompt']
    assert inp['cond_image'].endswith('/' + t['image_path'])
    assert inp['cond_audio']['person1'].endswith('/' + t['audio_path'])
for row in read(EXP / 'conditioning_local.json'):
    assert sha(ROOT / row['local_path']) == row['sha256']

variants = read(EXP / 'sync_variants.json')
assert variants['script_sha256'] == sha(ROOT / 'scripts/make_sync_variants.py')
assert len(variants['variants']) == 6 and variants['gpu_model_generations'] == 0
original_frames = {}
preservation = []
for row in variants['variants']:
    t = next(t for t in parent['trials'] if t['trial_id'] == row['parent_trial_id'])
    assert sha(ROOT / t['planned_output_path']) == row['parent_video_sha256']
    assert sha(ROOT / t['audio_path']) == row['parent_audio_sha256']
    assert sha(ROOT / row['output_path']) == row['output_sha256']
    assert sha(ROOT / row['derived_wav_path']) == row['derived_wav_sha256']
    original = original_frames.setdefault(t['trial_id'], None)
    if original is None:
        original = sync.raw_frames(ROOT / t['planned_output_path'])
        original_frames[t['trial_id']] = original
    output = sync.raw_frames(ROOT / row['output_path'])
    padding = row['video_padding_frames']
    assert output[padding:] == original
    assert all(f == original[0] for f in output[:padding])
    params, speech = pcm(ROOT / t['audio_path'])
    derived_params, derived = pcm(ROOT / row['derived_wav_path'])
    assert (derived_params.nchannels, derived_params.sampwidth, derived_params.framerate) == (1, 2, 24000)
    assert derived == speech + b'\0' * (row['appended_zero_samples'] * 2)
    preservation.append({'id': row['id'], 'all_source_frames_identical': True,
                         'speech_pcm_unchanged': True, 'exact_zero_tail': True})

fresh_audio = []
for stage in ['qsync', 'qmotion']:
    checked = read(EXP / (stage + '_quality.json'))
    assert checked['script_sha256'] == sha(ROOT / 'scripts/analyze_e1c.py')
    assert checked['protocol_sha256'] == sha(EXP / 'QUALITY_PROTOCOL.md')
    assert checked['manifest_sha256'] == sha(EXP / 'manifest.json')
    for c in checked['checks']:
        if stage == 'qsync':
            row = next(r for r in variants['variants'] if r['id'] == c['trial_id'])
            video = ROOT / row['output_path']
            reference = ROOT / row['derived_wav_path']
        else:
            row = next(r for r in manifest['trials'] if r['trial_id'] == c['trial_id'])
            video = ROOT / row['planned_output_path']
            reference = ROOT / row['audio_path']
        assert sha(video) == c['output_sha256']
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'],
                       check=True, capture_output=True)
        source, actual = audio(reference), audio(video)
        source_speech = source[:int(c['source_audio_duration_s'] * 16000)]
        a, b = source_speech[::16], actual[::16]
        best, lag = max((corr(a if i >= 0 else a[-i:], b[i:] if i >= 0 else b), i)
                        for i in range(-32, 33))
        end = len(source_speech)
        tail = corr(source_speech[-4800:], actual[end - 4800 + lag * 16:end + lag * 16])
        delta = (len(actual) - len(source)) / 16
        assert best >= .95 and abs(lag) <= 20 and tail >= .95 and -20 <= delta <= 100
        fresh_audio.append({'id': c['trial_id'], 'full_decode': True, 'correlation': best,
                            'lag_ms': lag, 'last300ms': tail, 'duration_delta_ms': delta})
motion = read(EXP / 'qmotion_quality.json')
assert sum(x['face_frames_detected'] for x in motion['checks']) == 258
assert all(x['multi_detection_frames'] == 0 for x in motion['checks'])
processes = [json.loads(x) for x in (EXP / 'video_process_results.jsonl').read_text().splitlines()]
assert len(processes) == 2 and all(p['exit_code'] == 0 and p['attempt'] == 1 for p in processes)
attempts = [json.loads(x) for x in (EXP / 'video_attempts.jsonl').read_text().splitlines()]
assert all(a['worker_sha256'] == sha(EXP / 'executed_workers/longcat/run_pilot.py') for a in attempts)
assert all(a['model_manifest_sha256'] == sha(EXP / 'video_model_manifest.json') for a in attempts)
gate = read(EXP / 'gate_review.json')
assert gate['qtail_model_generations'] == 0 and gate['qtail_status'] == 'skipped_gate_not_met'
assert not list((ROOT / 'outputs/e1c').glob('qtail/*.mp4'))
user = read(EXP / 'user_review.json')
assert all(user[k] is None for k in ['reviewer', 'sync_preference', 'motion_acceptance'])

preview = read(EXP / 'preview_manifest.json')
url = read(EXP / 'preview_server.json')['url']
served = set()
for g in preview['groups']:
    for position in range(3):
        assert len({r[position]['variant_id'] for r in g['sync_rounds']}) == 3
    for c in g['motion'] + [c for r in g['sync_rounds'] for c in r]:
        assert sha(ROOT / 'outputs/e1c' / c['filename']) == c['sha256']
        if c['filename'] not in served:
            with urllib.request.urlopen(url.rsplit('/', 1)[0] + '/' + c['filename'], timeout=10) as response:
                assert hashlib.sha256(response.read()).hexdigest() == c['sha256']
            served.add(c['filename'])
assert [c['reveal'] for c in preview['groups'][0]['motion']] == [c['reveal'] for c in preview['groups'][1]['motion']][::-1]
browser = read(EXP / 'browser_playback.json')
assert len(browser['playback']) == 10 and all(c['ended'] and c['error'] is None for c in browser['playback'])
assert len(browser['rounds']) == 3
assert len([v for v in browser['exclusive'] if not v['paused']]) == 1
assert browser['stop_all_pauses'] and browser['final_ui']['allPaused']
assert browser['final_ui']['round'] == '当前第1轮 / 共3轮'
assert browser['final_ui']['unrevealed'].startswith('当前未揭示')
assert not subprocess.check_output(['git', 'ls-files', '--stage'], cwd=ROOT, text=True).strip()
assert not subprocess.check_output(['git', 'remote'], cwd=ROOT, text=True).strip()
assert subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=ROOT, capture_output=True).returncode != 0
for p in ['outputs/e1c', 'data/private/e1c', 'models', 'vendor', '.venv-quality', '.cache']:
    assert subprocess.run(['git', 'check-ignore', p], cwd=ROOT, capture_output=True).returncode == 0

files = [ROOT / p for p in subprocess.check_output(
    ['rg', '--files', '-g', '*.md'], cwd=ROOT, text=True).splitlines()]
voice = ROOT.parent / 'voice_ai'
files += [voice / p for p in ['PROJECT_STATUS.md', 'EVOLUTION.md', 'reports/Avatar 完整表情 选型 扩展路线.md']]
links, missing = 0, []
for p in files:
    for m in re.finditer(r'!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)', p.read_text()):
        target = m.group(1).strip().strip('<>')
        if target.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        target = urllib.parse.unquote(target.split('#')[0].split('?')[0])
        links += 1
        if not (p.parent / target).exists() and (p.parent / target).resolve() != EXP / 'final_checks.json':
            missing.append({'file': str(p), 'target': target})
assert not missing, missing
env = read(EXP / 'environment-after.json')
assert not env['own_workers'].strip()
assert 'GPU-d8788c54-b9da-d038-e5bc-aa3b718ef62c' not in env['compute']
assert '2154793' in env['compute']
result = {'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'verification_scope': 'local integrity/decode/audio/HTTP checks; no new model inference or SSH',
          'parent_locked_files_unchanged': len(lock['files']), 'old_e1_videos_unchanged': 12,
          'original_audio_and_portraits_unchanged': True, 'executed_new_prompt_verified': 2,
          'only_backend_config_change': 'positive prompt', 'conditioning_hashes_verified': 4,
          'fresh_sync_frame_pcm_checks': preservation, 'fresh_decode_audio_checks': fresh_audio,
          'qmotion_single_face_frames': 258, 'qmotion_attempts_success': 2, 'qtail_generations': 0,
          'served_media_hashes': len(served), 'browser_ended': 10, 'balanced_rotations': 3,
          'single_audio_and_pause_all': True, 'delivered_unrevealed': True,
          'environment_snapshot_utc': env['captured_utc'], 'own_gpu_workers_exited_in_snapshot': True,
          'gpu1_compute_processes_in_snapshot': 0, 'gpu0_foreign_arrivals_untouched': True,
          'markdown_files_checked': len(files), 'local_links_checked': links, 'missing_local_links': missing,
          'human_av_acceptance': 'pending; no user scores written', 'head_exists': False,
          'staged_files': 0, 'remotes': [],
          'artifact_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [
              EXP / f for f in ['manifest.json', 'QUALITY_PROTOCOL.md', 'qsync_quality.json',
                               'qmotion_quality.json', 'sync_variants.json', 'gate_review.json',
                               'browser_playback.json', 'user_review.json', 'RESULTS.md']]}}
(EXP / 'final_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['fresh_sync_frame_pcm_checks',
    'fresh_decode_audio_checks', 'artifact_sha256']}, ensure_ascii=False, indent=2))
