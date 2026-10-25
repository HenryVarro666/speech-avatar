import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workers/liveportrait'))
try:
    import cv2
    import numpy as np
except ModuleNotFoundError as error:
    if error.name not in ('cv2', 'numpy'):
        raise
    cv2 = np = None
else:
    from motion_template import regional_motion


def template():
    first = {'R': np.eye(3, dtype=np.float32)[None],
             'exp': np.zeros((1, 21, 3), np.float32),
             't': np.zeros((1, 3), np.float32),
             'scale': np.ones((1, 1), np.float32),
             'kp': np.arange(63, dtype=np.float32).reshape(1, 21, 3) / 100,
             'x_s': np.zeros((1, 21, 3), np.float32)}
    second = copy.deepcopy(first)
    second['R'] = cv2.Rodrigues(np.array([0., .2, 0.]))[0][None].astype(np.float32)
    second['exp'] += .1
    second['t'] += .2
    second['scale'] += .1
    return {'n_frames': 2, 'output_fps': 25, 'motion': [first, second],
            'c_eyes_lst': [np.ones((1, 2))] * 2, 'c_lip_lst': [np.ones((1, 1))] * 2}


@unittest.skipUnless(cv2 is not None, 'Regional motion requires NumPy/OpenCV in .venv-quality')
class RegionalMotionTest(unittest.TestCase):
    def test_eyes_keep_full_delta_while_mouth_and_pose_attenuate(self):
        raw = template()
        out = regional_motion(raw, pose_gain=.65, expression_gain=.65, eye_gain=1.)
        for i in (11, 13, 15, 16, 18):
            np.testing.assert_allclose(out['motion'][1]['exp'][:, i], .1)
        np.testing.assert_allclose(out['motion'][1]['exp'][:, 6], .065)
        np.testing.assert_allclose(out['motion'][1]['t'], .13)
        np.testing.assert_allclose(out['motion'][1]['scale'], 1.065)
        rotation = out['motion'][1]['R'][0]
        np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-6)
        self.assertAlmostEqual(np.linalg.det(rotation), 1., places=6)
        self.assertAlmostEqual(float(cv2.Rodrigues(rotation)[0][1, 0]), .13, places=5)

    def test_first_frame_and_input_are_preserved_and_result_is_independent(self):
        raw = template(); before = copy.deepcopy(raw)
        out = regional_motion(raw)
        for a, b in zip(raw['motion'], before['motion']):
            for key in a: np.testing.assert_array_equal(a[key], b[key])
        for key in ('R', 'exp', 't', 'scale', 'kp'):
            np.testing.assert_array_equal(out['motion'][0][key], raw['motion'][0][key])
        out['motion'][1]['exp'][:] = 99
        np.testing.assert_array_equal(raw['motion'][1]['exp'], before['motion'][1]['exp'])

    def test_zero_and_identity_controls_with_nonidentity_initial_rotation(self):
        raw = template()
        r0 = cv2.Rodrigues(np.array([.1, -.2, .05]))[0].astype(np.float32)
        for frame in raw['motion']: frame['R'] = frame['R'] @ r0
        full = regional_motion(raw, pose_gain=1., expression_gain=1., eye_gain=1.)
        zero = regional_motion(raw, pose_gain=0., expression_gain=0., eye_gain=0.)
        for i, frame in enumerate(raw['motion']):
            for key in ('R', 'exp', 't', 'scale'):
                np.testing.assert_allclose(full['motion'][i][key], frame[key], atol=1e-6)
                np.testing.assert_allclose(zero['motion'][i][key], raw['motion'][0][key], atol=1e-6)

    def test_invalid_templates_and_gains_are_rejected(self):
        for gain in (-.1, 1.1, float('nan')):
            with self.assertRaises(ValueError): regional_motion(template(), eye_gain=gain)
        for change in ('count', 'nan', 'shape', 'rotation'):
            bad = template()
            if change == 'count': bad['n_frames'] = 3
            if change == 'nan': bad['motion'][1]['exp'][0, 0, 0] = np.nan
            if change == 'shape': bad['motion'][1]['exp'] = np.zeros((1, 20, 3))
            if change == 'rotation': bad['motion'][1]['R'][0, 0, 0] = 3
            with self.assertRaises(ValueError): regional_motion(bad)


if __name__ == '__main__': unittest.main()
