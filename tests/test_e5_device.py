import unittest
from workers.realtime_tts.device import check_snapshot, configure_device


class DeviceGuardTests(unittest.TestCase):
    def test_cpu_hides_cuda_and_gpu_requires_exact_uuid(self):
        env={}
        configure_device('cpu',None,env)
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'')
        with self.assertRaises(ValueError):configure_device('cuda',None,env)
        configure_device('cuda','GPU-selected',env)
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'GPU-selected')

    def test_fresh_claim_requires_idle_free_gpu_without_foreign_process(self):
        gpu='GPU-selected, 95830, 14, 0\n'
        self.assertEqual(check_snapshot(gpu,'','GPU-selected',123)['memory_used_mib'],14)
        for g,p in [(gpu,'GPU-selected, 888, 1\n'),('GPU-selected, 95830, 14, 20\n',''),('GPU-selected, 95830, 90000, 0\n','')]:
            with self.assertRaises(RuntimeError):check_snapshot(g,p,'GPU-selected',123)

    def test_owned_context_allowed_but_other_gpu_and_late_foreign_context_are_distinct(self):
        gpu='GPU-other, 95830, 50000, 90\nGPU-selected, 95830, 6000, 90\n'
        p='GPU-other, 999, 50000\nGPU-selected, 123, 6000\n'
        self.assertTrue(check_snapshot(gpu,p,'GPU-selected',123,resident=True)['owned_visible'])
        with self.assertRaises(RuntimeError):check_snapshot(gpu,p+'GPU-selected, 888, 1\n','GPU-selected',123,resident=True)
        with self.assertRaises(RuntimeError):check_snapshot(gpu,'','GPU-selected',123,resident=True)

    def test_missing_or_ambiguous_uuid_fails_closed(self):
        for g in ['', 'GPU-selected, 95830, 14, 0\nGPU-selected, 95830, 14, 0\n']:
            with self.assertRaises(RuntimeError):check_snapshot(g,'','GPU-selected',123)
