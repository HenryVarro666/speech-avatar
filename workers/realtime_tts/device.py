"""Explicit device selection and cooperative, fail-closed CUDA ownership guard."""
import os
import re
import subprocess


def configure_device(device,uuid,env=None):
    env=os.environ if env is None else env
    if device=='cpu':env['CUDA_VISIBLE_DEVICES']='';return
    if device!='cuda' or not uuid or not re.fullmatch(r'GPU-[A-Za-z0-9-]+',uuid):
        raise ValueError('CUDA requires an explicit full GPU UUID')
    env['CUDA_VISIBLE_DEVICES']=uuid


def check_snapshot(gpus,processes,uuid,pid,resident=False):
    rows=[x.split(',') for x in gpus.strip().splitlines() if x.strip()]
    selected=[x for x in rows if x[0].strip()==uuid]
    if len(selected)!=1:raise RuntimeError('Selected GPU missing or ambiguous')
    _,total,used,util=[x.strip() for x in selected[0]]
    total,used,util=int(total),int(used),int(util)
    procs=[x.split(',') for x in processes.strip().splitlines() if x.strip()]
    pids=[int(x[1].strip()) for x in procs if x[0].strip()==uuid]
    if any(p!=pid for p in pids):raise RuntimeError('Foreign CUDA context on selected GPU')
    if resident:
        if pid not in pids:raise RuntimeError('Owned CUDA reservation not visible')
        if used>16384:raise RuntimeError('Selected GPU memory ceiling exceeded')
    elif pids or util>2 or total-used<16384:
        raise RuntimeError('Selected GPU is not idle and free for a fresh claim')
    return {'uuid':uuid,'memory_total_mib':total,'memory_used_mib':used,'utilization_pct':util,
            'compute_pids':pids,'owned_visible':pid in pids,'cooperative_guard_not_atomic_lease':True}


def snapshot(uuid,resident=False):
    def query(args):
        return subprocess.check_output(['nvidia-smi',*args,'--format=csv,noheader,nounits'],text=True,timeout=5)
    return check_snapshot(query(['--query-gpu=uuid,memory.total,memory.used,utilization.gpu']),
                          query(['--query-compute-apps=gpu_uuid,pid,used_gpu_memory']),uuid,os.getpid(),resident)
