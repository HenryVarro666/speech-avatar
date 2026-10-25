"""Bounded relative gains on a copied, native LivePortrait human template.

The eye indices are the pinned upstream animation_region='eyes' mapping.
This is an experiment adapter, not an anatomical or naturalness guarantee.
"""
import copy

import cv2
import numpy as np

EYE_INDICES = (11, 13, 15, 16, 18)


def regional_motion(template, *, pose_gain=.65, expression_gain=.65, eye_gain=1.):
    gains = (pose_gain, expression_gain, eye_gain)
    if not all(np.isfinite(g) and 0 <= g <= 1 for g in gains):
        raise ValueError('Gains must be finite values in [0,1]')
    frames = template.get('motion', [])
    if not frames or len(frames) != template.get('n_frames'):
        raise ValueError('Motion frame count mismatch')
    shapes = {'R': (1, 3, 3), 'exp': (1, 21, 3), 'kp': (1, 21, 3),
              't': (1, 3), 'scale': (1, 1)}
    for frame in frames:
        for key, shape in shapes.items():
            value = np.asarray(frame.get(key))
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError(f'Invalid template {key}')
        rotation = frame['R'][0]
        if not (np.allclose(rotation @ rotation.T, np.eye(3), atol=1e-4)
                and np.isclose(np.linalg.det(rotation), 1., atol=1e-4)):
            raise ValueError('Expected proper SO(3) rotation')
    output = copy.deepcopy(template)
    first = frames[0]
    expression_gains = np.full((1, 21, 1), expression_gain, dtype=np.float32)
    expression_gains[:, EYE_INDICES, :] = eye_gain
    for raw, frame in zip(frames, output['motion']):
        relative = raw['R'][0] @ first['R'][0].T
        if pose_gain == 0:
            frame['R'] = first['R'].copy()
        elif pose_gain != 1:
            vector = cv2.Rodrigues(relative.astype(np.float64))[0]
            rotation = cv2.Rodrigues(vector * pose_gain)[0] @ first['R'][0]
            frame['R'] = rotation[None].astype(raw['R'].dtype)
        for key in ('t', 'scale'):
            frame[key] = first[key] + pose_gain * (raw[key] - first[key])
        frame['exp'] = first['exp'] + expression_gains * (raw['exp'] - first['exp'])
        # Match native transform_keypoint; z translation is deliberately omitted.
        frame['x_s'] = frame['scale'] * (frame['kp'] @ frame['R'] + frame['exp'])
        frame['x_s'][..., :2] += frame['t'][:, None, :2]
    return output
