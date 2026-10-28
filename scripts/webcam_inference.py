# scripts/webcam_inference.py
"""Real‑time PostureAI inference using webcam.

- Captures frames with OpenCV.
- Uses MediaPipe Pose to obtain 33 3‑D landmarks.
- Computes the eight engineered features defined in the dataset spec.
- Loads the viewpoint‑robust RandomForest model (trained in Phase 2).
- Displays the predicted posture label on the video feed.

Run:
    python scripts/webcam_inference.py
"""

import cv2
import numpy as np
import joblib
from pathlib import Path
import mediapipe as mp

from ml.inference.feature_extractor import FEATURE_FUNCS

MODEL_PATH = Path("models/viewpoint_robust_model.joblib")
model = joblib.load(MODEL_PATH)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False,
                    model_complexity=1,
                    enable_segmentation=False,
                    min_detection_confidence=0.5)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Webcam not accessible")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)
    label = "No Pose"
    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        try:
            feats = [fn(lm) for fn in FEATURE_FUNCS]
            pred = model.predict(np.array(feats).reshape(1, -1))[0]
            label = pred
        except Exception as e:
            label = f"Err:{type(e).__name__}"
    cv2.putText(frame, f"Posture: {label}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow("PostureAI – Real‑time", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
pose.close()
