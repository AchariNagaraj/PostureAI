# ml/tests/test_target_tracker_full.py
"""Comprehensive Unit & Integration Test Suite for TargetTracker Subsystem.

Verifies all person detection, target selection, temporal tracking, safety rules,
and edge cases, including the CRITICAL SAFETY RULE: NEVER SILENTLY SWITCH TARGET PERSON.
"""

import pytest
from ml.inference.target_tracker import TargetTracker, calculate_iou


def create_mock_candidate(temp_id: int, center_x: float, center_y: float, width: float = 0.3, height: float = 0.6):
    """Helper to construct mock person candidate dict."""
    bbox = {
        "x": round(center_x - width / 2.0, 4),
        "y": round(center_y - height / 2.0, 4),
        "width": round(width, 4),
        "height": round(height, 4),
    }
    # Mock landmarks (33 dummy landmark items)
    mock_landmarks = [{"x": center_x, "y": center_y, "z": 0.0, "visibility": 0.9} for _ in range(33)]
    return {
        "temp_id": temp_id,
        "bbox": bbox,
        "center": (center_x, center_y),
        "landmarks": mock_landmarks,
        "confidence": 0.95,
    }


def test_single_person_auto_selection():
    tracker = TargetTracker()
    cand1 = create_mock_candidate(1, 0.5, 0.5)

    payload = tracker.process_candidates([cand1])

    assert payload["person_state"] == "ONE_PERSON"
    assert payload["tracking_state"] == "TARGET_TRACKING"
    assert payload["target_selected"] is True
    assert payload["target_id"] == 1
    assert payload["pose_valid"] is True
    assert payload["target_bbox"] == cand1["bbox"]


def test_multiple_people_requires_selection():
    tracker = TargetTracker()
    cand1 = create_mock_candidate(1, 0.3, 0.5)
    cand2 = create_mock_candidate(2, 0.7, 0.5)

    payload = tracker.process_candidates([cand1, cand2])

    assert payload["person_state"] == "MULTIPLE_PEOPLE"
    assert payload["tracking_state"] == "AWAITING_SELECTION"
    assert payload["target_selected"] is False
    assert payload["target_id"] is None
    assert payload["pose_valid"] is False
    assert len(payload["candidates"]) == 2


def test_explicit_target_selection():
    tracker = TargetTracker()
    cand1 = create_mock_candidate(1, 0.3, 0.5)
    cand2 = create_mock_candidate(2, 0.7, 0.5)

    # User selects candidate #2
    payload = tracker.process_candidates([cand1, cand2], manual_target_id=2)

    assert payload["person_state"] == "MULTIPLE_PEOPLE"
    assert payload["tracking_state"] == "TARGET_TRACKING"
    assert payload["target_selected"] is True
    assert payload["target_id"] == 2
    assert payload["pose_valid"] is True


def test_click_target_selection():
    tracker = TargetTracker()
    cand1 = create_mock_candidate(1, 0.2, 0.5)
    cand2 = create_mock_candidate(2, 0.8, 0.5)

    # User clicks at (0.81, 0.52) near candidate #2
    payload = tracker.process_candidates([cand1, cand2], click_coords=(0.81, 0.52))

    assert payload["target_selected"] is True
    assert payload["target_id"] == 2
    assert payload["tracking_state"] == "TARGET_TRACKING"


def test_safety_rule_never_silently_switch_target():
    """CRITICAL SAFETY TEST:
    If Person A is selected, Person A leaves and Person B remains,
    the system MUST NOT silently switch to Person B!
    """
    tracker = TargetTracker(max_missing_allowed=3)
    person_a = create_mock_candidate(1, 0.3, 0.5)
    person_b = create_mock_candidate(2, 0.7, 0.5)

    # 1. Lock onto Person A
    tracker.process_candidates([person_a, person_b], manual_target_id=1)

    # 2. Person A leaves. Only Person B remains in frame.
    payload_frame2 = tracker.process_candidates([person_b])

    # MUST NOT evaluate Person B or set target_id to 2!
    assert payload_frame2["tracking_state"] == "TEMPORARILY_LOST"
    assert payload_frame2["target_id"] == 1
    assert payload_frame2["pose_valid"] is False

    # 3. Person A remains absent for several frames exceeding timeout
    for _ in range(4):
        payload_lost = tracker.process_candidates([person_b])

    assert payload_lost["tracking_state"] in ("TARGET_LOST", "AWAITING_CONFIRMATION")
    assert payload_lost["reselection_required"] is True
    assert payload_lost["pose_valid"] is False
    assert payload_lost["target_id"] == 1  # Kept reference, did not switch to 2!


def test_target_temporary_disappearance_and_recovery():
    tracker = TargetTracker(max_missing_allowed=5)
    person_a = create_mock_candidate(1, 0.5, 0.5)

    # Frame 1: Target visible
    p1 = tracker.process_candidates([person_a])
    assert p1["tracking_state"] == "TARGET_TRACKING"

    # Frame 2-3: Target temporarily missing
    p2 = tracker.process_candidates([])
    assert p2["tracking_state"] == "TEMPORARILY_LOST"
    assert p2["pose_valid"] is False

    # Frame 4: Target returns near expected center (0.52, 0.51)
    person_a_returned = create_mock_candidate(1, 0.52, 0.51)
    p4 = tracker.process_candidates([person_a_returned])

    assert p4["tracking_state"] == "TARGET_TRACKING"
    assert p4["target_id"] == 1
    assert p4["pose_valid"] is True


def test_ambiguous_reacquisition():
    tracker = TargetTracker(max_missing_allowed=5)
    person_a = create_mock_candidate(1, 0.5, 0.5)

    tracker.process_candidates([person_a])

    # Target missing briefly
    tracker.process_candidates([])

    # Two candidate persons appear close to previous location (0.48, 0.5) and (0.52, 0.5)
    cand_left = create_mock_candidate(1, 0.48, 0.5)
    cand_right = create_mock_candidate(2, 0.52, 0.5)

    payload = tracker.process_candidates([cand_left, cand_right])

    assert payload["tracking_state"] == "AWAITING_CONFIRMATION"
    assert payload["pose_valid"] is False


def test_another_person_enters():
    tracker = TargetTracker()
    person_a = create_mock_candidate(1, 0.3, 0.5)

    # 1. Single person locked
    tracker.process_candidates([person_a])

    # 2. Person B enters scene at x=0.8
    person_b = create_mock_candidate(2, 0.8, 0.5)
    payload = tracker.process_candidates([person_a, person_b])

    assert payload["person_state"] == "MULTIPLE_PEOPLE"
    assert payload["tracking_state"] == "TARGET_TRACKING"
    assert payload["target_id"] == 1
    assert payload["pose_valid"] is True
    assert payload["target_bbox"] == person_a["bbox"]


def test_no_person_state():
    tracker = TargetTracker()
    payload = tracker.process_candidates([])

    assert payload["person_state"] == "NO_PERSON"
    assert payload["tracking_state"] == "NO_TARGET"
    assert payload["target_selected"] is False
    assert payload["pose_valid"] is False


def test_reset_clears_target():
    tracker = TargetTracker()
    person_a = create_mock_candidate(1, 0.5, 0.5)

    tracker.process_candidates([person_a])
    assert tracker.target_selected is True

    tracker.reset()
    assert tracker.target_selected is False
    assert tracker.target_id is None
    assert tracker.tracking_state == "NO_TARGET"


def test_iou_calculation():
    boxA = {"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5}
    boxB = {"x": 0.25, "y": 0.0, "width": 0.5, "height": 0.5}

    iou = calculate_iou(boxA, boxB)
    # Intersection = 0.25 * 0.5 = 0.125
    # Union = 0.25 + 0.25 - 0.125 = 0.375
    # IoU = 0.125 / 0.375 = 0.3333...
    assert round(iou, 3) == 0.333
