"""Frozen E1b input checks shared by the two small offline workers."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def required_segments(duration_s):
    return 1 + math.ceil(max(0, duration_s * 25 - 93) / 80)


def load_trial(root, trial_id):
    root = Path(root).resolve()
    path = root / 'manifest.json'
    if digest(path) != (root / 'manifest.sha256').read_text().split()[0]:
        raise ValueError('manifest hash mismatch')
    manifest = json.loads(path.read_text())
    review_path = root / 'audio_review.json'
    if digest(review_path) != manifest['audio_review_sha256']:
        raise ValueError('review hash mismatch')
    trial = next(row for row in manifest['trials'] if row['trial_id'] == trial_id)
    for kind in ['audio', 'image', 'reference']:
        if digest(root / trial[kind + '_path']) != trial[kind + '_sha256']:
            raise ValueError(kind + ' hash mismatch')
    review = next(row for row in json.loads(review_path.read_text())['clips']
                  if row['audio_id'] == trial['audio_id'])
    if review['accepted'] is not True or review['reviewed_audio_sha256'] != trial['audio_sha256']:
        raise ValueError('voice not accepted with matching hash')
    if trial['backend'].startswith('longcat'):
        if trial['num_segments'] < required_segments(trial['audio_duration_s']):
            raise ValueError('insufficient video coverage')
    if (root / trial['planned_output_path']).exists():
        raise FileExistsError(root / trial['planned_output_path'])
    return manifest, trial


def check_gpu():
    selected = os.environ['CUDA_VISIBLE_DEVICES']
    if not selected.startswith('GPU-'):
        raise ValueError('Select the checked physical GPU UUID')
    output = subprocess.check_output(
        ['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True,
    )
    for line in output.splitlines():
        fields = [field.strip() for field in line.split(',')]
        if len(fields) != 2 or not fields[1].isdigit():
            raise ValueError('unrecognized GPU query')
        if fields[0] == selected and int(fields[1]) != os.getpid():
            raise RuntimeError(f'External GPU process detected; selected={selected}, other_pid={fields[1]}, own_pid={os.getpid()}, query={output.strip()!r}; worker will not touch it')
    return output.strip()


def assert_media_tools():
    for name in ['ffmpeg', 'ffprobe']:
        if shutil.which(name) is None:
            raise RuntimeError('Missing required media executable: ' + name)


def open_job(path):
    descriptor = json.loads(Path(path).read_text())
    root = Path(descriptor['root'])
    manifest, trial = load_trial(root, descriptor['trial_id'])
    assert_media_tools()
    check_gpu()
    return root, manifest, trial


def append_result(root, record):
    with (root / 'attempts.jsonl').open('a') as out:
        out.write(json.dumps(record, ensure_ascii=False) + '\n')
