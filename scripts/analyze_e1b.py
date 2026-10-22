"""Local E1b media validation, dynamic face tracks and auxiliary SyncNet metrics."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import torch

import audit_e1_quality as sync

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT/'experiments/2026-10-20-e1b-full-expression'
OUT = ROOT/'outputs/e1b'


def corr(a, b):
    n = min(len(a), len(b))
    return float(np.corrcoef(a[:n], b[:n])[0, 1]) if n else 0.0


def overlap(a, b):
    x1, y1 = np.maximum(a[:2], b[:2])
    x2, y2 = np.minimum(a[2:], b[2:])
    intersection = max(0, x2-x1)*max(0, y2-y1)
    union = np.prod(a[2:]-a[:2])+np.prod(b[2:]-b[:2])-intersection
    return float(intersection/union) if union else 0


def track(detector, frames):
    boxes, counts = [], []
    previous = None
    for frame in frames:
        found = detector.detect_faces(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                                      conf_th=0.9, scales=[0.25])
        counts.append(len(found))
        if len(found) == 0:
            boxes.append(None)
            continue
        candidates = found[:, :4]
        if previous is None:
            selected = max(candidates, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))
        else:
            selected = max(candidates, key=lambda b: overlap(b, previous))
        previous = selected
        boxes.append(selected.tolist())
    if any(box is None for box in boxes):
        return boxes, None, counts
    raw = np.asarray(boxes)
    smooth = np.stack([np.median(raw[max(0, i-6):min(len(raw), i+7)], axis=0)
                       for i in range(len(raw))])
    return boxes, smooth, counts


def evidence(frames, boxes, ident):
    Image.fromarray(cv2.cvtColor(frames[0], cv2.COLOR_BGR2RGB)).save(OUT/'quality'/(ident+'-poster.png'))
    sheet = Image.new('RGB', (8*144, math.ceil(len(frames)/8)*120), '#e4e6ea')
    full = Image.new('RGB', (4*192, 4*214), '#e4e6ea')
    ids = np.rint(np.linspace(0, len(frames)-1, 16)).astype(int)
    for i, frame in enumerate(frames):
        box = boxes[i] if boxes is not None else None
        if box is not None:
            x1, y1, x2, y2 = box
            w, h = x2-x1, y2-y1
            left, right = max(0, int(x1+.15*w)), min(frame.shape[1], int(x2-.15*w))
            top, bottom = max(0, int(y1+.52*h)), min(frame.shape[0], int(y2+.10*h))
            mouth = frame[top:bottom, left:right]
        else:
            mouth = frame
        tile = Image.new('RGB', (144, 120), 'white')
        tile.paste(Image.fromarray(cv2.cvtColor(mouth, cv2.COLOR_BGR2RGB)).resize((144, 96)), (0, 24))
        ImageDraw.Draw(tile).text((3, 4), f'f{i:03d} {i/25:.2f}s', fill='black')
        sheet.paste(tile, ((i % 8)*144, (i//8)*120))
    for j, i in enumerate(ids):
        tile = Image.new('RGB', (192, 214), 'white')
        picture = ImageOps.pad(Image.fromarray(cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)),
                               (192, 192), color='#101722')
        tile.paste(picture, (0, 22))
        ImageDraw.Draw(tile).text((3, 3), f'f{i:03d} {i/25:.2f}s', fill='black')
        full.paste(tile, ((j % 4)*192, (j//4)*214))
    sheet.save(OUT/'quality'/(ident+'-mouths.png'))
    full.save(OUT/'quality'/(ident+'-faces.png'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-seconds', type=int, default=0,
                        help='Allow remaining frozen outputs to arrive while earlier clips are analyzed')
    args = parser.parse_args()
    target = EXP/'video_validation.json'
    if target.exists():
        raise FileExistsError('Retain earlier metrics; use a new review path for reruns')
    protocol = EXP/'VIDEO_QUALITY_PROTOCOL.md'
    assert sync.sha(protocol) == (EXP/'VIDEO_QUALITY_PROTOCOL.sha256').read_text().split()[0]
    manifest = json.loads((EXP/'manifest.json').read_text())
    assert sync.sha(EXP/'manifest.json') == (EXP/'manifest.sha256').read_text().split()[0]
    torch.set_num_threads(4)
    model = sync.S().eval()
    model.load_state_dict(torch.load(ROOT/'models/syncnet/syncnet_v2.model', map_location='cpu', weights_only=True))
    cwd = os.getcwd(); os.chdir(sync.VENDOR)
    detector = sync.S3FD(device='cpu'); os.chdir(cwd)
    (OUT/'quality').mkdir(exist_ok=True)
    checks, tracking = [], {}
    for trial in manifest['trials']:
        ident = trial['trial_id']
        video = ROOT/trial['planned_output_path']
        deadline = time.monotonic()+args.wait_seconds
        while not video.exists() and time.monotonic()<deadline:
            time.sleep(2)
        attempts = [json.loads(line) for line in (EXP/'video_attempts.jsonl').read_text().splitlines()]
        row = next(r for r in reversed(attempts) if r['trial_id'] == ident and r['status']=='rendered_pending_validation')
        assert sync.sha(video) == row['output_sha256']
        assert sync.sha(ROOT/trial['audio_path']) == trial['audio_sha256']
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'],
                       capture_output=True, check=True)
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                                    '-show_format', '-of', 'json', str(video)]))
        stream = next(s for s in probe['streams'] if s['codec_type']=='video')
        original, output = sync.audio(ROOT/trial['audio_path']), sync.audio(video)
        values = []
        a, b = original[::16], output[::16]
        for lag in range(-32, 33):
            values.append((corr(a if lag >= 0 else a[-lag:], b[lag:] if lag >= 0 else b), lag))
        best, lag = max(values)
        tail_start = len(original)-4800
        shifted_start, shifted_end = tail_start+lag*16, len(original)+lag*16
        tail = corr(original[tail_start:], output[max(0,shifted_start):min(len(output),shifted_end)])
        delta = (len(output)-len(original))/16
        frames = sync.read_video(video)
        raw, boxes, counts = track(detector, frames)
        score = None
        if boxes is not None:
            crops = np.concatenate([sync.face_crops(frames[i:i+1], box) for i, box in enumerate(boxes)])
            vf, af = sync.features(model, crops, output)
            score = sync.official_score(vf, af)
        tracking[ident] = {'raw_boxes': raw, 'smoothed_boxes': boxes.tolist() if boxes is not None else None,
                           'detections_per_frame': counts}
        evidence(frames, boxes, ident)
        record = {'trial_id': ident, 'backend': trial['backend'], 'output_sha256': row['output_sha256'],
            'full_decode': True, 'width': stream['width'], 'height': stream['height'],
            'fps': stream['avg_frame_rate'], 'decoded_frames': len(frames),
            'source_duration_s': len(original)/16000, 'decoded_audio_duration_s': len(output)/16000,
            'decoded_audio_delta_ms': delta, 'audio_correlation': best, 'best_audio_lag_ms': lag,
            'last_300ms_audio_correlation': tail,
            'audio_integrity_passed': best>=.95 and abs(lag)<=20 and -20<=delta<=100 and tail>=.95,
            'face_frames_detected': sum(c>0 for c in counts), 'multi_detection_frames': sum(c>1 for c in counts),
            'syncnet': score, 'human_av_acceptance': None}
        if boxes is not None:
            centers = (boxes[:, :2]+boxes[:, 2:])/2
            record['tracked_center_span_xy_pixels'] = np.ptp(centers, axis=0).tolist()
        checks.append(record)
        print(json.dumps({k:v for k,v in record.items() if k!='syncnet'}), flush=True)
    (EXP/'video_face_tracks.json').write_text(json.dumps(tracking, indent=2)+'\n')
    result = {'protocol_sha256': sync.sha(protocol), 'analysis_script_sha256': sync.sha(__file__),
              'syncnet_weights_sha256': sync.sha(ROOT/'models/syncnet/syncnet_v2.model'),
              'face_detector_weights_sha256': sync.sha(sync.VENDOR/'detectors/s3fd/weights/sfd_face.pth'),
              'device': 'local CPU, four threads', 'checks': checks,
              'full_decode_passed': len(checks),
              'audio_integrity_passed': sum(c['audio_integrity_passed'] for c in checks),
              'human_accepted_count': None, 'quality_gate': 'pending_user_video_review'}
    target.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
