# ml/inference/viewpoint_estimator.py
"""Viewpoint estimation based on 3D landmark skeletal geometry."""

import numpy as np
from typing import List, Any, Optional

def estimate_viewpoint(landmarks: List[Any]) -> str:
    """Estimate camera viewpoint relative to user from 3D landmarks.

    Returns one of:
      - 'FRONT'
      - 'LEFT_3_4'
      - 'RIGHT_3_4'
      - 'LEFT_PROFILE'
      - 'RIGHT_PROFILE'
      - 'UNKNOWN'
    """
    if not landmarks or len(landmarks) < 33:
        return "UNKNOWN"

    try:
        left_shoulder = np.array([landmarks[11].x, landmarks[11].y, landmarks[11].z])
        right_shoulder = np.array([landmarks[12].x, landmarks[12].y, landmarks[12].z])

        # Lateral shoulder width in x-axis
        w_x = abs(right_shoulder[0] - left_shoulder[0])
        # Depth difference in z-axis
        dz = right_shoulder[2] - left_shoulder[2]

        if w_x < 1e-4:
            return "UNKNOWN"

        # Yaw angle approximation in degrees
        yaw_angle = np.degrees(np.arctan2(dz, w_x))

        if abs(yaw_angle) < 15.0:
            return "FRONT"
        elif 15.0 <= yaw_angle < 45.0:
            return "LEFT_3_4"
        elif -45.0 < yaw_angle <= -15.0:
            return "RIGHT_3_4"
        elif yaw_angle >= 45.0:
            return "LEFT_PROFILE"
        elif yaw_angle <= -45.0:
            return "RIGHT_PROFILE"
        else:
            return "UNKNOWN"
    except Exception:
        return "UNKNOWN"
