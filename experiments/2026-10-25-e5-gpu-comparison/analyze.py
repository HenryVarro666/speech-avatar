"""Verify owned PCM/code receipts and compare identical-protocol browser schedules."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];EXP=Path(__file__).resolve().parent


def analyze_report(name):
    browser=json.loads((EXP/name).read_text());records=[]
    for r in browser['results']:
        path=ROOT/'data/private/e5-gpu-comparison'/r['backend']/'jobs'/r['id']
        w=json.loads((path/'receipt.json').read_text());pcm=(path/'stream.pcm').read_bytes()
        assert len(pcm)//2==w.get('samples_emitted',0)
        offset=0;gaps=[];last=None
        for i,s in enumerate(r['schedules']):
            assert s['index']==i and s['offset']==offset and s['rate']==24000 and s['epoch']==r['epoch']
            if last:
                gap=s['start']-last['start']-last['samples']/24000;assert gap>=-1e-4;gaps.append(max(0,gap))
            offset+=s['samples'];last=s
        assert offset==r['scheduledSamples']==r['pcmSamples']
        if r['status']=='complete':
            assert w['status']=='complete' and w['codes_exact'] and w['first_chunk_before_lm_complete']
            assert r['transport']['status']=='complete' and r['transport']['samples']==offset==len(pcm)//2
            assert w['pcm_sha256']==r['transport']['sha256']==hashlib.sha256(pcm).hexdigest()
            assert r['finalControllerRest'] and r['classifierCallbacks']>0 and r['animatedFrames']>0
        if r['status']=='cancelled':assert w['status']=='cancelled' and r['audioStoppedAfterCall'] and r['server']['status']=='cancelled'
        if r['status']=='incomplete':assert r['profile']=='drop' and r['chunks']==2 and offset==46080 and w['status']=='cancelled' and r['transport']['status']=='incomplete'
        records.append({'id':r['id'],'backend':r['backend'],'text':r['text'],'role':r['role'],'status':r['status'],'profile':r['profile'],
                        'first_pcm_s':r.get('firstPcmMs',0)/1000,'planned_audio_start_s':(r.get('requestToScheduleMs',0)+r.get('scheduleLeadMs',0))/1000,
                        'scheduled_samples':offset,'audio_s':w.get('samples',0)/24000,'max_scheduled_gap_s':max(gaps,default=0),'gaps_over_20ms':sum(g>0.020 for g in gaps),
                        'worker_first_pcm_s':w.get('first_pcm_s'),'worker_generation_s':w.get('generation_s'),'rtf':w.get('generation_s',0)/(w['samples']/24000) if w.get('samples') else None,
                        'peak_cuda_allocated_mib':w.get('peak_cuda_allocated_mib',0),'peak_rss_gib':w.get('peak_rss_kib',0)/1024**2,
                        'source_pcm_sha256':hashlib.sha256(pcm).hexdigest(),'worker_status':w['status'],'human_av_accepted':None})
    return browser,records


def main():
    primary,rows=analyze_report('browser-primary.json');life,lr=analyze_report('browser-lifecycle.json')
    assert len(rows)==8 and all(r['status']=='complete' for r in rows)
    assert [r['backend'] for r in rows]==['cpu','gpu','gpu','cpu','cpu','gpu','gpu','cpu']
    spec=json.loads((EXP/'manifest.json').read_text())
    for u in spec['utterances']:
        pair=[r for r in rows if r['text']==u['text']];assert len(pair)==2 and {r['backend'] for r in pair}=={'cpu','gpu'}
    assert len(lr)==7 and all(r['backend']=='gpu' for r in lr)
    assert [r['status'] for r in lr]==['complete','complete','cancelled','complete','incomplete','complete','complete']
    assert any(e['kind']=='controlled_barge_in' for e in life['events']) and any(e['kind']=='stale_ui_discarded' for e in life['events'])
    assert lr[4]['text']==lr[5]['text'] and lr[4]['id']!=lr[5]['id']
    assert lr[-1]['text']==spec['utterances'][-1]['text']
    summaries={}
    for b in ['cpu','gpu']:
        rr=[r for r in rows if r['backend']==b]
        span=lambda k:[min(r[k] for r in rr),max(r[k] for r in rr)]
        summaries[b]={'n':4,'first_pcm_s':span('first_pcm_s'),'first_pcm_median_s':statistics.median(r['first_pcm_s'] for r in rr),
                      'planned_audio_start_s':span('planned_audio_start_s'),'worker_rtf':span('rtf'),
                      'max_scheduled_gap_s':max(r['max_scheduled_gap_s'] for r in rr),'gaps_over_20ms':sum(r['gaps_over_20ms'] for r in rr),
                      'peak_cuda_allocated_mib':max(r['peak_cuda_allocated_mib'] for r in rr),'peak_rss_gib':span('peak_rss_gib')}
    gpu=[r for r in rows+lr if r['backend']=='gpu' and r['status']=='complete']
    summary={'matched_primary':summaries,'gpu_lifecycle_requests':7,'gpu_lifecycle_complete':5,'gpu_barge_in_cancelled':1,'gpu_disconnect_incomplete':1,
             'explicit_retry_new_id':True,'new_phrase_recovery':True,'stale_ui_discarded':True,'source_pcm_hash_sample_and_code_proofs':13,
             'first_pcm_before_lm_complete':13,'gpu_first_pcm_target_1s_pass':all(r['first_pcm_s']<=1 for r in gpu),
             'gpu_rtf_target_pass':all(r['rtf']<1 for r in gpu),'gpu_gap_target_20ms_pass':all(r['max_scheduled_gap_s']<=0.020 for r in gpu),
             'human_microphone_asr_translation_tested':False,'human_av_accepted':None,'production_deployed':False,
             'scope':'Warm same-model/protocol development comparison; scheduled playback, not physical audio latency or SLO; cross-device sampled audio can differ'}
    (EXP/'metrics.json').write_text(json.dumps({'summary':summary,'primary':rows,'lifecycle':lr},ensure_ascii=False,indent=2)+'\n')
    (EXP/'PUBLIC_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def preparation():
    browser,rows=analyze_report('browser-preparation.json')
    assert len(rows)==9 and all(r['backend']=='cpu' for r in rows)
    assert [r['status'] for r in rows]==['complete']*4+['cancelled','complete','incomplete','complete','complete']
    assert any(e['kind']=='controlled_barge_in' for e in browser['events']) and any(e['kind']=='stale_ui_discarded' for e in browser['events'])
    assert rows[6]['text']==rows[7]['text'] and rows[6]['id']!=rows[7]['id']
    good=[r for r in rows if r['status']=='complete'];span=lambda k:[min(r[k] for r in good),max(r[k] for r in good)]
    summary={'status':'GPU_NOT_RUN_RESOURCE_GATE','gpu_inference_requests':0,'matched_comparison_completed':False,
             'cpu_preparation_requests':9,'cpu_complete':7,'cpu_cancelled':1,'cpu_disconnect_incomplete':1,
             'cpu_explicit_retry_and_new_phrase_recovery':True,'cpu_stale_ui_discarded':True,
             'cpu_first_pcm_s':span('first_pcm_s'),'cpu_planned_audio_start_s':span('planned_audio_start_s'),'cpu_worker_rtf':span('rtf'),
             'cpu_max_scheduled_gap_s':max(r['max_scheduled_gap_s'] for r in good),'source_pcm_hash_sample_and_code_proofs':7,
             'gpu_first_pcm_s':None,'gpu_rtf':None,'gpu_gap_s':None,'gpu_lifecycle_pass':None,
             'human_microphone_asr_translation_tested':False,'human_av_accepted':None,'production_deployed':False,
             'scope':'CPU preparation and routing regression only; GPU runtime/performance/lifecycle unverified; no claim of acceleration or eliminated gaps'}
    (EXP/'metrics-preparation.json').write_text(json.dumps({'summary':summary,'records':rows},ensure_ascii=False,indent=2)+'\n')
    (EXP/'PUBLIC_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':preparation() if '--preparation' in sys.argv else main()
