# PostureAI Enriched Dataset Report

## Overview
- **Total Samples:** 4794
- **Total Features & Metadata:** 20
- **Subjects:** [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
- **Primary Target 1 (Posture Class):** TUP, TLB, TLF, TLR, TLL
- **Primary Target 2 (Ergonomic Risk):** GOOD, MODERATE, BAD

## Posture Class Distribution
| Posture Class | Count | Percentage |
|---|---|---|
| TLF | 1897 | 39.6% |
| TUP | 1615 | 33.7% |
| TLB | 442 | 9.2% |
| TLL | 420 | 8.8% |
| TLR | 420 | 8.8% |

## Ergonomic Risk Level Distribution
| Risk Level | Count | Percentage |
|---|---|---|
| MODERATE | 1997 | 41.7% |
| BAD | 1462 | 30.5% |
| GOOD | 1335 | 27.8% |

## Posture Class vs. Risk Level Mapping
| upperbody_label   |   BAD |   GOOD |   MODERATE |
|:------------------|------:|-------:|-----------:|
| TLB               |    49 |      0 |        393 |
| TLF               |   716 |      0 |       1181 |
| TLL               |   375 |      0 |         45 |
| TLR               |   322 |      0 |         98 |
| TUP               |     0 |   1335 |        280 |

## Feature Summary Statistics
|                           |         mean |        std |            min |          50% |        max |
|:--------------------------|-------------:|-----------:|---------------:|-------------:|-----------:|
| subject                   |    6.05131   |  3.68829   |    1           |    6         |  13        |
| head_pitch                |  -75.3663    | 11.7016    | -159.923       |  -73.036     | -39.3382   |
| head_roll                 |  141.456     | 77.1323    | -179.997       |  161.59      | 179.738    |
| forward_head_displacement |    0.64427   |  0.0865181 |    0.234109    |    0.636894  |   1.13867  |
| forward_head_distance     |    0.27356   |  0.0303185 |    0.0693617   |    0.27321   |   0.396774 |
| craniovertebral_angle     |   27.1463    | 13.4298    |  -50.3452      |   29.1813    |  68.9478   |
| neck_lateral_tilt         |  -13.7041    | 38.3848    | -179.99        |   -7.22289   | 178.886    |
| neck_deviation            |   63.1168    | 13.2761    |   21.0488      |   61.0005    | 140.285    |
| shoulder_diff             |    0.05965   |  0.0323467 |    3.65525e-05 |    0.053611  |   0.203353 |
| shoulder_asymmetry        |    0.184281  |  0.111942  |    0.000122798 |    0.160429  |   0.708049 |
| shoulder_tilt_angle       | -139.645     | 95.6497    | -179.993       | -170.22      | 179.904    |
| shoulder_protraction_asym |    0.0503022 |  0.0217827 |    7.15405e-05 |    0.0500933 |   0.159    |
| upper_arm_elevation       |  157.112     | 14.4379    |   93.0528      |  159.866     | 178.574    |
| torso_pitch               |  -10.8541    | 21.1125    | -122.605       |   -9.05812   |  40.1812   |
| torso_lateral_tilt        |  -86.4826    | 17.2804    | -179.283       |  -87.0881    |  96.5396   |
| torso_rotation            |  319.518     | 73.3672    |  -37.2413      |  335.782     | 351.415    |
| spine_lateral_deviation   |    9.01181   | 12.9571    |    0.00135121  |    3.6752    |  89.2832   |
