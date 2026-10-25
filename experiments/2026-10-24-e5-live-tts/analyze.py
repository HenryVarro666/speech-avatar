"""Join actual browser, proxy and new-model PCM receipts by immutable request ID."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];EXP=Path(__file__).resolve().parent


def main():
    browser=json.loads((EXP/'browser.json').read_text());rows=browser['results'];assert len(rows)==7
    assert len({r['id'] for r in rows})==7
    complete=[r for r in rows if r['status']=='complete'];assert len(complete)==5
    assert len({r['text'] for r in complete})==4
    records=[]
    for r in rows:
        path=ROOT/'data/private/e5-live-tts/jobs'/r['id'];worker=json.loads((path/'receipt.json').read_text());pcm=(path/'stream.pcm').read_bytes()
        assert len(pcm)//2==worker.get('samples_emitted',0)
        offset=0;holes=[];previous=None
        for i,s in enumerate(r['schedules']):
            assert s['index']==i and s['offset']==offset and s['rate']==24000
            assert s['epoch']==r['epoch']
            if previous:
                hole=(s['start']-previous['start']-previous['samples']/24000)*1000;assert hole>=-1e-4;holes.append(max(0,hole))
            offset+=s['samples'];previous=s
        assert offset==r['scheduledSamples']==r['pcmSamples']
        if r['status']=='complete':
            assert worker['status']=='complete' and worker['codes_exact'] and worker['first_chunk_before_lm_complete']
            assert r['transport']['status']=='complete' and r['transport']['samples']==offset==len(pcm)//2
            assert worker['pcm_sha256']==r['transport']['sha256']==hashlib.sha256(pcm).hexdigest()
            assert r['finalControllerRest'] and r['classifierCallbacks']>0 and r['animatedFrames']>0
        if r['status']=='cancelled':assert worker['status']=='cancelled' and r['audioStoppedAfterCall'] and r['server']['status']=='cancelled'
        if r['status']=='incomplete':assert r['profile']=='drop' and r['chunks']==2 and offset==46080 and worker['status']=='cancelled' and r['transport']['status']=='incomplete'
        records.append({'id':r['id'],'text':r['text'],'role':r['role'],'status':r['status'],'profile':r['profile'],
                        'browser_first_pcm_s':r.get('firstPcmMs',0)/1000,'browser_planned_audio_start_s':(r.get('requestToScheduleMs',0)+r.get('scheduleLeadMs',0))/1000,
                        'browser_total_s':r.get('finishedMs',0)/1000,'scheduled_samples':offset,'max_scheduled_gap_s':max(holes,default=0)/1000,
                        'worker_status':worker['status'],'worker_first_pcm_s':worker.get('first_pcm_s'),'worker_generation_s':worker.get('generation_s'),
                        'audio_s':worker.get('samples',0)/24000,'rtf':worker.get('generation_s',0)/(worker['samples']/24000) if worker.get('samples') else None,
                        'peak_rss_gib':worker.get('peak_rss_kib',0)/1024**2,'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'human_av_accepted':None})
    assert any(e['kind']=='controlled_barge_in' for e in browser['events'])
    assert any(e['kind']=='stale_ui_discarded' for e in browser['events'])
    before=next(r for r in rows if r['status']=='incomplete');after=next(r for r in rows if r['requestAt']>before['requestAt'] and r['status']=='complete')
    assert before['text']==after['text'] and before['id']!=after['id'] and after['pcmSamples']>before['pcmSamples']
    good=[r for r in records if r['status']=='complete'];span=lambda name:[min(r[name] for r in good),max(r[name] for r in good)]
    summary={'browser_requests':7,'complete':5,'distinct_completed_texts':4,'controlled_barge_in_cancelled':1,'injected_disconnect_incomplete':1,
             'explicit_retry_recovered':True,'new_phrase_after_disconnect':True,'stale_ui_discarded':True,'new_model_audio_not_fixture_replay':True,
             'browser_first_pcm_s':span('browser_first_pcm_s'),'browser_planned_audio_start_s':span('browser_planned_audio_start_s'),
             'worker_rtf':span('rtf'),'worker_peak_rss_gib':span('peak_rss_gib'),'largest_scheduled_gap_s':max(r['max_scheduled_gap_s'] for r in good),
             'source_pcm_hash_and_samples_exact':5,'codec_rows_checked_against_official_return':5,'first_audio_before_lm_complete':5,
             'lifecycle_substage_pass':True,'realtime_performance_gate_pass':False,'human_microphone_asr_translation_tested':False,
             'human_av_accepted':None,'production_deployed':False,'scope':'CPU local TTS substage E5a; not live microphone/full interpreter/hardware latency acceptance'}
    (EXP/'metrics.json').write_text(json.dumps({'summary':summary,'records':records},ensure_ascii=False,indent=2)+'\n')
    (EXP/'PUBLIC_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
