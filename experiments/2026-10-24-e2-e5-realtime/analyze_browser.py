"""Validate exported real-browser receipts; no synthetic success records."""
import hashlib,json
from pathlib import Path
EXP=Path(__file__).resolve().parent
def read(name):return json.loads((EXP/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def continuous(row):
    offset=0;previous=None
    for i,s in enumerate(row['schedules']):
        assert s['index']==i and s['offset']==offset
        assert s['rate']==row['sourceSampleRate']
        if previous:assert s['start']+1e-7>=previous['start']+previous['samples']/previous['rate']
        offset+=s['samples'];previous=s
    assert offset==row['scheduledSamples']
def span(rows,key):return [min(r[key] for r in rows),max(r[key] for r in rows)]
def main():
    matrix=read('browser-matrix.json');rows=matrix['results'];assert len(rows)==12
    assert len({(r['clip'],r['mode']) for r in rows})==12
    for r in rows:
        continuous(r);assert r['status']=='complete' and r['scheduledSamples']==r['expectedSamples']
        assert r['finalControllerRest'] and r['visualFailures']==0
        assert r['humanAvAccepted'] is None
        if r['mode']=='idle':assert r['animatedFrames']==0
        else:assert r['animatedFrames']>0
        if r['mode']=='headaudio':assert r['classifierCallbacks']>0 and not r.get('analysisError')
    faults=read('browser-faults.json');allrows=faults['results']
    for r in allrows:continuous(r)
    gap=next(r for r in allrows if r['profile']=='gap')
    assert gap['status']=='complete' and gap['scheduledSamples']==gap['expectedSamples'] and gap['gapInjected']
    holes=[(b['start']-a['start']-a['samples']/a['rate'])*1000 for a,b in zip(gap['schedules'],gap['schedules'][1:])]
    assert max(holes)>250
    disconnect=next(r for r in allrows if r['profile']=='disconnect')
    assert disconnect['status']=='incomplete' and disconnect['scheduledSamples']<disconnect['expectedSamples']
    broken=next(r for r in allrows if r['profile']=='model-error')
    assert broken['status']=='complete' and broken['analysisError'] and broken['fallback']=='rms' and broken['rmsFrames']>0
    assert broken['scheduledSamples']==broken['expectedSamples']
    recovered=next(r for r in allrows if r['id']>broken['id'] and r['analysisReady'] and not r.get('analysisError'))
    assert recovered['status']=='complete' and recovered['scheduledSamples']==recovered['expectedSamples']
    cancelled=[r for r in allrows if r['status']=='cancelled' and r.get('audioStoppedAfterCall')]
    assert cancelled and all(r['finalControllerRest'] and r['stopToNeutralMs']<100 for r in cancelled)
    assert any(e['kind']=='stale_injection' and e['accepted'] is False for e in faults['events'])
    loss=next(r for r in allrows if r['status']=='complete' and any(e['reason']=='context_lost' for e in r['renderEvents']))
    static=next(r for r in allrows if r['status']=='complete' and r['staticFallbackFrames']>100 and r['visualFailures']>0 and not any(e['reason']=='context_lost' for e in r['renderEvents']))
    assert all(r['status']=='complete' and r['scheduledSamples']==r['expectedSamples'] for r in [loss,static])
    restored=next(r for r in allrows if r['id']>static['id'] and r['drawFrames']>100 and not r['visualFailures'])
    assert restored['status']=='complete'
    delayed=next(r for r in allrows if r['profile']=='visual-delay')
    assert delayed['status']=='complete' and delayed['visualReadyMs']>=1500
    assert delayed['scheduledLatencyMs']+delayed['schedulingLeadMs']<delayed['visualReadyMs']
    assert delayed['scheduledSamples']==delayed['expectedSamples'] and delayed['staticFallbackFrames']>100
    assert all(r['humanAvAccepted'] is None for r in allrows)
    h=[r for r in rows if r['mode']=='headaudio']
    metrics={'scope':'local PCM playback/browser engineering only; no acoustic or human sync acceptance',
      'matrix_complete':12,'samples_exact':12,'controller_rest':12,'head_audio_active':len(h),
      'request_to_schedule_ms':span(rows,'scheduledLatencyMs'),
      'request_to_planned_audio_start_ms':[min(r['scheduledLatencyMs']+r['schedulingLeadMs'] for r in rows),max(r['scheduledLatencyMs']+r['schedulingLeadMs'] for r in rows)],
      'headaudio_first_active_pose_after_audio_start_ms':[min((r['firstVisualContext']-r['firstAudioContext'])*1000 for r in h),max((r['firstVisualContext']-r['firstAudioContext'])*1000 for r in h)],
      'rolling_300_raf_interval_p95_ms':span(rows,'frameIntervalP95Ms'),
      'injected_delay_ms':400,'largest_actual_audio_gap_ms':max(holes),
      'disconnect_samples':[disconnect['scheduledSamples'],disconnect['expectedSamples']],
      'delayed_visual_ready_ms':delayed['visualReadyMs'],
      'delayed_visual_planned_audio_start_ms':delayed['scheduledLatencyMs']+delayed['schedulingLeadMs'],
      'stop_to_controller_rest_ms':[r['stopToNeutralMs'] for r in cancelled],
      'fault_checks':{'stop':True,'stale_event':True,'late_chunk':True,'disconnect':True,'model_failure_rms':True,'model_restore':True,'webgl_loss_static':True,'new_audio_while_lost':True,'webgl_restore':True,'visual_prepare_parallel':True},
      'gpu_renderer':matrix['gpuRenderer'],'human_av_accepted':None,'production_deployed':False,
      'receipts':{n:sha(EXP/n) for n in ['browser-matrix.json','browser-faults.json']}}
    (EXP/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n');print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
