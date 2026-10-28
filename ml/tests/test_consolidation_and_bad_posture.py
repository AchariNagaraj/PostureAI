# ml/tests/test_consolidation_and_bad_posture.py
import pytest
import time
from ml.risk.temporal_risk_engine import TemporalRiskEngine, TemporalRiskConfig
from ml.inference.inference_service import InferenceEngine
from ml.inference.target_tracker import TargetTracker

def test_upright_posture_gives_good_state():
    cfg = TemporalRiskConfig(persistence_duration=2.0)
    engine = TemporalRiskEngine(cfg)
    t0 = time.time()

    # Upright posture evaluation
    eval_good = {
        "overall_status": "GOOD",
        "head": {"status": "GOOD"},
        "shoulder": {"status": "GOOD"},
        "trunk": {"status": "GOOD"},
    }
    alert = engine.process(timestamp=t0, label="TUP", confidence=0.95, posture_evaluation=eval_good)
    assert alert is None
    assert engine.state.value in ("NORMAL", "WATCH")

def test_sustained_head_tilt_triggers_bad_and_alert():
    cfg = TemporalRiskConfig(persistence_duration=1.0)
    engine = TemporalRiskEngine(cfg)
    t0 = time.time()

    eval_head_bad = {
        "overall_status": "BAD",
        "head": {"status": "BAD", "detail": "Head tilt detected"},
        "shoulder": {"status": "GOOD"},
        "trunk": {"status": "GOOD"},
    }

    # Initial frame: risk elevated but persistence duration not reached
    alert1 = engine.process(timestamp=t0, label="TUP", confidence=0.90, posture_evaluation=eval_head_bad)
    assert alert1 is None

    # Frame after persistence_duration: MUST trigger ACTIVE_RISK and alert_event
    alert2 = engine.process(timestamp=t0 + 1.5, label="TUP", confidence=0.90, posture_evaluation=eval_head_bad)
    assert alert2 is not None
    assert alert2["risk_level"] == "ALERT"
    assert alert2["message"] == "You're compromising with your posture. Please correct your posture."
    assert alert2["voice_message"] == "You're compromising with your posture. Please correct your posture."
    assert alert2["alert_type"] == "PERSISTENT_HEAD_TILT"

def test_sustained_shoulder_misalignment_triggers_bad_and_alert():
    cfg = TemporalRiskConfig(persistence_duration=1.0)
    engine = TemporalRiskEngine(cfg)
    t0 = time.time()

    eval_shoulder_bad = {
        "overall_status": "BAD",
        "head": {"status": "GOOD"},
        "shoulder": {"status": "BAD", "detail": "Shoulder misaligned"},
        "trunk": {"status": "GOOD"},
    }

    engine.process(timestamp=t0, label="TUP", confidence=0.90, posture_evaluation=eval_shoulder_bad)
    alert = engine.process(timestamp=t0 + 1.5, label="TUP", confidence=0.90, posture_evaluation=eval_shoulder_bad)

    assert alert is not None
    assert alert["alert_type"] == "PERSISTENT_SHOULDER_MISALIGNMENT"
    assert alert["message"] == "You're compromising with your posture. Please correct your posture."

def test_sustained_trunk_tilt_triggers_bad_and_alert():
    cfg = TemporalRiskConfig(persistence_duration=1.0)
    engine = TemporalRiskEngine(cfg)
    t0 = time.time()

    eval_trunk_bad = {
        "overall_status": "BAD",
        "head": {"status": "GOOD"},
        "shoulder": {"status": "GOOD"},
        "trunk": {"status": "BAD", "detail": "Trunk pitch tilt"},
    }

    engine.process(timestamp=t0, label="TLF", confidence=0.95, posture_evaluation=eval_trunk_bad)
    alert = engine.process(timestamp=t0 + 1.5, label="TLF", confidence=0.95, posture_evaluation=eval_trunk_bad)

    assert alert is not None
    assert alert["message"] == "You're compromising with your posture. Please correct your posture."

def test_target_loss_and_return_requires_explicit_confirmation():
    tracker = TargetTracker(max_missing_allowed=3)
    cand = {
        "temp_id": 1,
        "bbox": {"x": 0.2, "y": 0.2, "width": 0.4, "height": 0.6},
        "center": (0.4, 0.5),
        "landmarks": [],
        "confidence": 0.9,
    }

    # Lock target
    res1 = tracker.process_candidates([cand])
    assert res1["tracking_state"] == "TARGET_TRACKING"
    assert res1["pose_valid"] is True

    # User leaves camera view for 4 consecutive frames (> max_missing_allowed)
    for _ in range(4):
        res = tracker.process_candidates([])
    assert res["tracking_state"] == "TARGET_LOST"
    assert res["pose_valid"] is False

    # Person returns into view -> system MUST NOT automatically start tracking
    res_return = tracker.process_candidates([cand])
    assert res_return["tracking_state"] == "AWAITING_CONFIRMATION"
    assert res_return["pose_valid"] is False
    assert res_return["reselection_required"] is True

    # Only after explicit user selection should tracking resume
    res_confirm = tracker.process_candidates([cand], manual_target_id=1)
    assert res_confirm["tracking_state"] == "TARGET_TRACKING"
    assert res_confirm["pose_valid"] is True
