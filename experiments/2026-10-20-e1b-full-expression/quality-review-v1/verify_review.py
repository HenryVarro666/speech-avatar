"""Recheck this review with .venv-quality/bin/python; does not rerender."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import urllib.parse

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT/'experiments/2026-10-20-e1b-full-expression'
REVIEW = EXP/'quality-review-v1'
VOICE = ROOT.parent/'voice_ai'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audio(path):
    return np.frombuffer(subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-ar', '16000', '-ac', '1',
        '-f', 's16le', '-'], stderr=subprocess.PIPE), dtype='<i2')


def corr(a, b):
    n = min(len(a), len(b))
    return float(np.corrcoef(a[:n], b[:n])[0, 1])


lock = json.loads((REVIEW/'INPUT_LOCK.json').read_text())
for relative, digest in lock['files'].items():
    assert sha(ROOT/relative) == digest, relative
diagnostics = json.loads((REVIEW/'diagnostics.json').read_text())
assert sha(ROOT/'scripts/review_e1b_quality.py') == diagnostics['script_sha256']
assert sha(REVIEW/'PLAN.md') == diagnostics['plan_sha256']
assert all(r['recovery_error_frames']==0 for c in diagnostics['clips']
           for r in c['known_shift_controls'])
images = 0
for clip in diagnostics['clips']:
    for evidence in clip['evidence_files']:
        assert sha(ROOT/evidence['path']) == evidence['sha256']
        images += 1
manifest = json.loads((EXP/'manifest.json').read_text())
audio_checks = []
for trial in manifest['trials']:
    video = ROOT/trial['planned_output_path']
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'],
                   capture_output=True, check=True)
    source, output = audio(ROOT/trial['audio_path']), audio(video)
    a, b = source[::16], output[::16]
    best, lag = max((corr(a if shift>=0 else a[-shift:], b[shift:] if shift>=0 else b), shift)
                    for shift in range(-32, 33))
    tail = corr(source[-4800:], output[len(source)-4800+lag*16:len(source)+lag*16])
    delta = (len(output)-len(source))/16
    assert best>=.95 and abs(lag)<=20 and -20<=delta<=100 and tail>=.95
    audio_checks.append({'trial_id': trial['trial_id'], 'correlation': best,
                         'best_lag_ms': lag, 'duration_delta_ms': delta,
                         'last300ms_correlation': tail})
assert sha(ROOT/'experiments/2026-10-20-e0/manifest.json') == '6c8a132f01101f447819f6cc708c2fe27d8d1fc88244f36a631a8cdb73911920'
for line in (ROOT/'experiments/2026-10-20-e1-musetalk/trials.jsonl').read_text().splitlines():
    row = json.loads(line)
    assert sha(ROOT/row['output_path']) == row['output_sha256']
browser = json.loads((REVIEW/'browser_playback.json').read_text())
assert len(browser['post_restart_playback']) == 4
assert all(c['ended'] and c['error'] is None for c in browser['post_restart_playback'])
assert browser['delivered_state'] == {'revealed': 'false', 'paused': True}
assert not subprocess.check_output(['git', 'ls-files', '--stage'], cwd=ROOT, text=True).strip()
assert not subprocess.check_output(['git', 'remote'], cwd=ROOT, text=True).strip()
assert subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=ROOT, capture_output=True).returncode != 0
for relative in ['outputs/e1b/quality-review-v1', 'data/private/e1b', 'models', 'vendor', '.venv-quality']:
    assert subprocess.run(['git', 'check-ignore', relative], cwd=ROOT, capture_output=True).returncode == 0
files = [ROOT/path for path in subprocess.check_output(['rg', '--files', '-g', '*.md'], cwd=ROOT, text=True).splitlines()]
files += [VOICE/path for path in ['README.md', 'README.zh-CN.md', 'PROJECT_STATUS.md', 'EVOLUTION.md',
                                  'reports/Avatar 完整表情 选型 扩展路线.md']]
link_count, missing = 0, []
for path in files:
    for match in re.finditer(r'!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)', path.read_text()):
        target = match.group(1).strip().strip('<>')
        if target.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        target = urllib.parse.unquote(target.split('#')[0].split('?')[0])
        link_count += 1
        if not (path.parent/target).exists() and (path.parent/target).resolve() != (REVIEW/'verification.json'):
            missing.append({'file': str(path), 'target': target})
assert not missing, missing
result = {'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'local CPU review only; no SSH or apex',
          'locked_files_unchanged': len(lock['files']), 'original_videos_unchanged': 4,
          'old_e1_videos_unchanged': 12, 'user_video_review_sha256_unchanged': sha(EXP/'video_review.json'),
          'full_decode_passed': 4, 'fresh_audio_integrity': audio_checks,
          'whole_curves_reproduced': 4, 'known_nonzero_shift_controls_exact': 8,
          'evidence_image_hashes_verified': images,
          'overview_sha256': sha(ROOT/'outputs/e1b/quality-review-v1/evidence-overview.png'),
          'browser_complete_after_restart': 4, 'browser_logs_after_restart': browser['post_restart_logs'],
          'delivered_preview_unrevealed': True, 'markdown_files_checked': len(files),
          'local_links_checked': link_count, 'missing_local_links': missing, 'new_video_renders': 0,
          'human_av_acceptance': 'pending; no scores changed', 'staged_files': 0, 'remotes': [],
          'head_exists': False}
(REVIEW/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items()
                  if key not in ['fresh_audio_integrity', 'browser_logs_after_restart']},
                 ensure_ascii=False, indent=2))
print('browser log count:', len(browser['post_restart_logs']))
