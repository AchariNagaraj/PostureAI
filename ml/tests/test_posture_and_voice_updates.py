# ml/tests/test_posture_and_voice_updates.py
import pytest
import time
from ml.inference.target_tracker import TargetTracker
from ml.risk.temporal_risk_engine import TemporalRiskEngine, TemporalRiskConfig
from ml.inference.inference_service import InferenceEngine
from ml.analytics.service import process_metric_intervals

def test_target_lost_voice_notification():
    tracker = TargetTracker()
    cand = {
        "temp_id": 1,
        "bbox": {"x": 0.1, "y": 0.1, "width": 0.5, "height": 0.8},
        "center": (0.35, 0.5),
        "landmarks": [],
        "confidence": 0.9,
    }
    # Initial lock
    tracker.process_candidates([cand])
    assert tracker.tracking_state == "TARGET_TRACKING"

    # Target lost frame
    payload = tracker.process_candidates([])
    assert payload["tracking_state"] == "TEMPORARILY_LOST"
    assert "voice_message" in payload
    assert "Target temporarily lost" in payload["voice_message"]

def test_specific_postural_voice_guidance():
    cfg = TemporalRiskConfig(persistence_duration=1.0)
    engine = TemporalRiskEngine(cfg)
    t0 = time.time()
    
    # Process TLF risk
    engine.process(timestamp=t0, label="TLF", probabilities={"TLF": 0.95})
    alert = engine.process(timestamp=t0 + 1.5, label="TLF", probabilities={"TLF": 0.95})
    
    assert alert is not None
    assert "voice_message" in alert
    assert "You're compromising with your posture. Please correct your posture." in alert["voice_message"]

def test_inference_engine_recommendation():
    ie = InferenceEngine()
    output = ie.process(timestamp=time.time(), label="TLF", probabilities={"TLF": 0.90})
    assert output["recommendation"] is not None
    assert output["recommendation"]["description"] == "You're compromising with your posture. Please correct your posture."

def test_never_silently_switch_to_background_candidate():
    tracker = TargetTracker()
    foreground_target = {
        "temp_id": 1,
        "bbox": {"x": 0.2, "y": 0.2, "width": 0.5, "height": 0.7},
        "center": (0.45, 0.55),
        "landmarks": [1, 2, 3],
        "confidence": 0.95,
    }
    # Initial lock on Person #1 (Foreground)
    res1 = tracker.process_candidates([foreground_target])
    assert res1["target_id"] == 1
    assert res1["tracking_state"] == "TARGET_TRACKING"

    # Frame 2: Foreground person disappears, background person appears near center with small bbox area
    background_candidate = {
        "temp_id": 2,
        "bbox": {"x": 0.38, "y": 0.35, "width": 0.15, "height": 0.2},
        "center": (0.455, 0.45),
        "landmarks": [4, 5, 6],
        "confidence": 0.85,
    }
    res2 = tracker.process_candidates([background_candidate])
    # MUST NOT silently switch target to candidate #2!
    assert res2["target_id"] == 1
    assert res2["tracking_state"] == "TEMPORARILY_LOST"
    assert res2["pose_valid"] is False

def test_never_switch_when_different_person_sits_in_same_place():
    tracker = TargetTracker()
    class DummyLM:
        def __init__(self, x, y, z=0.0):
            self.x = x
            self.y = y
            self.z = z

    # Person A landmarks (e.g. broad shoulders: r_shoulder=(0.7,0.5), l_shoulder=(0.3,0.5), mid_hip=(0.5,0.8), nose=(0.5,0.3))
    lms_person_a = [DummyLM(0.5, 0.3)] + [DummyLM(0,0)] * 6 + [DummyLM(0.48, 0.31), DummyLM(0.52, 0.31)] + [DummyLM(0,0)] * 2 + [DummyLM(0.3, 0.5), DummyLM(0.7, 0.5)] + [DummyLM(0,0)] * 10 + [DummyLM(0.4, 0.8), DummyLM(0.6, 0.8)]
    cand_person_a = {
        "temp_id": 1,
        "bbox": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.6},
        "center": (0.5, 0.55),
        "landmarks": lms_person_a,
        "confidence": 0.95,
    }
    tracker.process_candidates([cand_person_a])
    assert tracker.tracking_state == "TARGET_TRACKING"

    # Person A vacates place for 2 frames
    tracker.process_candidates([])
    tracker.process_candidates([])
    assert tracker.consecutive_missing_frames == 2

    # Person B sits in the same place but has different geometry signature (e.g., narrow shoulders, tall head)
    lms_person_b = [DummyLM(0.5, 0.1)] + [DummyLM(0,0)] * 6 + [DummyLM(0.49, 0.11), DummyLM(0.51, 0.11)] + [DummyLM(0,0)] * 2 + [DummyLM(0.45, 0.5), DummyLM(0.55, 0.5)] + [DummyLM(0,0)] * 10 + [DummyLM(0.45, 0.8), DummyLM(0.55, 0.8)]
    cand_person_b = {
        "temp_id": 2,
        "bbox": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.6},
        "center": (0.5, 0.55),
        "landmarks": lms_person_b,
        "confidence": 0.90,
    }

    res = tracker.process_candidates([cand_person_b])
    # Must NOT automatically match Person B as Person ID #1!
    assert res["pose_valid"] is False
    assert res["tracking_state"] in ("TEMPORARILY_LOST", "AWAITING_CONFIRMATION")


