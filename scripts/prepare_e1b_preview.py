"""Build two counterbalanced A/B pairs from the four validated native MP4s."""
import hashlib
import json
from pathlib import Path
import random
import shutil

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT/'experiments/2026-10-20-e1b-full-expression'
OUT = ROOT/'outputs/e1b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((EXP/'manifest.json').read_text())
    validation = json.loads((EXP/'video_validation.json').read_text())
    if validation['full_decode_passed'] != 4 or validation['audio_integrity_passed'] != 4:
        raise ValueError('Require all four complete, audio-preserving outputs before preview')
    processes = [json.loads(line) for line in (EXP/'video_process_results.jsonl').read_text().splitlines()]
    initial_order = list(manifest['backends'])
    if random.Random(20261020).randrange(2):
        initial_order.reverse()
    groups, reviews = [], []
    media = OUT/'review-media'
    media.mkdir(exist_ok=True)
    for number, role in enumerate(manifest['roles']):
        order = initial_order if number == 0 else initial_order[::-1]
        short = '女声' if role['persona_voice']=='female' else '男声'
        group = {'label': '女角色' if role['persona_voice']=='female' else '男角色',
                 'short_label': short, 'voice': role['audio']['voice_id']+' · 已确认普通话配音 · '+str(role['audio']['duration_s'])+' 秒',
                 'source_audio_sha256': role['audio']['sha256'], 'clips': []}
        for letter, backend in zip(['A', 'B'], order):
            trial = next(t for t in manifest['trials'] if t['avatar_id']==role['avatar_id'] and t['backend']==backend)
            check = next(c for c in validation['checks'] if c['trial_id']==trial['trial_id'])
            process = next(p for p in reversed(processes) if p['trial_id']==trial['trial_id'] and p['exit_code']==0)
            source = ROOT/trial['planned_output_path']
            if sha(source) != check['output_sha256']:
                raise ValueError('Video changed after validation')
            ident = role['persona_voice']+'-'+letter.lower()
            target = media/(ident+'.mp4')
            if target.exists() and sha(target)!=check['output_sha256']:
                raise FileExistsError('Refusing to replace different preview media')
            if not target.exists():
                shutil.copyfile(source, target)
            assert sha(target)==check['output_sha256']
            poster = media/(ident+'.png')
            shutil.copyfile(OUT/'quality'/(trial['trial_id']+'-poster.png'), poster)
            label = 'MuseTalk 1.5' if backend=='musetalk-v15' else 'LongCat Avatar 1.5'
            group['clips'].append({'id': ident, 'blind_label': letter, 'label': label,
                'trial_id': trial['trial_id'], 'backend': backend, 'sha256': check['output_sha256'],
                'filename': 'review-media/'+target.name, 'poster': 'review-media/'+poster.name,
                'width': check['width'], 'height': check['height'], 'duration_s': check['decoded_frames']/25,
                'process_wall_s': process['process_wall_s']})
            reviews.append({'blind_id': ident, 'trial_id': trial['trial_id'],
                'candidate_sha256': check['output_sha256'], 'reviewed_video_sha256': None,
                'sync_acceptable': None, 'identity_acceptable': None, 'expression_appropriate': None,
                'teeth_acceptable': None, 'ending_acceptable': None, 'accepted': None, 'feedback': None})
        groups.append(group)
    data = {'text': manifest['roles'][0]['audio']['text'], 'assignment_seed': 20261020,
            'assignment_method': 'fixed seeded order for female, reversed for male; no score-based assignment',
            'manifest_sha256': sha(EXP/'manifest.json'),
            'preview_protocol_sha256': sha(EXP/'PREVIEW_PROTOCOL.md'),
            'blinding': 'interface single blind only; source and files remain inspectable', 'groups': groups}
    (EXP/'preview_manifest.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    review_path = EXP/'video_review.json'
    if not review_path.exists():
        review_path.write_text(json.dumps({'status': 'pending_user_video_review', 'reviewer': None,
            'source_audio_accepted': True, 'clips': reviews}, ensure_ascii=False, indent=2)+'\n')
    html = (ROOT/'workers/pilot_review.template.html').read_text().replace(
        '__DATA_JSON__', json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'))
    (OUT/'index.html').write_text(html)
    print(json.dumps({'clips': 4, 'groups': 2, 'default_revealed': False,
                       'preview': str(OUT/'index.html')}))


if __name__ == '__main__':
    main()
