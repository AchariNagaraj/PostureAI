# ml/tests/test_phase10_step2.py
"""Automated Pytest suite for Phase 10 Step 2: Real frame transport & pose processing."""

import pytest
import numpy as np
import cv2
import base64
from unittest.mock import MagicMock, patch

from ml.inference.pose_processor import PoseProcessor
from ml.inference.inference_service import InferenceEngine


def generate_dummy_jpeg_base64(width=100, height=100) -> str:
    """Helper to generate a valid base64-encoded JPEG image buffer."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")


def test_pose_processor_invalid_frame():
    """Verify invalid/corrupt frame handling returns (False, None) without crashing."""
    processor = PoseProcessor()
    valid, landmarks = processor.process_base64_frame("invalid_base64_string")
    assert valid is False
    assert landmarks is None
    processor.close()


def test_pose_processor_blank_frame_no_pose():
    """Verify processing a blank image handles 'no pose detected' safely."""
    processor = PoseProcessor()
    b64_img = generate_dummy_jpeg_base64(100, 100)
    valid, landmarks = processor.process_base64_frame(b64_img)
    # Blank image should return False or None for pose_landmarks
    assert valid is False or landmarks is None
    processor.close()


def test_inference_engine_with_mock_landmarks():
    """Verify InferenceEngine.process() runs feature extraction and model inference when given landmarks."""
    engine = InferenceEngine()

    # Create 33 mock landmarks with valid x, y, z attributes
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    mock_landmarks = [MockLandmark(0.5, 0.5, 0.0) for _ in range(33)]

    result = engine.process(
        timestamp=1000.0,
        landmarks=mock_landmarks,
        viewpoint="FRONT",
        tracking_state="TRACKING",
        pose_valid=True,
    )

    assert "posture" in result
    assert result["posture"] in ["TUP", "TLB", "TLF", "TLL", "TLR"]
    assert "class_probabilities" in result
    assert "confidence" in result
    assert result["risk_level"] in ["NORMAL", "ALERT"]
    assert result["pose_valid"] is True
