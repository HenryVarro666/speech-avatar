/** Actual AudioContext timeline; no network-arrival timestamp is a playback clock. */
export class PlaybackTimeline {
  epoch=0; segments=[];
  accept(e) {
    if(e.type==='reset'){if(e.epoch<this.epoch)return false;this.epoch=e.epoch;this.segments=[];return true}
    if(e.type!=='scheduled')throw new TypeError('Unknown playback event');
    if(e.epoch<this.epoch)return false;
    if(!Number.isInteger(e.epoch)||!Number.isFinite(e.contextStartTime)||!Number.isFinite(e.sampleRate)||e.sampleRate<=0||!Number.isInteger(e.sampleOffset)||e.sampleOffset<0||!(e.pcm instanceof Float32Array)||!e.pcm.length)throw new TypeError('Malformed PCM schedule');
    if(e.epoch>this.epoch){this.epoch=e.epoch;this.segments=[]}
    const end=e.contextStartTime+e.pcm.length/e.sampleRate;
    if(this.segments.some(s=>e.contextStartTime<s.end-1e-7&&end>s.contextStartTime+1e-7))throw new RangeError('Overlapping playback');
    this.segments.push({...e,pcm:e.pcm.slice(),end});return true;
  }
  at(time){const s=this.segments.find(s=>time>=s.contextStartTime&&time<s.end);return s?{...s,sourceSample:s.sampleOffset+Math.floor((time-s.contextStartTime)*s.sampleRate)}:null}
  prune(time){this.segments=this.segments.filter(s=>s.end>time)}
}
export function pcmRms(samples){if(!samples.length)return 0;let sum=0;for(const x of samples)sum+=Number.isFinite(x)?x*x:0;return Math.sqrt(sum/samples.length)}
export function poseFromWeights(weights){const groups={viseme_aa:1,viseme_O:2,viseme_U:2,viseme_RR:2,viseme_E:3,viseme_I:3,viseme_SS:3,viseme_TH:3,viseme_DD:3,viseme_FF:4,viseme_kk:1,viseme_nn:3,viseme_CH:2,viseme_PP:0,viseme_sil:0};let pose=0,max=0;for(const [key,p] of Object.entries(groups)){const v=Number(weights[key]);if(Number.isFinite(v)&&v>max){max=v;pose=p}}return {pose,amount:pose?Math.min(1,Math.max(0,max/.65)):0}}
