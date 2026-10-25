"""Exact reference ROI preprocessing; keeps original portraits unchanged."""
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgb(path):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stderr=subprocess.PIPE)


def crop_reference(source, target, box, expected_sha256):
    source, target = Path(source), Path(target)
    if target.exists():
        raise FileExistsError(target)
    if sha(source) != expected_sha256:
        raise ValueError('Source portrait hash mismatch')
    stream = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-show_streams', '-of', 'json', str(source)]))['streams'][0]
    width, height = stream['width'], stream['height']
    if len(box) != 4 or any(type(x) is not int for x in box):
        raise ValueError('ROI must contain four integer coordinates')
    left, top, right, bottom = box
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError('Invalid reference ROI')
    target.parent.mkdir(parents=True, exist_ok=True)
    command = ['ffmpeg', '-v', 'error', '-n', '-i', str(source), '-vf',
               f'crop={right-left}:{bottom-top}:{left}:{top}', '-frames:v', '1',
               '-pix_fmt', 'rgb24', str(target)]
    subprocess.run(command, check=True, capture_output=True)
    original = rgb(source)
    expected = b''.join(original[(y*width+left)*3:(y*width+right)*3]
                        for y in range(top, bottom))
    if rgb(target) != expected:
        raise ValueError('Cropped image changed source pixels')
    return {'source_sha256': expected_sha256, 'source_size': [width, height],
            'box_xyxy': box, 'output_size': [right-left, bottom-top],
            'output_sha256': sha(target), 'all_pixels_equal_source_roi': True,
            'operation': 'exact pre-generation reference crop; no resampling/redraw; no output-video crop',
            'command': command}


def main():
    import copy
    from datetime import datetime, timezone
    root = Path(__file__).resolve().parents[1]
    exp = root/'experiments/2026-10-23-e1d-reference-framing'
    parent = root/'experiments/2026-10-21-e1c-controlled-expression'
    if (exp/'manifest.json').exists():
        raise FileExistsError('Preserve frozen E1d manifest')
    manifest = copy.deepcopy(json.loads((parent/'manifest.json').read_text()))
    manifest.update(experiment_id=exp.name, created_at_utc=datetime.now(timezone.utc).isoformat(),
                    parent_manifest_sha256=sha(parent/'manifest.json'))
    manifest['reference_framing'] = {'box_xyxy': [125,75,1129,1079],
        'baseline_experiment': parent.name, 'only_variable': 'pre-generation reference image framing'}
    ledger = []
    for role, trial in zip(manifest['roles'], manifest['trials']):
        source = root/trial['image_path']
        target = root/'data/private/e1d/avatars'/trial['avatar_id']/'source-crop.png'
        crop = crop_reference(source, target, [125,75,1129,1079], trial['image_sha256'])
        ledger.append({'avatar_id':trial['avatar_id'], 'source_path':trial['image_path'],
                       'output_path':str(target.relative_to(root)), **crop})
        trial['parent_trial_id'] = trial['trial_id']
        trial['trial_id'] = 'e1d-'+('female' if trial['avatar_id']=='avatar-a' else 'male')+'-reference-framing'
        trial['planned_output_path'] = 'outputs/e1d/'+trial['trial_id']+'.mp4'
        trial.update(image_path=str(target.relative_to(root)), image_sha256=crop['output_sha256'], status='queued')
        role.update(image_path=trial['image_path'], image_sha256=trial['image_sha256'])
    (exp/'reference_crops.json').write_text(json.dumps({'script_sha256':sha(__file__), 'crops':ledger},indent=2)+'\n')
    (exp/'audio_review.json').write_bytes((parent/'audio_review.json').read_bytes())
    path=exp/'manifest.json'
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (exp/'manifest.sha256').write_text(sha(path)+'  manifest.json\n')
    protocol=exp/'QUALITY_PROTOCOL.md'
    protocol.with_suffix('.sha256').write_text(sha(protocol)+'  QUALITY_PROTOCOL.md\n')
    lock=json.loads((root/'experiments/2026-10-20-e1b-full-expression/quality-review-v1/INPUT_LOCK.json').read_text())['files']
    for name in ['manifest.json','audio_review.json','qmotion_quality.json','qmotion_face_tracks.json',
                 'qsync_quality.json','sync_variants.json','gate_review.json','user_review.json','final_checks.json']:
        p=parent/name;lock[str(p.relative_to(root))]=sha(p)
    for t in json.loads((parent/'manifest.json').read_text())['trials']:
        for field in ['image_path','audio_path','planned_output_path']:
            lock[t[field]]=sha(root/t[field])
    for line in (root/'experiments/2026-10-20-e1-musetalk/trials.jsonl').read_text().splitlines():
        t=json.loads(line);lock[t['output_path']]=t['output_sha256']
    (exp/'INPUT_LOCK.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),
        'files':lock},indent=2)+'\n')
    print(json.dumps({'manifest_sha256':sha(path),'reference_crops':len(ledger),'locked_parent_files':len(lock)}))


if __name__ == '__main__':
    main()
