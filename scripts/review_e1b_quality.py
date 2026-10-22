"""Post-hoc local diagnostics for four immutable E1b videos; no rendering."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import torch

import audit_e1_quality as sync

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments/2026-10-20-e1b-full-expression'
REVIEW = EXP / 'quality-review-v1'
OUT = ROOT / 'outputs/e1b/quality-review-v1'


def sheet(frames, ids, target, size=(256, 244), crop=None, cols=4):
    result = Image.new('RGB', (cols*size[0], math.ceil(len(ids)/cols)*(size[1]+24)), '#dfe4eb')
    for n, i in enumerate(ids):
        frame = frames[i]
        if crop is not None:
            x1, y1, x2, y2 = crop
            frame = frame[y1:y2, x1:x2]
        tile = Image.new('RGB', (size[0], size[1]+24), 'white')
        tile.paste(ImageOps.pad(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                               size, color='#101722'), (0, 24))
        ImageDraw.Draw(tile).text((4, 5), f'f{i:03d} / {i/25:.2f}s', fill='black')
        result.paste(tile, ((n % cols)*size[0], (n//cols)*(size[1]+24)))
    result.save(target)


def valid_score(vf, af, start, end):
    ids = torch.arange(max(15, math.ceil(start*25)), min(len(vf)-15, math.ceil(end*25)))
    if len(ids) < 8:
        return {'available': False, 'valid_starts': len(ids)}
    curve = torch.stack([torch.nn.functional.pairwise_distance(vf[ids], af[ids+j]).mean()
                         for j in range(-15, 16)])
    index = int(curve.argmin())
    return {'available': True, 'valid_starts': len(ids),
            'actual_start_s': int(ids[0])/25, 'last_window_start_s': int(ids[-1])/25,
            'offset_ms': (15-index)*40, 'confidence': float(curve.median()-curve.min()),
            'minimum_distance': float(curve.min()), 'distance_curve': curve.tolist()}


def temporal(frames, box):
    x1, y1, x2, y2 = box
    w, h = x2-x1, y2-y1
    rois = {'eyes': [x1+.10*w, y1+.20*h, x2-.10*w, y1+.45*h],
            'mouth': [x1+.15*w, y1+.52*h, x2-.15*w, y2+.10*h],
            'bottom': [0, frames.shape[1]*.70, frames.shape[2], frames.shape[1]]}
    differences = np.abs(np.diff(frames.astype(np.int16), axis=0))
    result = {}
    for name, rect in rois.items():
        a, b, c, d = [int(v) for v in rect]
        a, b, c, d = max(0, a), max(0, b), min(frames.shape[2], c), min(frames.shape[1], d)
        delta = differences[:, b:d, a:c].mean(axis=(1, 2, 3))
        join = delta[92]
        result[name] = {'fixed_roi_xyxy': [a, b, c, d], 'adjacent_mae': delta.tolist(),
                        'mean_mae': float(delta.mean()), 'p95_mae': float(np.percentile(delta, 95)),
                        'transition_92_to_93_mae': float(join),
                        'transition_92_to_93_percentile': float((delta <= join).mean()*100),
                        'largest_transition_to_frame': int(delta.argmax()+1),
                        'largest_transition_time_s': int(delta.argmax()+1)/25}
    return result


def main():
    target = REVIEW / 'diagnostics.json'
    if target.exists():
        raise FileExistsError('Keep prior audit diagnostics')
    lock = json.loads((REVIEW/'INPUT_LOCK.json').read_text())
    for path, digest in lock['files'].items():
        assert sync.sha(ROOT/path) == digest, path
    OUT.mkdir(exist_ok=True)
    torch.set_num_threads(4)
    model = sync.S().eval()
    model.load_state_dict(torch.load(ROOT/'models/syncnet/syncnet_v2.model',
                                    map_location='cpu', weights_only=True))
    manifest = json.loads((EXP/'manifest.json').read_text())
    previous = json.loads((EXP/'video_validation.json').read_text())
    tracks = json.loads((EXP/'video_face_tracks.json').read_text())
    records = []
    for trial in manifest['trials']:
        ident = trial['trial_id']
        short = ('female' if trial['avatar_id']=='avatar-a' else 'male') + (
            '-musetalk' if trial['backend']=='musetalk-v15' else '-longcat')
        video = ROOT/trial['planned_output_path']
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'],
                       capture_output=True, check=True)
        frames = sync.read_video(video)
        boxes = np.asarray(tracks[ident]['smoothed_boxes'])
        wav = sync.audio(video)
        crops = np.concatenate([sync.face_crops(frames[i:i+1], box) for i, box in enumerate(boxes)])
        vf, af = sync.features(model, crops, wav)
        torch.save({'video_features': vf, 'audio_features': af}, OUT/(short+'-features.pt'))
        whole = sync.official_score(vf, af)
        old = next(c for c in previous['checks'] if c['trial_id']==ident)
        assert whole['offset_ms'] == old['syncnet']['offset_ms']
        assert np.allclose(whole['distance_curve'], old['syncnet']['distance_curve'], atol=1e-5)
        windows = [{'requested_start_s': a, 'requested_end_s': b,
                    **valid_score(vf, af, a, b)} for a, b in
                   [(0.6, 2.0), (2.0, 3.4), (3.4, len(frames)/25-.8)]]
        ids = sorted(set(range(0, len(frames), 5)) | {len(frames)-1})
        sheet(frames, ids, OUT/(short+'-full.png'))
        sheet(frames, list(range(85, min(102, len(frames)))), OUT/(short+'-join.png'))
        mouth = temporal(frames, boxes[0])['mouth']['fixed_roi_xyxy']
        sheet(frames, [round(t*25) for t in [.4, .8, 1.2, 1.6, 2.4, 2.8, 3.2, 3.6, 3.72, 4, 4.4, 4.8]],
              OUT/(short+'-teeth.png'), size=(256, 150), crop=mouth)
        sheet(frames, ids, OUT/(short+'-hands.png'), size=(256, 140),
              crop=(0, int(frames.shape[1]*.66), frames.shape[2], frames.shape[1]))
        # Exact native frames for anatomy inspection, never upscaled or retouched.
        detail_times = [1.0, 2.64] if trial['avatar_id']=='avatar-a' else [1.4, 4.6]
        for time_s in detail_times:
            index = round(time_s*25)
            Image.fromarray(cv2.cvtColor(frames[index], cv2.COLOR_BGR2RGB)).save(
                OUT/(short+f'-f{index:03d}-native.png'))
        record = {'trial_id': ident, 'short_id': short, 'output_sha256': sync.sha(video),
                  'full_decode': True, 'frames': len(frames), 'fps': 25,
                  'whole_clip_reproduced': whole,
                  'strict_window_scores': windows, 'known_shift_controls': sync.controls(vf, af),
                  'temporal': temporal(frames, boxes[0]),
                  'fullframe_sample_ids': ids, 'evidence_files': []}
        for path in sorted(OUT.glob(short+'-*.png')):
            record['evidence_files'].append({'path': str(path.relative_to(ROOT)), 'sha256': sync.sha(path)})
        records.append(record)
        print(json.dumps({'clip': short, 'offset_ms': whole['offset_ms'],
                          'windows': [{k:v for k,v in w.items() if k!='distance_curve'} for w in windows],
                          'controls': record['known_shift_controls'],
                          'join_mouth_percentile': record['temporal']['mouth']['transition_92_to_93_percentile']}), flush=True)
    result = {'plan_sha256': sync.sha(REVIEW/'PLAN.md'), 'script_sha256': sync.sha(__file__),
              'input_lock_sha256': sync.sha(REVIEW/'INPUT_LOCK.json'),
              'device': 'local CPU /4threads', 'post_hoc': True,
              'original_outputs_modified': False, 'human_av_review': 'pending', 'clips': records}
    target.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
