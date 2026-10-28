# ml/inference/pose_processor.py
"""Python-side MediaPipe Pose processor for decoding frames and extracting multi-person candidate landmarks."""

import base64
from pathlib import Path
from typing import Tuple, Optional, Any, List, Dict
import cv2
import numpy as np
import mediapipe as mp

MODEL_TASK_PATH = Path("ml/models/pose_landmarker_lite.task")


class PoseProcessor:
    """Manages a MediaPipe PoseLandmarker instance supporting multi-person candidate detection."""

    def __init__(self, max_poses: int = 5):
        self.landmarker = None
        self.max_poses = max_poses
        if MODEL_TASK_PATH.is_file():
            try:
                base_options = mp.tasks.BaseOptions(model_asset_path=str(MODEL_TASK_PATH))
                options = mp.tasks.vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp.tasks.vision.RunningMode.IMAGE,
                    num_poses=self.max_poses,
                    min_pose_detection_confidence=0.45,
                    min_pose_presence_confidence=0.45,
                    min_tracking_confidence=0.45,
                )
                self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
            except Exception as exc:
                print(f"[PoseProcessor] Could not initialize PoseLandmarker: {exc}")

    def _extract_candidate_bbox(self, landmarks: List[Any]) -> Tuple[Dict[str, float], Tuple[float, float]]:
        """Calculate normalized bounding box and center coordinate for landmark set."""
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        x_min = max(0.0, min(x_coords))
        x_max = min(1.0, max(x_coords))
        y_min = max(0.0, min(y_coords))
        y_max = min(1.0, max(y_coords))
        width = max(0.02, x_max - x_min)
        height = max(0.02, y_max - y_min)
        center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
        bbox = {"x": round(x_min, 4), "y": round(y_min, 4), "width": round(width, 4), "height": round(height, 4)}
        return bbox, center

    def process_frame_bytes_candidates(self, frame_bytes: bytes) -> List[Dict[str, Any]]:
        """Decode image bytes and detect all pose candidates.
        
        Returns list of candidate dicts:
          [ { "id": idx, "bbox": {...}, "center": (cx, cy), "landmarks": [...], "confidence": float } ]
        """
        if self.landmarker is None:
            return []

        try:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self.landmarker.detect(mp_image)

            candidates = []
            if result and result.pose_landmarks:
                for idx, landmarks in enumerate(result.pose_landmarks):
                    if len(landmarks) >= 33:
                        bbox, center = self._extract_candidate_bbox(landmarks)
                        # Average visibility score if available
                        vis_scores = [getattr(lm, "visibility", 0.9) for lm in landmarks]
                        avg_vis = float(np.mean(vis_scores)) if vis_scores else 0.9
                        candidates.append({
                            "temp_id": idx + 1,
                            "bbox": bbox,
                            "center": center,
                            "landmarks": landmarks,
                            "confidence": round(avg_vis, 2),
                        })
            return candidates
        except Exception as exc:
            print(f"[PoseProcessor] Error processing frame: {exc}")
            return []

    def process_base64_candidates(self, base64_str: str) -> List[Dict[str, Any]]:
        """Decode base64 image string and return pose candidates."""
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",", 1)[1]
            frame_bytes = base64.b64decode(base64_str)
            return self.process_frame_bytes_candidates(frame_bytes)
        except Exception as exc:
            print(f"[PoseProcessor] Error decoding base64: {exc}")
            return []

    def process_frame_bytes(self, frame_bytes: bytes) -> Tuple[bool, Optional[List[Any]]]:
        """Backward-compatible single-pose processor."""
        candidates = self.process_frame_bytes_candidates(frame_bytes)
        if candidates:
            return True, candidates[0]["landmarks"]
        return False, None

    def process_base64_frame(self, base64_str: str) -> Tuple[bool, Optional[List[Any]]]:
        """Backward-compatible single-pose processor for base64 strings."""
        candidates = self.process_base64_candidates(base64_str)
        if candidates:
            return True, candidates[0]["landmarks"]
        return False, None

    def close(self):
        """Release MediaPipe PoseLandmarker resources."""
        if self.landmarker:
            try:
                self.landmarker.close()
            except Exception:
                pass
            self.landmarker = None

