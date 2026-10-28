# ml/tests/test_phase10_step3_4.py
"""Automated Pytest suite for Phase 10 Steps 3 & 4: Target tracking, viewpoint estimation, and WebSocket integration."""

import pytest
from ml.inference.target_tracker import TargetTracker
from ml.inference.viewpoint_estimator import estimate_viewpoint
from ml.inference.inference_service import InferenceEngine


class MockLandmark:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def generate_mock_landmarks(dx=0.0, dy=0.0, dz=0.0):
    landmarks = [MockLandmark(0.5, 0.5, 0.0) for _ in range(33)]
    # Left shoulder at 11, Right shoulder at 12
    landmarks[11] = MockLandmark(0.4 + dx, 0.5 + dy, 0.0 + dz)
    landmarks[12] = MockLandmark(0.6 + dx, 0.5 + dy, 0.0)
    return landmarks


def test_target_tracker_single_person():
    """Verify single person detection enters TRACKING state."""
    tracker = TargetTracker()
    lm = generate_mock_landmarks()
    res = tracker.process_pose(True, lm)
    assert res["person_state"] == "ONE_PERSON"
    assert res["tracking_state"] == "TRACKING"
    assert res["pose_valid"] is True


def test_target_tracker_no_person():
    """Verify no person detection transitions to SEARCHING / TARGET_LOST safely."""
    tracker = TargetTracker()
    res = tracker.process_pose(False, None)
    assert res["person_state"] == "NO_PERSON"
    assert res["tracking_state"] == "SEARCHING"
    assert res["pose_valid"] is False


def test_target_tracker_spatial_jump_guard():
    """Verify sudden spatial target jump triggers RESELECT_REQUIRED state guard."""
    tracker = TargetTracker()
    lm1 = generate_mock_landmarks(dx=0.0, dy=0.0)
    tracker.process_pose(True, lm1)

    # Spatial jump to far side of frame (dx = 0.5)
    lm2 = generate_mock_landmarks(dx=0.5, dy=0.5)
    res = tracker.process_pose(True, lm2)

    assert res["person_state"] == "MULTIPLE_PEOPLE"
    assert res["tracking_state"] == "RESELECT_REQUIRED"
    assert res["pose_valid"] is False


def test_viewpoint_estimation_front():
    """Verify frontal shoulder orientation classifies as FRONT."""
    lm = generate_mock_landmarks(dz=0.0)
    vp = estimate_viewpoint(lm)
    assert vp == "FRONT"


def test_viewpoint_estimation_profile():
    """Verify profile depth shift classifies as PROFILE / 3_4 viewpoint."""
    lm = generate_mock_landmarks(dz=0.3) # Significant z-depth delta
    vp = estimate_viewpoint(lm)
    assert vp in ["LEFT_PROFILE", "RIGHT_PROFILE", "LEFT_3_4", "RIGHT_3_4"]


def test_viewpoint_estimation_unknown():
    """Verify invalid / insufficient landmarks return UNKNOWN viewpoint."""
    assert estimate_viewpoint([]) == "UNKNOWN"
    assert estimate_viewpoint(None) == "UNKNOWN"


def test_inference_engine_with_target_and_viewpoint():
    """Verify InferenceEngine integrates tracking state and viewpoint correctly."""
    engine = InferenceEngine()
    lm = generate_mock_landmarks()
    vp = estimate_viewpoint(lm)

    result = engine.process(
        timestamp=1000.0,
        landmarks=lm,
        viewpoint=vp,
        tracking_state="TRACKING",
        pose_valid=True,
    )

    assert result["viewpoint"] == "FRONT"
    assert result["tracking_state"] == "TRACKING"
    assert result["pose_valid"] is True
    assert "posture" in result
    assert "risk_score" in result
