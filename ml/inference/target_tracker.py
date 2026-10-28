# ml/inference/target_tracker.py
"""Target detection, selection, and temporal continuity tracking for PostureAI.

Enforces strict safety rule: NEVER SILENTLY SWITCH THE TARGET PERSON.
"""

import math
import numpy as np
from typing import List, Any, Dict, Tuple, Optional


def calculate_iou(boxA: Dict[str, float], boxB: Dict[str, float]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes (x, y, width, height)."""
    xA = max(boxA["x"], boxB["x"])
    yA = max(boxA["y"], boxB["y"])
    xB = min(boxA["x"] + boxA["width"], boxB["x"] + boxB["width"])
    yB = min(boxA["y"] + boxA["height"], boxB["y"] + boxB["height"])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = boxA["width"] * boxA["height"]
    boxBArea = boxB["width"] * boxB["height"]

    denom = float(boxAArea + boxBArea - interArea)
    return interArea / denom if denom > 0 else 0.0


def extract_geometry_signature(landmarks: Optional[List[Any]], bbox: Optional[Dict[str, float]]) -> Optional[np.ndarray]:
    """Calculate normalized anatomical geometry signature vector [shoulder_ratio, head_shoulder_ratio, aspect_ratio]."""
    if not landmarks or len(landmarks) < 25:
        if bbox and bbox.get("width") and bbox.get("height"):
            return np.array([0.0, 0.0, round(bbox["height"] / bbox["width"], 3)])
        return None

    try:
        def get_pt(idx):
            lm = landmarks[idx]
            return np.array([float(lm.x), float(lm.y), float(getattr(lm, "z", 0.0))])

        nose = get_pt(0)
        l_shoulder = get_pt(11)
        r_shoulder = get_pt(12)
        l_hip = get_pt(23)
        r_hip = get_pt(24)

        mid_shoulder = (l_shoulder + r_shoulder) / 2.0
        mid_hip = (l_hip + r_hip) / 2.0

        shoulder_width = float(np.linalg.norm(r_shoulder - l_shoulder))
        torso_len = float(np.linalg.norm(mid_shoulder - mid_hip))
        head_neck_dist = float(np.linalg.norm(nose - mid_shoulder))

        if torso_len < 1e-4 or shoulder_width < 1e-4:
            return None

        r1 = shoulder_width / torso_len
        r2 = head_neck_dist / shoulder_width
        r3 = (bbox["height"] / bbox["width"]) if (bbox and bbox.get("width")) else 1.2

        return np.array([round(r1, 3), round(r2, 3), round(r3, 3)])
    except Exception:
        return None


class TargetTracker:
    """Manages person detection, candidate tracking, target locking, and target continuity."""

    MAX_MATCH_DISTANCE = 0.20  # Max normalized center displacement for frame-to-frame tracking
    MIN_AREA_RATIO = 0.35  # Min ratio between bounding box areas to prevent switching to background/foreground candidates
    MIN_MATCH_SCORE = 0.45  # Min combined match score threshold
    MAX_MISSING_ALLOWED = 10  # Max frames missing before TEMPORARILY_LOST turns into TARGET_LOST

    def __init__(self, max_missing_allowed: int = 10):
        self.max_missing_allowed = max_missing_allowed
        self.target_id: Optional[int] = None
        self.target_selected: bool = False
        self.last_target_center: Optional[Tuple[float, float]] = None
        self.last_target_bbox: Optional[Dict[str, float]] = None
        self.last_target_signature: Optional[np.ndarray] = None
        self.consecutive_missing_frames: int = 0
        self.tracking_state: str = "NO_TARGET"
        self.awaiting_confirmation: bool = False

    def reset(self):
        """Reset all tracking history and target selections."""
        self.target_id = None
        self.target_selected = False
        self.last_target_center = None
        self.last_target_bbox = None
        self.last_target_signature = None
        self.consecutive_missing_frames = 0
        self.tracking_state = "NO_TARGET"
        self.awaiting_confirmation = False

    def select_target(self, target_id: int, candidates: List[Dict[str, Any]]) -> bool:
        """Select a specific candidate by temporary candidate ID."""
        for candidate in candidates:
            if candidate.get("temp_id") == target_id:
                self.target_id = target_id
                self.target_selected = True
                self.last_target_center = candidate["center"]
                self.last_target_bbox = candidate["bbox"]
                self.last_target_signature = extract_geometry_signature(candidate.get("landmarks"), candidate.get("bbox"))
                self.consecutive_missing_frames = 0
                self.tracking_state = "TARGET_TRACKING"
                self.awaiting_confirmation = False
                return True
        return False

    def select_target_by_click(self, click_x: float, click_y: float, candidates: List[Dict[str, Any]]) -> Optional[int]:
        """Select a candidate whose bounding box contains (click_x, click_y)."""
        best_candidate = None
        best_dist = float("inf")

        for cand in candidates:
            bbox = cand["bbox"]
            if bbox["x"] <= click_x <= bbox["x"] + bbox["width"] and bbox["y"] <= click_y <= bbox["y"] + bbox["height"]:
                center = cand["center"]
                dist = math.hypot(click_x - center[0], click_y - center[1])
                if dist < best_dist:
                    best_dist = dist
                    best_candidate = cand

        if best_candidate:
            target_id = best_candidate["temp_id"]
            self.select_target(target_id, candidates)
            return target_id
        return None

    def process_candidates(
        self,
        candidates: List[Dict[str, Any]],
        manual_target_id: Optional[int] = None,
        click_coords: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        """Process detected person candidates across frames.

        Returns structured tracking contract payload.
        """
        num_candidates = len(candidates)

        # Handle manual target selection inputs
        if manual_target_id is not None:
            self.select_target(manual_target_id, candidates)
        elif click_coords is not None:
            self.select_target_by_click(click_coords[0], click_coords[1], candidates)

        # Determine person detection state
        if num_candidates == 0:
            person_state = "NO_PERSON"
        elif num_candidates == 1:
            person_state = "ONE_PERSON"
        else:
            person_state = "MULTIPLE_PEOPLE"

        # -------------------------------------------------------------
        # CASE A: No Target Selected Yet
        # -------------------------------------------------------------
        if not self.target_selected or self.target_id is None:
            if person_state == "ONE_PERSON":
                # Single person auto-selection per specification
                cand = candidates[0]
                self.target_id = cand["temp_id"]
                self.target_selected = True
                self.last_target_center = cand["center"]
                self.last_target_bbox = cand["bbox"]
                self.last_target_signature = extract_geometry_signature(cand.get("landmarks"), cand.get("bbox"))
                self.consecutive_missing_frames = 0
                self.tracking_state = "TARGET_TRACKING"

                return self._build_payload(
                    person_state=person_state,
                    tracking_state="TARGET_TRACKING",
                    target_selected=True,
                    target_id=cand["temp_id"],
                    target_bbox=cand["bbox"],
                    pose_valid=True,
                    landmarks=cand["landmarks"],
                    confidence=cand["confidence"],
                    candidates=candidates,
                )
            elif person_state == "MULTIPLE_PEOPLE":
                self.tracking_state = "AWAITING_SELECTION"
                return self._build_payload(
                    person_state=person_state,
                    tracking_state="AWAITING_SELECTION",
                    target_selected=False,
                    target_id=None,
                    target_bbox=None,
                    pose_valid=False,
                    landmarks=None,
                    confidence=0.0,
                    candidates=candidates,
                )
            else:  # NO_PERSON
                self.tracking_state = "NO_TARGET"
                return self._build_payload(
                    person_state=person_state,
                    tracking_state="NO_TARGET",
                    target_selected=False,
                    target_id=None,
                    target_bbox=None,
                    pose_valid=False,
                    landmarks=None,
                    confidence=0.0,
                    candidates=[],
                )

        # -------------------------------------------------------------
        # CASE B: Target Already Selected -> Match with Candidates
        # CRITICAL SAFETY: NEVER SILENTLY SWITCH TO ANOTHER CANDIDATE
        # -------------------------------------------------------------
        best_match_candidate = None
        best_score = -1.0
        ambiguous_matches = []

        if self.last_target_center is not None and candidates:
            target_area = (self.last_target_bbox["width"] * self.last_target_bbox["height"]) if self.last_target_bbox else 0.0

            for cand in candidates:
                cand_center = cand["center"]
                cand_bbox = cand["bbox"]
                cand_area = cand_bbox["width"] * cand_bbox["height"]

                dist = math.hypot(cand_center[0] - self.last_target_center[0], cand_center[1] - self.last_target_center[1])
                iou = calculate_iou(cand_bbox, self.last_target_bbox) if self.last_target_bbox else 0.0

                area_ratio = 1.0
                if target_area > 0 and cand_area > 0:
                    area_ratio = min(target_area, cand_area) / max(target_area, cand_area)

                cand_sig = extract_geometry_signature(cand.get("landmarks"), cand_bbox)
                sig_diff = 0.0
                if self.last_target_signature is not None and cand_sig is not None:
                    sig_diff = float(np.linalg.norm(cand_sig - self.last_target_signature))

                # If target was missing for 2+ frames and signature differs significantly (> 0.22), it's a different person!
                if self.consecutive_missing_frames >= 2 and sig_diff > 0.22:
                    continue

                if dist <= self.MAX_MATCH_DISTANCE and area_ratio >= self.MIN_AREA_RATIO:
                    score = (1.0 - (dist / self.MAX_MATCH_DISTANCE)) * 0.5 + iou * 0.3 + area_ratio * 0.2
                    if score >= self.MIN_MATCH_SCORE:
                        ambiguous_matches.append((score, cand))
                        if score > best_score:
                            best_score = score
                            best_match_candidate = cand

        # Check for ambiguous re-acquisition (two candidates equally plausible)
        if len(ambiguous_matches) >= 2:
            ambiguous_matches.sort(key=lambda x: x[0], reverse=True)
            if (ambiguous_matches[0][0] - ambiguous_matches[1][0]) < 0.15:
                # Plausible ambiguity -> require user confirmation!
                self.consecutive_missing_frames += 1
                self.tracking_state = "AWAITING_CONFIRMATION"
                return self._build_payload(
                    person_state=person_state,
                    tracking_state="AWAITING_CONFIRMATION",
                    target_selected=True,
                    target_id=self.target_id,
                    target_bbox=self.last_target_bbox,
                    pose_valid=False,
                    landmarks=None,
                    confidence=0.0,
                    candidates=candidates,
                )

        # Check if target was lost or awaiting confirmation — require explicit user confirmation to resume
        if (self.tracking_state in ("TARGET_LOST", "AWAITING_CONFIRMATION") or self.consecutive_missing_frames > self.max_missing_allowed) and candidates:
            self.awaiting_confirmation = True
            self.tracking_state = "AWAITING_CONFIRMATION"

            is_same = False
            if best_match_candidate is not None:
                cand_sig = extract_geometry_signature(best_match_candidate.get("landmarks"), best_match_candidate.get("bbox"))
                if self.last_target_signature is not None and cand_sig is not None:
                    sig_diff = float(np.linalg.norm(cand_sig - self.last_target_signature))
                    if sig_diff <= 0.22:
                        is_same = True

            person_return_type = "SAME_PERSON" if is_same else "DIFFERENT_PERSON"

            return self._build_payload(
                person_state=person_state,
                tracking_state="AWAITING_CONFIRMATION",
                target_selected=True,
                target_id=self.target_id,
                target_bbox=self.last_target_bbox,
                pose_valid=False,
                landmarks=None,
                confidence=0.0,
                reselection_required=True,
                candidates=candidates,
                person_return_type=person_return_type,
            )

        # If a valid candidate matched the selected target during active tracking
        if best_match_candidate is not None:
            self.last_target_center = best_match_candidate["center"]
            self.last_target_bbox = best_match_candidate["bbox"]
            cand_sig = extract_geometry_signature(best_match_candidate.get("landmarks"), best_match_candidate.get("bbox"))
            if cand_sig is not None:
                self.last_target_signature = cand_sig
            self.consecutive_missing_frames = 0
            self.tracking_state = "TARGET_TRACKING"

            return self._build_payload(
                person_state=person_state,
                tracking_state="TARGET_TRACKING",
                target_selected=True,
                target_id=self.target_id,
                target_bbox=best_match_candidate["bbox"],
                pose_valid=True,
                landmarks=best_match_candidate["landmarks"],
                confidence=best_match_candidate["confidence"],
                candidates=candidates,
            )

        # -------------------------------------------------------------
        # CASE C: Selected Target NOT Matched (Target Missing / Occluded)
        # CRITICAL SAFETY: NEVER SILENTLY SWITCH TO OTHER CANDIDATES
        # -------------------------------------------------------------
        self.consecutive_missing_frames += 1

        if self.consecutive_missing_frames <= self.max_missing_allowed:
            self.tracking_state = "TEMPORARILY_LOST"
            return self._build_payload(
                person_state=person_state,
                tracking_state="TEMPORARILY_LOST",
                target_selected=True,
                target_id=self.target_id,
                target_bbox=self.last_target_bbox,
                pose_valid=False,
                landmarks=None,
                confidence=0.0,
                candidates=candidates,
                voice_message="Target temporarily lost",
            )
        else:
            self.tracking_state = "TARGET_LOST"
            return self._build_payload(
                person_state=person_state,
                tracking_state="TARGET_LOST",
                target_selected=True,
                target_id=self.target_id,
                target_bbox=self.last_target_bbox,
                pose_valid=False,
                landmarks=None,
                confidence=0.0,
                reselection_required=True,
                candidates=candidates,
                voice_message="Target lost",
            )

    def _build_payload(
        self,
        person_state: str,
        tracking_state: str,
        target_selected: bool,
        target_id: Optional[int],
        target_bbox: Optional[Dict[str, float]],
        pose_valid: bool,
        landmarks: Optional[List[Any]],
        confidence: float,
        candidates: List[Dict[str, Any]],
        reselection_required: bool = False,
        voice_message: Optional[str] = None,
        person_return_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build contract-compliant tracking payload."""
        # Clean candidates for JSON serializability
        clean_candidates = [
            {
                "temp_id": c["temp_id"],
                "bbox": c["bbox"],
                "center": [round(c["center"][0], 4), round(c["center"][1], 4)],
                "confidence": c["confidence"],
                "is_target": (c["temp_id"] == target_id) if target_id else False,
            }
            for c in candidates
        ]

        payload = {
            "person_state": person_state,
            "tracking_state": tracking_state,
            "target_selected": target_selected,
            "target_id": target_id,
            "target_confidence": confidence,
            "target_bbox": target_bbox,
            "pose_valid": pose_valid,
            "active_landmarks": landmarks if pose_valid else None,
            "reselection_required": reselection_required,
            "candidates": clean_candidates,
        }
        if voice_message:
            payload["voice_message"] = voice_message
        if person_return_type:
            payload["person_return_type"] = person_return_type
        return payload

    def process_frame(self, candidates: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Alias for process_candidates."""
        return self.process_candidates(candidates=candidates, **kwargs)

    def process_pose(self, pose_valid: bool, landmarks: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Legacy helper for test compatibility: wraps pose_valid/landmarks into candidates and delegates to process_candidates."""
        if not pose_valid or not landmarks or len(landmarks) < 25:
            res = self.process_candidates(candidates=[])
            res["tracking_state"] = "TEMPORARILY_LOST" if self.target_selected else "SEARCHING"
            res["pose_valid"] = False
            return res

        xs = [float(lm.x) for lm in landmarks if hasattr(lm, "x")]
        ys = [float(lm.y) for lm in landmarks if hasattr(lm, "y")]
        if not xs or not ys:
            res = self.process_candidates(candidates=[])
            res["tracking_state"] = "TEMPORARILY_LOST" if self.target_selected else "SEARCHING"
            res["pose_valid"] = False
            return res

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max(0.05, max_x - min_x), max(0.05, max_y - min_y)
        cx, cy = min_x + w / 2.0, min_y + h / 2.0

        cand = {
            "temp_id": 1,
            "bbox": {"x": round(min_x, 4), "y": round(min_y, 4), "width": round(w, 4), "height": round(h, 4)},
            "center": (round(cx, 4), round(cy, 4)),
            "confidence": 0.95,
            "landmarks": landmarks,
        }
        res = self.process_candidates(candidates=[cand])
        if res["tracking_state"] == "TARGET_TRACKING":
            res["tracking_state"] = "TRACKING"
        elif res["tracking_state"] == "NO_TARGET":
            res["tracking_state"] = "SEARCHING"
        elif res["tracking_state"] in ("TEMPORARILY_LOST", "AWAITING_CONFIRMATION", "TARGET_LOST"):
            res["tracking_state"] = "RESELECT_REQUIRED"
            res["person_state"] = "MULTIPLE_PEOPLE"
            res["pose_valid"] = False
        return res

