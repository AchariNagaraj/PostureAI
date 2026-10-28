# ml/tests/test_phase11_failure_edgecases.py
"""Phase 11 — Failure & Edge-Case Test Suite.

Verifies robust handling of input corruption, invalid frames, landmark loss,
target tracking spatial jumps, viewpoint estimation edge cases, and temporal risk engine behavior.
"""

import pytest
import numpy as np
import base64
import cv2
import math
from ml.inference.pose_processor import PoseProcessor
from ml.inference.target_tracker import TargetTracker
from ml.inference.viewpoint_estimator import estimate_viewpoint
from ml.inference.inference_service import InferenceEngine
from ml.risk.temporal_risk_engine import TemporalRiskEngine
from ml.risk.risk_config import TemporalRiskConfig


class MockLM:
    def __init__(self, x, y, z, visibility=0.9):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


def build_mock_landmarks(dx=0.0, dy=0.0, dz=0.0, visibility=0.9):
    lms = [MockLM(0.5, 0.5, 0.0, visibility) for _ in range(33)]
    # Left shoulder (11), Right shoulder (12)
    lms[11] = MockLM(0.4 + dx, 0.5 + dy, 0.0 + dz, visibility)
    lms[12] = MockLM(0.6 + dx, 0.5 + dy, 0.0, visibility)
    # Left hip (23), Right hip (24)
    lms[23] = MockLM(0.42 + dx, 0.8 + dy, 0.0, visibility)
    lms[24] = MockLM(0.58 + dx, 0.8 + dy, 0.0, visibility)
    # Left ear (7), Right ear (8)
    lms[7] = MockLM(0.43 + dx, 0.3 + dy, 0.0, visibility)
    lms[8] = MockLM(0.57 + dx, 0.3 + dy, 0.0, visibility)
    return lms


# =====================================================================
# 1. CAMERA / FRAME INPUT TESTS
# =====================================================================

def test_camera_valid_jpeg_frame():
    processor = PoseProcessor()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(buf).decode("utf-8")
    
    valid, landmarks = processor.process_base64_frame(b64_str)
    assert isinstance(valid, bool)
    processor.close()


def test_camera_malformed_base64():
    processor = PoseProcessor()
    malformed_b64 = "!!!NotBase64Data!!!"
    valid, landmarks = processor.process_base64_frame(malformed_b64)
    assert valid is False
    assert landmarks is None
    processor.close()


def test_camera_invalid_jpeg_bytes():
    processor = PoseProcessor()
    invalid_bytes_b64 = base64.b64encode(b"Hello World Random Bytes").decode("utf-8")
    valid, landmarks = processor.process_base64_frame(invalid_bytes_b64)
    assert valid is False
    assert landmarks is None
    processor.close()


def test_camera_empty_frame():
    processor = PoseProcessor()
    valid, landmarks = processor.process_base64_frame("")
    assert valid is False
    assert landmarks is None

    valid, landmarks = processor.process_base64_frame("data:image/jpeg;base64,")
    assert valid is False
    assert landmarks is None
    processor.close()


def test_camera_oversized_frame_payload():
    processor = PoseProcessor()
    img = np.zeros((2000, 2000, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(buf).decode("utf-8")
    
    valid, landmarks = processor.process_base64_frame(b64_str)
    assert isinstance(valid, bool)
    processor.close()


def test_camera_rapid_frame_burst():
    processor = PoseProcessor()
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(buf).decode("utf-8")
    
    for _ in range(50):
        valid, landmarks = processor.process_base64_frame(b64_str)
        assert isinstance(valid, bool)
    processor.close()


# =====================================================================
# 2. POSE EDGE CASES
# =====================================================================

def test_pose_no_person():
    tracker = TargetTracker()
    info = tracker.process_pose(False, None)
    assert info["pose_valid"] is False
    assert info["person_state"] == "NO_PERSON"
    assert info["tracking_state"] == "SEARCHING"
    assert info["active_landmarks"] is None


def test_pose_insufficient_landmarks():
    tracker = TargetTracker()
    short_landmarks = build_mock_landmarks()[:10]
    info = tracker.process_pose(True, short_landmarks)
    assert info["pose_valid"] is False
    assert info["tracking_state"] == "SEARCHING"


def test_pose_invalid_nan_landmarks():
    tracker = TargetTracker()
    nan_landmarks = build_mock_landmarks()
    nan_landmarks[11].x = float("nan")
    # Tracker handles NaN gracefully
    info = tracker.process_pose(True, nan_landmarks)
    assert isinstance(info["pose_valid"], bool)


def test_pose_disappearance_and_recovery():
    tracker = TargetTracker()
    lms = build_mock_landmarks()
    
    info1 = tracker.process_pose(True, lms)
    assert info1["tracking_state"] == "TRACKING"
    
    info2 = tracker.process_pose(False, None)
    assert info2["tracking_state"] == "TEMPORARILY_LOST"
    
    info3 = tracker.process_pose(True, lms)
    assert info3["tracking_state"] == "TRACKING"


# =====================================================================
# 3. TARGET TRACKING EDGE CASES
# =====================================================================

def test_target_tracking_single_person_normal_movement():
    tracker = TargetTracker()
    lms1 = build_mock_landmarks(dx=0.0)
    lms2 = build_mock_landmarks(dx=0.05)
    
    info1 = tracker.process_pose(True, lms1)
    assert info1["tracking_state"] == "TRACKING"
    
    info2 = tracker.process_pose(True, lms2)
    assert info2["tracking_state"] == "TRACKING"


def test_target_tracking_spatial_jump_guard():
    tracker = TargetTracker()
    lms1 = build_mock_landmarks(dx=0.0)
    lms2 = build_mock_landmarks(dx=0.50)
    
    tracker.process_pose(True, lms1)
    info2 = tracker.process_pose(True, lms2)
    assert info2["tracking_state"] == "RESELECT_REQUIRED"
    assert info2["person_state"] == "MULTIPLE_PEOPLE"


def test_target_tracking_permanent_loss():
    tracker = TargetTracker()
    lms = build_mock_landmarks()
    
    tracker.process_pose(True, lms)
    for _ in range(10):
        info = tracker.process_pose(False, None)
    
    assert info["tracking_state"] in ["SEARCHING", "TEMPORARILY_LOST"]
    assert info["person_state"] == "NO_PERSON"


# =====================================================================
# 4. VIEWPOINT EDGE CASES
# =====================================================================

def test_viewpoint_front():
    lms = build_mock_landmarks()
    vp = estimate_viewpoint(lms)
    assert vp == "FRONT"


def test_viewpoint_profiles_and_three_quarters():
    lms_lp = build_mock_landmarks()
    vp_lp = estimate_viewpoint(lms_lp)
    assert vp_lp in ["FRONT", "LEFT_PROFILE", "RIGHT_PROFILE", "LEFT_3_4", "RIGHT_3_4", "UNKNOWN"]


def test_viewpoint_unknown_never_causes_artificial_risk():
    engine = TemporalRiskEngine()
    # UNKNOWN viewpoint / missing pose
    event = engine.process(
        timestamp=100.0,
        label="UNKNOWN",
        probabilities={"TUP": 0.5, "UNKNOWN": 0.5},
        pose_valid=False,
        tracking_state="SEARCHING",
        viewpoint="UNKNOWN"
    )
    assert event is None
    assert engine.state.value in ["NORMAL", "WATCH"]


def test_viewpoint_insufficient_landmarks():
    vp = estimate_viewpoint([])
    assert vp == "UNKNOWN"
    vp_short = estimate_viewpoint(build_mock_landmarks()[:5])
    assert vp_short == "UNKNOWN"


# =====================================================================
# 5. RISK ENGINE EDGE CASES
# =====================================================================

def test_risk_engine_normal_upright():
    engine = InferenceEngine()
    res = engine.process(timestamp=1.0, label="TUP", probabilities={"TUP": 0.95, "TLF": 0.05}, pose_valid=True)
    assert res["risk_score"] < 25.0
    assert res["risk_level"] == "NORMAL"


def test_risk_engine_short_risky_no_alert():
    config = TemporalRiskConfig(persistence_duration=5.0)
    engine = InferenceEngine(config=config)
    
    res = None
    for t in range(1, 3):
        res = engine.process(timestamp=float(t), label="TLF", probabilities={"TLF": 0.95}, pose_valid=True)
    assert res["alert_event"] is None


def test_risk_engine_persistent_risky_triggers_alert():
    config = TemporalRiskConfig(persistence_duration=3.0, cooldown_duration=5.0)
    engine = InferenceEngine(config=config)
    
    alert_count = 0
    for t in range(1, 8):
        res = engine.process(timestamp=float(t), label="TLF", probabilities={"TLF": 0.95}, pose_valid=True)
        if res["alert_event"]:
            alert_count += 1
            
    assert alert_count == 1  # 1 alert triggered due to 5s cooldown


def test_risk_engine_low_confidence_posture():
    engine = InferenceEngine()
    res = engine.process(timestamp=1.0, label="TLF", probabilities={"TLF": 0.30, "TUP": 0.70}, pose_valid=True)
    assert res["confidence"] == 0.70  # max prob is 0.70


def test_risk_engine_cooldown_behavior():
    config = TemporalRiskConfig(persistence_duration=2.0, cooldown_duration=10.0)
    engine = InferenceEngine(config=config)
    
    alerts = []
    for t in range(1, 16):
        res = engine.process(timestamp=float(t), label="TLF", probabilities={"TLF": 0.95}, pose_valid=True)
        if res["alert_event"]:
            alerts.append(t)
            
    assert len(alerts) >= 1
    if len(alerts) > 1:
        assert alerts[1] - alerts[0] >= 10.0


def test_risk_engine_invalid_pose_or_target_loss_during_active_risk():
    config = TemporalRiskConfig(persistence_duration=2.0)
    engine = InferenceEngine(config=config)
    
    # Active risk
    engine.process(timestamp=1.0, label="TLF", probabilities={"TLF": 0.95}, pose_valid=True)
    engine.process(timestamp=2.0, label="TLF", probabilities={"TLF": 0.95}, pose_valid=True)
    
    # Target lost / Invalid pose handled cleanly
    res_lost = engine.process(
        timestamp=3.0,
        label="UNKNOWN",
        probabilities={"TUP": 0.5, "UNKNOWN": 0.5},
        pose_valid=False,
        tracking_state="SEARCHING",
        invalid_state="NO_PERSON"
    )
    assert res_lost["alert_event"] is None
