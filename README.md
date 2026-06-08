# SLAM Front-End Robustness Study

This repository contains a course project on visual SLAM front-end robustness under degraded scenes.

## Project Goal

Study whether learned features improve SLAM front-end stability compared with traditional ORB-based features in challenging scenes such as:

- low texture
- motion blur
- illumination changes
- fast camera motion

## Research Question

Can learned features improve tracking stability, trajectory accuracy, and matching reliability in a simplified visual SLAM pipeline?

## Dataset

- TUM RGB-D

## Baseline

- ORB feature extraction
- Frame-to-frame feature matching
- Pose estimation
- Trajectory accumulation

## Planned Comparison

- Traditional feature pipeline
- Learned-feature pipeline

## Metrics

- ATE
- RPE
- Tracking success rate
- Matching count
- Runtime

## Repository Layout

```text
slam/
├── external/   # third-party source code such as ORB-SLAM3
├── data/       # dataset notes and local paths
├── docs/       # notes, figures, and report drafts
├── results/    # experiment outputs and plots
├── scripts/    # runnable experiment scripts
├── src/        # core implementation
├── README.md
├── SCHEDULE.md
└── .gitignore
```

## External Code

The official ORB-SLAM3 source code should live under:

```text
external/ORB_SLAM3/
```

Recommended workflow:

1. Create the `external/` directory if it does not already exist.
2. Clone the official repository into `external/ORB_SLAM3/`.
3. Keep the third-party source code separate from your own implementation in `src/`.
4. Record any local setup notes in `external/README.md` or `docs/`.

Example:

```bash
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git external/ORB_SLAM3
```

## Status

This repo is currently in the initial setup phase.
