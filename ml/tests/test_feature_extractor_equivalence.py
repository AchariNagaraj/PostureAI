# ml/tests/test_feature_extractor_equivalence.py
"""Unit tests verifying real-time feature extractor equivalence with dataset specification."""

import math
import numpy as np
import pytest
from ml.inference.feature_extractor import (
    FEATURE_FUNCS,
    head_pitch,
    head_roll,
    forward_head_displacement,
    torso_pitch,
    torso_lateral_tilt,
    torso_rotation,
    shoulder_asymmetry,
    upper_arm_elevation,
)

class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

def get_standard_upright_landmarks():
    lms = [MockLandmark(0.5, 0.5, 0.0) for _ in range(33)]
    # Head & ears
    lms[0] = MockLandmark(0.50, 0.25, -0.05)  # nose
    lms[7] = MockLandmark(0.56, 0.23,  0.02)  # left ear (image right)
    lms[8] = MockLandmark(0.44, 0.23,  0.02)  # right ear (image left)

    # Shoulders & arms
    lms[11] = MockLandmark(0.62, 0.42, 0.00) # left shoulder
    lms[12] = MockLandmark(0.38, 0.42, 0.00) # right shoulder
    lms[13] = MockLandmark(0.65, 0.58, 0.02) # left elbow
    lms[14] = MockLandmark(0.35, 0.58, 0.02) # right elbow

    # Hips
    lms[23] = MockLandmark(0.60, 0.82, 0.05) # left hip
    lms[24] = MockLandmark(0.40, 0.82, 0.05) # right hip
    return lms

def test_feature_dimensionality_and_ordering():
    lms = get_standard_upright_landmarks()
    assert len(FEATURE_FUNCS) == 8
    feats = [fn(lms) for fn in FEATURE_FUNCS]
    assert len(feats) == 8
    assert all(math.isfinite(f) for f in feats)

def test_head_roll_uses_ears():
    lms = get_standard_upright_landmarks()
    roll = head_roll(lms)
    # Level ears (y=0.23 for both) -> atan2(0, -0.12) = 180 degrees
    assert abs(roll - 180.0) < 1e-3

def test_torso_lateral_tilt_uses_torso_vector():
    lms = get_standard_upright_landmarks()
    tilt = torso_lateral_tilt(lms)
    # Mid-shoulder = (0.50, 0.42), Mid-hip = (0.50, 0.82)
    # Torso vector = (0.0, -0.40) -> atan2(-0.40, 0.0) = -90 degrees
    assert abs(tilt - (-90.0)) < 1e-3

def test_torso_rotation_and_shoulder_asymmetry():
    lms = get_standard_upright_landmarks()
    rot = torso_rotation(lms)
    asym = shoulder_asymmetry(lms)
    assert math.isfinite(rot)
    assert abs(asym - 0.0) < 1e-3

def test_upper_arm_elevation_bilateral():
    lms = get_standard_upright_landmarks()
    elev = upper_arm_elevation(lms)
    # Arms hanging down naturally -> elevation near ~167 degrees
    assert 140.0 <= elev <= 180.0

def test_extended_head_and_shoulder_features():
    from ml.inference.feature_extractor import (
        craniovertebral_angle,
        neck_lateral_tilt,
        shoulder_diff,
        shoulder_tilt_angle,
        EXTENDED_FEATURE_FUNCS,
    )
    lms = get_standard_upright_landmarks()
    assert len(EXTENDED_FEATURE_FUNCS) == 12

    sd = shoulder_diff(lms)
    assert abs(sd - 0.0) < 1e-3  # Shoulders are at equal Y (0.42)

    sta = shoulder_tilt_angle(lms)
    assert math.isfinite(sta)

    cva = craniovertebral_angle(lms)
    assert math.isfinite(cva)

    nlt = neck_lateral_tilt(lms)
    assert math.isfinite(nlt)

