import numpy as np
from typing import List, Callable, Any, Optional, Dict

# Feature extraction utilities – aligned strictly to dataset engineering specification
# (PostureAI_Dataset_Specification.md & feature_engineering_report.md)

def _get_xyz(lm: Any) -> np.ndarray:
    return np.array([float(lm.x), float(lm.y), float(getattr(lm, 'z', 0.0))])

def head_pitch(landmarks: List[Any]) -> float:
    """Signed forward/backward head inclination angle in degrees."""
    nose = _get_xyz(landmarks[0])
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    mid_shoulder = (left_shoulder + right_shoulder) / 2.0
    vec = nose - mid_shoulder
    return float(np.degrees(np.arctan2(vec[2], -vec[1])))

def head_roll(landmarks: List[Any]) -> float:
    """Signed left/right lateral head inclination angle in degrees."""
    left_ear = _get_xyz(landmarks[7])
    right_ear = _get_xyz(landmarks[8])
    vec = right_ear - left_ear
    return float(np.degrees(np.arctan2(vec[1], vec[0])))

def forward_head_displacement(landmarks: List[Any]) -> float:
    """Normalized forward displacement of head relative to torso length."""
    nose = _get_xyz(landmarks[0])
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    left_hip = _get_xyz(landmarks[23])
    right_hip = _get_xyz(landmarks[24])

    mid_shoulder = (left_shoulder + right_shoulder) / 2.0
    mid_hip = (left_hip + right_hip) / 2.0
    torso_length = float(np.linalg.norm(mid_shoulder - mid_hip))
    if torso_length < 1e-5:
        return 0.0
    forward_axis = np.array([0.0, 0.0, -1.0])
    disp = float(np.dot((nose - mid_shoulder), forward_axis))
    return disp / torso_length

def torso_pitch(landmarks: List[Any]) -> float:
    """Signed forward/backward trunk inclination angle in degrees."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    left_hip = _get_xyz(landmarks[23])
    right_hip = _get_xyz(landmarks[24])

    mid_shoulder = (left_shoulder + right_shoulder) / 2.0
    mid_hip = (left_hip + right_hip) / 2.0
    torso_vector = mid_shoulder - mid_hip

    dz = torso_vector[2]
    dz_adj = dz
    dy = -torso_vector[1]
    return float(np.degrees(np.arctan2(dz_adj, dy)))

def torso_lateral_tilt(landmarks: List[Any]) -> float:
    """Signed left/right trunk inclination angle in degrees."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    left_hip = _get_xyz(landmarks[23])
    right_hip = _get_xyz(landmarks[24])

    mid_shoulder = (left_shoulder + right_shoulder) / 2.0
    mid_hip = (left_hip + right_hip) / 2.0
    torso_vector = mid_shoulder - mid_hip
    return float(np.degrees(np.arctan2(torso_vector[1], torso_vector[0])))

def torso_rotation(landmarks: List[Any]) -> float:
    """Estimated axial trunk rotation angle in degrees."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    left_hip = _get_xyz(landmarks[23])
    right_hip = _get_xyz(landmarks[24])

    shoulder_axis = right_shoulder[[0, 2]] - left_shoulder[[0, 2]]
    hip_axis = right_hip[[0, 2]] - left_hip[[0, 2]]

    yaw_shoulder = np.degrees(np.arctan2(shoulder_axis[1], shoulder_axis[0]))
    yaw_hip = np.degrees(np.arctan2(hip_axis[1], hip_axis[0]))
    return float(yaw_shoulder - yaw_hip)

def shoulder_asymmetry(landmarks: List[Any]) -> float:
    """Normalized left/right shoulder height imbalance ratio."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    height_diff = abs(left_shoulder[1] - right_shoulder[1])
    shoulder_width = float(np.linalg.norm(right_shoulder - left_shoulder))
    if shoulder_width < 1e-5:
        return 0.0
    return height_diff / shoulder_width

def upper_arm_elevation(landmarks: List[Any]) -> float:
    """Mean upper-arm elevation angle in degrees."""
    left_shoulder = _get_xyz(landmarks[11])
    left_elbow = _get_xyz(landmarks[13])
    right_shoulder = _get_xyz(landmarks[12])
    right_elbow = _get_xyz(landmarks[14])

    vec_l = left_elbow - left_shoulder
    vec_r = right_elbow - right_shoulder

    elev_l = np.degrees(np.arctan2(np.sqrt(vec_l[0]**2 + vec_l[2]**2), -vec_l[1]))
    elev_r = np.degrees(np.arctan2(np.sqrt(vec_r[0]**2 + vec_r[2]**2), -vec_r[1]))
    return float((elev_l + elev_r) / 2.0)

def shoulder_diff(landmarks: List[Any]) -> float:
    """Raw vertical difference between left and right shoulders."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    return float(abs(left_shoulder[1] - right_shoulder[1]))

def shoulder_tilt_angle(landmarks: List[Any]) -> float:
    """Coronal shoulder tilt angle relative to horizontal in degrees."""
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    return float(np.degrees(np.arctan2(right_shoulder[1] - left_shoulder[1], right_shoulder[0] - left_shoulder[0])))

def craniovertebral_angle(landmarks: List[Any]) -> float:
    """Craniovertebral Angle (CVA) in degrees in sagittal plane."""
    left_ear = _get_xyz(landmarks[7])
    right_ear = _get_xyz(landmarks[8])
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    ms = (left_shoulder + right_shoulder) / 2.0
    me = (left_ear + right_ear) / 2.0
    neck_vec = me - ms
    return float(np.degrees(np.arctan2(-neck_vec[1], abs(neck_vec[2]) + 1e-5)))

def neck_lateral_tilt(landmarks: List[Any]) -> float:
    """Lateral neck angle relative to vertical in coronal plane in degrees."""
    left_ear = _get_xyz(landmarks[7])
    right_ear = _get_xyz(landmarks[8])
    left_shoulder = _get_xyz(landmarks[11])
    right_shoulder = _get_xyz(landmarks[12])
    ms = (left_shoulder + right_shoulder) / 2.0
    me = (left_ear + right_ear) / 2.0
    neck_vec = me - ms
    return float(np.degrees(np.arctan2(neck_vec[0], -neck_vec[1] + 1e-5)))

# Core ordered list for production model inference
FEATURE_FUNCS: List[Callable] = [
    head_pitch,
    head_roll,
    forward_head_displacement,
    torso_pitch,
    torso_lateral_tilt,
    torso_rotation,
    shoulder_asymmetry,
    upper_arm_elevation,
]

# Extended list including enhanced head and shoulder features
EXTENDED_FEATURE_FUNCS: List[Callable] = [
    head_pitch,
    head_roll,
    forward_head_displacement,
    craniovertebral_angle,
    neck_lateral_tilt,
    shoulder_diff,
    shoulder_asymmetry,
    shoulder_tilt_angle,
    upper_arm_elevation,
    torso_pitch,
    torso_lateral_tilt,
    torso_rotation,
]


# ---------------------------------------------------------------------------
# Calibration Baseline — collects samples and computes robust neutral
# ---------------------------------------------------------------------------
MIN_CALIBRATION_SAMPLES = 5

class CalibrationBaseline:
    """Collects posture feature samples during calibration and computes
    the user's neutral baseline using robust median statistics."""

    def __init__(self):
        self._samples: List[Dict[str, float]] = []
        self.baseline: Optional[Dict[str, float]] = None
        self.is_calibrated = False

    def reset(self):
        self._samples.clear()
        self.baseline = None
        self.is_calibrated = False

    def add_sample(self, landmarks: List[Any], pose_valid: bool = True) -> bool:
        """Add a calibration sample. Returns True if sample was accepted."""
        if not pose_valid:
            return False
        if not landmarks or len(landmarks) < 25:
            return False

        try:
            hp = head_pitch(landmarks)
            hr = head_roll(landmarks)
            fhd = forward_head_displacement(landmarks)
            tp = torso_pitch(landmarks)
            tlt = torso_lateral_tilt(landmarks)
            sa = shoulder_asymmetry(landmarks)
        except Exception:
            return False

        # Reject if any value is non-finite
        vals = [hp, hr, fhd, tp, tlt, sa]
        if not all(np.isfinite(v) for v in vals):
            return False

        self._samples.append({
            'head_pitch': hp,
            'head_roll': hr,
            'forward_head_displacement': fhd,
            'torso_pitch': tp,
            'torso_lateral_tilt': tlt,
            'shoulder_asymmetry': sa,
        })
        return True

    @property
    def sample_count(self) -> int:
        return len(self._samples)

    @property
    def valid_sample_count(self) -> int:
        return len(self._samples)

    def finalize(self) -> bool:
        """Compute baseline from collected samples. Returns True if successful."""
        if len(self._samples) < MIN_CALIBRATION_SAMPLES:
            return False

        keys = ['head_pitch', 'head_roll', 'forward_head_displacement',
                'torso_pitch', 'torso_lateral_tilt', 'shoulder_asymmetry']
        self.baseline = {}
        for k in keys:
            values = [s[k] for s in self._samples]
            self.baseline[k] = float(np.median(values))

        self.is_calibrated = True
        return True

    def get_debug_info(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            'sample_count': len(self._samples),
            'valid_sample_count': len(self._samples),
            'is_calibrated': self.is_calibrated,
        }
        if self.baseline:
            info['head_pitch_baseline'] = round(self.baseline['head_pitch'], 2)
            info['head_roll_baseline'] = round(self.baseline['head_roll'], 2)
            info['torso_pitch_baseline'] = round(self.baseline['torso_pitch'], 2)
            info['torso_lateral_baseline'] = round(self.baseline['torso_lateral_tilt'], 2)
            info['shoulder_asymmetry_baseline'] = round(self.baseline['shoulder_asymmetry'], 4)
        return info


def _angle_diff(a: float, b: float) -> float:
    """Shortest angular distance between two angles in degrees."""
    return float(abs((a - b + 180.0) % 360.0 - 180.0))


# ---------------------------------------------------------------------------
# Posture Rules — deviation-based when calibrated, absolute fallback otherwise
# ---------------------------------------------------------------------------

# Deviation thresholds (degrees or ratio units deviation from personal baseline)
_HEAD_ROLL_DEV_BAD = 20.0
_HEAD_ROLL_DEV_MODERATE = 7.0
_HEAD_PITCH_DEV_BAD = 25.0
_HEAD_PITCH_DEV_MODERATE = 10.0

_TRUNK_PITCH_DEV_BAD = 25.0
_TRUNK_PITCH_DEV_MODERATE = 10.0
_TRUNK_TILT_DEV_BAD = 20.0
_TRUNK_TILT_DEV_MODERATE = 8.0

_SHOULDER_DEV_BAD = 0.25
_SHOULDER_DEV_MODERATE = 0.10

# Absolute fallback thresholds (no calibration) — centered around nominal webcam geometry
_ABS_HEAD_ROLL_BAD = 22.0
_ABS_HEAD_ROLL_MODERATE = 8.0
_ABS_HEAD_PITCH_BAD = 30.0
_ABS_HEAD_PITCH_MODERATE = 12.0

_ABS_TRUNK_PITCH_BAD = 30.0
_ABS_TRUNK_PITCH_MODERATE = 12.0
_ABS_TRUNK_TILT_BAD = 20.0
_ABS_TRUNK_TILT_MODERATE = 10.0

_ABS_SHOULDER_BAD = 0.30
_ABS_SHOULDER_MODERATE = 0.12


def evaluate_posture_rules(
    landmarks: Optional[List[Any]],
    calibration: Optional[CalibrationBaseline] = None,
) -> dict:
    """Derived alignment evidence for Head, Shoulder, and Trunk alignment.
    Does NOT override ML posture predictions. Uses dataset-aligned baselines.

    When a CalibrationBaseline is provided and calibrated, thresholds are
    applied to the *deviation from the user's personal baseline* rather than
    to absolute values. This prevents false positives when a user's natural
    posture has non-zero head_pitch / head_roll / torso angles.
    """
    if not landmarks or len(landmarks) < 25:
        return {
            "overall_status": "UNKNOWN",
            "head": {"status": "UNKNOWN", "detail": "No landmarks"},
            "shoulder": {"status": "UNKNOWN", "detail": "No landmarks"},
            "trunk": {"status": "UNKNOWN", "detail": "No landmarks"},
        }

    hp = head_pitch(landmarks)
    hr = head_roll(landmarks)
    fhd = forward_head_displacement(landmarks)
    tp = torso_pitch(landmarks)
    tlt = torso_lateral_tilt(landmarks)
    sa = shoulder_asymmetry(landmarks)

    use_calibration = (calibration is not None
                       and calibration.is_calibrated
                       and calibration.baseline is not None)

    # --- Debug data for logging ---
    debug = {}

    if use_calibration:
        bl = calibration.baseline
        hp_dev = _angle_diff(hp, bl['head_pitch'])
        hr_dev = _angle_diff(hr, bl['head_roll'])
        tp_dev = _angle_diff(tp, bl['torso_pitch'])
        tlt_dev = _angle_diff(tlt, bl['torso_lateral_tilt'])
        sa_dev = abs(sa - bl['shoulder_asymmetry'])

        debug = {
            'head_pitch_deviation': round(hp_dev, 2),
            'head_roll_deviation': round(hr_dev, 2),
            'torso_pitch_deviation': round(tp_dev, 2),
            'torso_lateral_deviation': round(tlt_dev, 2),
            'shoulder_deviation': round(sa_dev, 4),
        }

        # 1. Head Posture — deviation from calibrated baseline
        if hr_dev > _HEAD_ROLL_DEV_BAD or hp_dev > _HEAD_PITCH_DEV_BAD:
            head_status = "BAD"
            head_detail = "Head heavily tilted (keep your head straight)"
        elif hr_dev > _HEAD_ROLL_DEV_MODERATE or hp_dev > _HEAD_PITCH_DEV_MODERATE:
            head_status = "MODERATE"
            head_detail = "Slight head tilt"
        else:
            head_status = "GOOD"
            head_detail = "Head straight"

        # 2. Shoulder Posture — deviation from baseline
        if sa_dev > _SHOULDER_DEV_BAD:
            shoulder_status = "BAD"
            shoulder_detail = "Shoulder misaligned (keep shoulders aligned)"
        elif sa_dev > _SHOULDER_DEV_MODERATE:
            shoulder_status = "MODERATE"
            shoulder_detail = "Slight shoulder misalignment"
        else:
            shoulder_status = "GOOD"
            shoulder_detail = "Shoulders aligned"

        # 3. Trunk Posture — deviation from baseline
        if tp_dev > _TRUNK_PITCH_DEV_BAD or tlt_dev > _TRUNK_TILT_DEV_BAD:
            trunk_status = "BAD"
            trunk_detail = "Trunk misaligned (keep trunk straight)"
        elif tp_dev > _TRUNK_PITCH_DEV_MODERATE or tlt_dev > _TRUNK_TILT_DEV_MODERATE:
            trunk_status = "MODERATE"
            trunk_detail = "Slight trunk tilt"
        else:
            trunk_status = "GOOD"
            trunk_detail = "Trunk straight"

    else:
        # Absolute fallback (no calibration) — supports both webcam geometry (-35°/-25°) and 0° synthetic models
        head_roll_dev = min(abs(hr), abs(abs(hr) - 180.0))
        head_pitch_dev = min(_angle_diff(hp, -35.0), _angle_diff(hp, 0.0))
        if head_roll_dev > _ABS_HEAD_ROLL_BAD or head_pitch_dev > _ABS_HEAD_PITCH_BAD:
            head_status = "BAD"
            head_detail = "Head tilt detected (keep your head straight)"
        elif head_roll_dev > _ABS_HEAD_ROLL_MODERATE or head_pitch_dev > _ABS_HEAD_PITCH_MODERATE:
            head_status = "MODERATE"
            head_detail = "Slight head tilt"
        else:
            head_status = "GOOD"
            head_detail = "Head straight"

        if sa > _ABS_SHOULDER_BAD:
            shoulder_status = "BAD"
            shoulder_detail = "Shoulder misaligned (keep shoulders aligned)"
        elif sa > _ABS_SHOULDER_MODERATE:
            shoulder_status = "MODERATE"
            shoulder_detail = "Slight shoulder misalignment"
        else:
            shoulder_status = "GOOD"
            shoulder_detail = "Shoulders aligned"

        trunk_pitch_dev = min(_angle_diff(tp, -25.0), _angle_diff(tp, 0.0))
        trunk_tilt_dev = min(abs(tlt + 90.0), abs(tlt - 90.0))
        if trunk_pitch_dev > _ABS_TRUNK_PITCH_BAD or trunk_tilt_dev > _ABS_TRUNK_TILT_BAD:
            trunk_status = "BAD"
            trunk_detail = "Trunk misaligned (keep trunk straight)"
        elif trunk_pitch_dev > _ABS_TRUNK_PITCH_MODERATE or trunk_tilt_dev > _ABS_TRUNK_TILT_MODERATE:
            trunk_status = "MODERATE"
            trunk_detail = "Slight trunk tilt"
        else:
            trunk_status = "GOOD"
            trunk_detail = "Trunk straight"

    # Combined Evidence Severity (consensus logic to prevent single-sensor jitter false positives)
    statuses = [head_status, shoulder_status, trunk_status]
    bad_count = statuses.count("BAD")
    mod_count = statuses.count("MODERATE")

    if bad_count >= 2 or (bad_count == 1 and mod_count >= 1):
        overall_status = "BAD"
    elif bad_count == 1 or mod_count >= 1:
        overall_status = "MODERATE"
    else:
        overall_status = "GOOD"

    result = {
        "overall_status": overall_status,
        "head": {"status": head_status, "pitch_deg": round(float(hp), 1), "roll_deg": round(float(hr), 1), "detail": head_detail},
        "shoulder": {"status": shoulder_status, "asymmetry_ratio": round(float(sa), 3), "detail": shoulder_detail},
        "trunk": {"status": trunk_status, "pitch_deg": round(float(tp), 1), "detail": trunk_detail},
    }
    if debug:
        result["deviations"] = debug
    return result
