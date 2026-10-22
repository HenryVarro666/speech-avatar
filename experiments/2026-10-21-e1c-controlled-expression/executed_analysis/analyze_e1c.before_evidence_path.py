"""Local CPU diagnostics for E1c calibration or controlled-expression clips."""
import argparse
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import torch

import analyze_e1b as quality
import audit_e1_quality as sync
from review_e1b_quality import valid_score

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT/'experiments/2026-10-21-e1c-controlled-expression'
PARENT = ROOT/'experiments/2026-10-20-e1b-full-expression'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', required=True, choices=['qsync', 'qmotion'])
    stage = parser.parse_args().stage
    target = EXP/(stage+'_quality.json')
    if target.exists():
        raise FileExistsError('Keep existing stage metrics')
    manifest = json.loads((EXP/'manifest.json').read_text())
    if sync.sha(EXP/'manifest.json') != (EXP/'manifest.sha256').read_text().split()[0]:
        raise ValueError('Frozen manifest mismatch')
    original_trials = json.loads((PARENT/'manifest.json').read_text())['trials']
    parent_tracks = json.loads((PARENT/'video_face_tracks.json').read_text())
    if stage=='qsync':
        variants = json.loads((EXP/'sync_variants.json').read_text())['variants']
        jobs = []
        for row in variants:
            source = next(t for t in original_trials if t['trial_id']==row['parent_trial_id'])
            jobs.append({**row, 'trial_id': row['id'], 'audio_path': source['audio_path'],
                         'padding_frames': row['video_padding_frames']})
    else:
        attempts = [json.loads(line) for line in (EXP/'video_attempts.jsonl').read_text().splitlines()]
        jobs = []
        for trial in manifest['trials']:
            row = next(r for r in reversed(attempts) if r['trial_id']==trial['trial_id']
                       and r['status']=='rendered_pending_validation')
            jobs.append({**trial, 'output_path': trial['planned_output_path'],
                         'output_sha256': row['output_sha256'], 'padding_frames': 0})
    torch.set_num_threads(4)
    model = sync.S().eval()
    model.load_state_dict(torch.load(ROOT/'models/syncnet/syncnet_v2.model',
                                    map_location='cpu', weights_only=True))
    detector = None
    if stage=='qmotion':
        previous = os.getcwd()
        os.chdir(sync.VENDOR)
        detector = sync.S3FD(device='cpu')
        os.chdir(previous)
    out = ROOT/'outputs/e1c/quality'/stage
    out.mkdir(parents=True, exist_ok=True)
    quality.OUT = out
    records, tracks = [], {}
    for job in jobs:
        video = ROOT/job['output_path']
        assert sync.sha(video)==job['output_sha256']
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'],
                       capture_output=True, check=True)
        frames = sync.read_video(video)
        speech, audio = sync.audio(ROOT/job['audio_path']), sync.audio(video)
        values = []
        a, b = speech[::16], audio[::16]
        for lag in range(-32, 33):
            values.append((quality.corr(a if lag>=0 else a[-lag:], b[lag:] if lag>=0 else b), lag))
        best, lag = max(values)
        tail = quality.corr(speech[-4800:], audio[len(speech)-4800+lag*16:len(speech)+lag*16])
        expected_samples = len(speech)+job['padding_frames']*640
        delta = (len(audio)-expected_samples)/16
        if stage=='qsync':
            parent_boxes = np.asarray(parent_tracks[job['parent_trial_id']]['smoothed_boxes'])
            boxes = np.concatenate([np.repeat(parent_boxes[:1], job['padding_frames'], axis=0), parent_boxes])
            counts = [1]*len(boxes)
            track_method = 'exact decoded-frame mapping from parent; repeated first box for cloned prefix'
        else:
            raw, boxes, counts = quality.track(detector, frames)
            track_method = 'S3FD every frame/confidence0.9/scale0.25;13frame centered median'
            tracks[job['trial_id']] = {'raw_boxes': raw, 'smoothed_boxes': boxes.tolist() if boxes is not None else None,
                                       'detections_per_frame': counts}
        score, windows = None, []
        if boxes is not None:
            crops = np.concatenate([sync.face_crops(frames[i:i+1], box) for i,box in enumerate(boxes)])
            vf, af = sync.features(model, crops, audio)
            score = sync.official_score(vf, af)
            voiced_duration = len(speech)/16000
            windows = [valid_score(vf, af, start, end) for start,end in
                       [(0.6,2), (2,3.4), (3.4,voiced_duration-.8)]]
        quality.evidence(frames, boxes, job['trial_id'])
        record = {'trial_id': job['trial_id'], 'output_sha256': job['output_sha256'],
                  'full_decode': True, 'decoded_frames': len(frames), 'fps': 25,
                  'width': frames.shape[2], 'height': frames.shape[1],
                  'source_audio_duration_s': len(speech)/16000,
                  'expected_output_duration_s': expected_samples/16000,
                  'decoded_audio_duration_s': len(audio)/16000,
                  'decoded_audio_delta_ms': delta, 'audio_correlation': best,
                  'best_audio_lag_ms': lag, 'last_300ms_speech_correlation': tail,
                  'audio_integrity_passed': best>=.95 and abs(lag)<=20 and -20<=delta<=100 and tail>=.95,
                  'face_frames_detected': sum(c>0 for c in counts),
                  'multi_detection_frames': sum(c>1 for c in counts), 'track_method': track_method,
                  'syncnet': score, 'strict_window_scores': windows, 'human_av_acceptance': None}
        if boxes is not None:
            record['tracked_center_span_xy_pixels'] = np.ptp((boxes[:,:2]+boxes[:,2:])/2, axis=0).tolist()
        records.append(record)
        print(json.dumps({k:v for k,v in record.items() if k not in ['strict_window_scores','syncnet']})+
              ' offset_ms='+str(score['offset_ms'] if score else None), flush=True)
    result = {'stage': stage, 'script_sha256': sync.sha(__file__),
              'protocol_sha256': sync.sha(EXP/'QUALITY_PROTOCOL.md'),
              'manifest_sha256': sync.sha(EXP/'manifest.json'),
              'device': 'local CPU/4threads', 'checks': records,
              'full_decode_passed': len(records),
              'audio_integrity_passed': sum(r['audio_integrity_passed'] for r in records),
              'human_av_acceptance': 'pending'}
    if tracks:
        (EXP/(stage+'_face_tracks.json')).write_text(json.dumps(tracks,indent=2)+'\n')
    target.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
