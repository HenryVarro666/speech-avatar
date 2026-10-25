"""Single-user latest-wins registry; the model lock is never shared across requests."""
from contextlib import contextmanager
import threading
import time
from .streaming import Cancelled


class Jobs:
    def __init__(self,limit=32):
        self.limit=limit;self.items={};self.tombstones=set();self.guard=threading.RLock();self.model_lock=threading.Lock()

    def submit(self,ident):
        with self.guard:
            if ident in self.items or len(self.items)>=self.limit:raise ValueError('Duplicate ID or request budget exhausted')
            for old in self.items.values():
                if old['status'] in ['queued','generating']:old['cancel'].set()
            job={'id':ident,'cancel':threading.Event(),'status':'queued','received':time.perf_counter()}
            if ident in self.tombstones:job['cancel'].set()
            self.items[ident]=job;return job

    def cancel(self,ident):
        with self.guard:
            self.tombstones.add(ident)
            if len(self.tombstones)>256:self.tombstones.pop()
            job=self.items.get(ident)
            if job:job['cancel_requested']=time.perf_counter();job['cancel'].set()
            return self.snapshot(ident)

    @contextmanager
    def claim(self,job):
        while True:
            if job['cancel'].is_set():raise Cancelled()
            if self.model_lock.acquire(timeout=.05):break
            if time.perf_counter()-job['received']>120:raise TimeoutError('Model queue timeout')
        try:
            if job['cancel'].is_set():raise Cancelled()
            job['status']='generating';job['generation_started']=time.perf_counter();yield
        finally:self.model_lock.release()

    def finish(self,job,status):
        job['status']='cancelled' if job['cancel'].is_set() else status;job['finished']=time.perf_counter()

    def snapshot(self,ident):
        with self.guard:
            job=self.items.get(ident)
            return {k:v for k,v in job.items() if k!='cancel'} if job else {'id':ident,'status':'cancel_requested'}
