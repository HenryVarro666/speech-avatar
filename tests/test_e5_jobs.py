import threading
import unittest
from workers.realtime_tts.jobs import Jobs
from workers.realtime_tts.streaming import Cancelled


class JobLifecycleTests(unittest.TestCase):
    def test_cancel_before_request_is_a_tombstone(self):
        jobs=Jobs();jobs.cancel('late');job=jobs.submit('late');self.assertTrue(job['cancel'].is_set())
        with self.assertRaises(Cancelled):
            with jobs.claim(job):self.fail('Cancelled request entered model')

    def test_replacement_releases_real_lock_then_recovers(self):
        jobs=Jobs();a=jobs.submit('a');started=threading.Event();ended=threading.Event()
        def old():
            try:
                with jobs.claim(a):started.set();a['cancel'].wait(2)
            finally:jobs.finish(a,'cancelled');ended.set()
        t=threading.Thread(target=old);t.start();self.assertTrue(started.wait(1));b=jobs.submit('b')
        with jobs.claim(b):self.assertTrue(ended.wait(1));self.assertEqual(b['status'],'generating')
        jobs.finish(b,'complete');t.join(1);self.assertEqual(jobs.snapshot('a')['status'],'cancelled');self.assertEqual(jobs.snapshot('b')['status'],'complete')

    def test_duplicate_and_request_limit_cannot_start_another_generation(self):
        jobs=Jobs(limit=1);jobs.submit('a')
        with self.assertRaises(ValueError):jobs.submit('a')
        with self.assertRaises(ValueError):jobs.submit('b')
