# Feature Engineering Report

All features are derived from MediaPipe‑estimated 3‑D landmarks. Angles are reported in degrees. Normalization uses body‑scale torso length where indicated.

## Coordinate convention (MediaPipe)

* **x** – rightward in the image plane
* **y** – upward (negative values correspond to upward direction)
* **z** – forward out of the camera (negative z is forward)

## Features

### head_pitch

* **Purpose**: Signed forward/backward head inclination.

* **Landmarks used**: `nose`, `left_shoulder`, `right_shoulder`.

* **Reference**: Vector from neck midpoint (average of left/right shoulder) to nose.

* **Plane**: Sagittal (Y‑Z).

* **Formula**: `head_pitch = atan2(z, -y)` of the head vector, converted to degrees. Positive values indicate forward tilt (nose moving forward).

* **Unit**: degrees.

* **Missing‑landmark handling**: If any required coordinate is NaN, the feature is set to NaN.

### head_roll

* **Purpose**: Signed left/right lateral head inclination.

* **Landmarks used**: `left_ear`, `right_ear`.

* **Vector**: From left ear to right ear.

* **Plane**: Coronal (X‑Y).

* **Formula**: `head_roll = atan2(y, x)` of the ear vector, in degrees. Positive values indicate head rolled to the right.

* **Unit**: degrees.

* **Missing‑landmark handling**: NaN if ear landmarks missing.

### forward_head_displacement

* **Purpose**: Normalized forward displacement of the head relative to torso.

* **Landmarks used**: `nose`, `left_shoulder`, `right_shoulder`, `left_hip`, `right_hip`.

* **Torso length**: Euclidean distance between shoulder_center and hip_center.

* **Forward axis**: -Z (MediaPipe forward).

* **Formula**: `disp = dot((nose - shoulder_center), forward_axis)`; `forward_head_displacement = disp / torso_length`.

* **Unit**: dimensionless (ratio).

### torso_pitch

* **Purpose**: Signed forward/backward trunk inclination.

* **Landmarks used**: `left_shoulder`, `right_shoulder`, `left_hip`, `right_hip`.

* **Vector**: `torso_vector = shoulder_center - hip_center`.

* **Plane**: Sagittal (Y‑Z).

* **Formula**: `torso_pitch = atan2(z, -y)` of torso_vector, in degrees.

### torso_lateral_tilt

* **Purpose**: Signed left/right trunk inclination.

* **Plane**: Coronal (X‑Y).

* **Formula**: `torso_lateral_tilt = atan2(y, x)` of torso_vector, in degrees.

### torso_rotation

* **Purpose**: Axial trunk rotation estimate.

* **Landmarks used**: `left_shoulder`, `right_shoulder`, `left_hip`, `right_hip`.

* **Shoulder axis**: vector between shoulders (left→right).

* **Hip axis**: vector between hips (left→right).

* **Projection**: Both axes projected onto X‑Z plane.

* **Formula**: `torso_rotation = yaw(shoulder_axis) - yaw(hip_axis)`, where `yaw = atan2(z, x)`. Result in degrees.

### shoulder_asymmetry

* **Purpose**: Normalized left/right shoulder height imbalance.

* **Landmarks used**: `left_shoulder_y`, `right_shoulder_y`, `left_shoulder`, `right_shoulder`.

* **Height difference**: `|left_y - right_y|`.

* **Width**: Euclidean distance between left and right shoulders.

* **Formula**: `shoulder_asymmetry = height_diff / width`.

### upper_arm_elevation

* **Purpose**: Mean elevation angle of both upper arms.

* **Landmarks used**: `left_shoulder`, `left_elbow`, `right_shoulder`, `right_elbow`.

* **Arm vector**: shoulder → elbow.

* **Elevation**: `atan2( sqrt(x²+z²), -y )` (vertical = -Y).

* **Aggregation**: `upper_arm_elevation = mean(left_elev, right_elev)` (ignores missing side).
