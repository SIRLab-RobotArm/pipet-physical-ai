# ICRiTA Indy7 RGB-only grip experiment preregistration draft

Status: **not frozen and not registered**. Complete every `TBD` item, register
externally, then create the `experiment-frozen` git tag before main collection.

## Confirmatory hypotheses and design

- H1: with 60 demonstrations fixed, broader XY coverage improves task success
  and reduces approach failures (`C > B > A`).
- H2: with all nine locations fixed, increasing demonstrations from 60 to 180
  improves success, with possible saturation (`D > C`).
- H3: distribution primarily changes approach/alignment failures, while purely
  mechanical slip failures may remain.
- Input is RGB-only. Depth collection, RGB-D training, and claims about depth
  are outside the experiment scope.
- Main collection contains 220 usable demonstrations: 20 at each of nine grid
  positions and 40 additional demonstrations at G5, for 60 total at G5.
- Collection has a balanced 20-round nine-grid stage (180) plus 40 additional
  G5 trials distributed across sessions rather than collected as one block.
- Conditions: A=G5×60; B=(G1,G6,G8)×20; C=60 across all nine positions with
  rows `(7,6,7)`; D=all nine positions×20=180.
- Seeds 0, 1, 2 use the same immutable subset manifest within each condition.
- The exact geometry and full mapping are defined in
  `docs/experiment_design.md`.

## Frozen representation and training contract

- Observation rate 20 Hz. Four phase-split 5 Hz trajectories preserve every
  20 Hz observation while ACT chunks advance by 200 ms.
- Action: `[dx_mm, dy_mm, dz_mm, gripper]`, where XYZ is
  `ee_pose[t+4]-ee_pose[t]`; rotation is excluded and gripper is binary.
- State: EEF XYZ, six joint positions in radians, and binary gripper (10-D).
- RGB is area-resized to 240x320. No sensor depth is collected or used.
- Normalization: VISUAL IDENTITY, STATE MEAN_STD, ACTION QUANTILE10.
- ACT: ResNet18 ImageNet, CVAE enabled, chunk 40, execution 10, batch 64,
  AdamW wd 1e-4, gradient clip 10, peak LR 1e-4, 2k warmup, cosine to 1e-6,
  100k fixed steps, checkpoints every 20k steps, no resume. The 100k final
  checkpoint is used for the preregistered evaluation.

## Blind exclusions and gates

- Run QA once before condition injection. Any excluded raw episode is excluded
  from both visual conditions.
- Exclude corrupted/incomplete files, synchronization jitter above the frozen
  RGB/robot-state threshold (currently dev default 15 ms; final value TBD),
  and safety-stop trials. Reasons are retained.
- G1, RGB camera G2, G5, and G6 must pass before main collection/training.
- G2 verifies RGB frame rate, fixed exposure/gain/white balance, PVC visibility,
  and robot occlusion at all 15 distinct physical locations.
- Main collection is invalid if camera geometry/settings, timestamp semantics,
  EEF meaning, gripper definition, task object, or success rule changes within
  the block.

## Outcomes and analysis

- All 12 models are evaluated at the same eight locations: G5, G1, G6, G8 and
  the four within-grid cell centers Q1~Q4, with two rollouts per location.
  This gives 16 rollouts/model and 192 total rollouts.
- Primary rollout outcomes: success and endpoint errors E1/E2/E3; exact
  tolerances, lift height, and hold duration are TBD before freezing. There is
  no automatic software timeout; the operator explicitly ends each rollout
  through `/grip_eval/stop` after the outcome is determined.
- Primary reporting uses the four exact grid evaluation positions. Q1~Q4 are
  a secondary local-interpolation analysis, not an extrapolation claim.
- Fit `condition * d + (1|seed) + (1|position)` to success and each
  continuous error; E1/E2 primary analysis is restricted to clean trials and
  E3 remains defined from the pre-stop trajectory even when no close occurs.
- Report all safety stops, E1/E2 missingness by condition,
  condition-blinded randomized rollout order, and Cohen's kappa on a random
  20% independently rescored video sample.
