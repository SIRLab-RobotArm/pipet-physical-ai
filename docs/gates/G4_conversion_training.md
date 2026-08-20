# G4 conversion and training gate

The conversion and training contract is RGB-only: one three-channel RGB camera
plus robot state. The RGB-only path must be used for every main dataset and
checkpoint.

## Result

Passed on 2026-08-03 with disposable development data.

- Three usable mock HDF5 episodes were converted through a four-phase split.
  The resulting dataset contained 19 total 20 Hz observation samples arranged
  as twelve 5 Hz LeRobot trajectories, so ACT chunks follow
  `[t, t+4, t+8, ...]` without dropping phase-offset samples.
- A one-raw-episode subset (four derived phases) was materialized with 8
  frames. RGB/state/action content SHA matched the selected source rows and
  subset stats were recomputed.
- Historical conversion identity and action-roundtrip checks passed.
- Active ACT training uses `use_vae=true` and the required normalization map.
- A 5,000-step small-model overfit finished in 37 seconds. Final reported
  training loss was about 0.006. Checkpoint evaluation in physical action
  units gave L1 `0.0028065`, versus copy-state L1 `0.8692309`.

Development HDF5 files are under `episodes/_dev`, derived artifacts under
`datasets/_dev3`, and checkpoints under `ai/models`; all are git-ignored.

The current A~D membership is defined in `docs/experiment_design.md`: A=G5×60,
B=(G1,G6,G8)×20, C=60 across nine positions, and D=20×nine positions. Each
condition uses the same manifest for training seeds 0, 1, and 2.

## LeRobot v3 storage compatibility note

LeRobot 0.5.1 v3 embeds image bytes for multiple episodes in shared parquet
files. A D1/D3 subset therefore cannot hardlink per-episode parquet/PNG files:
selected and unselected rows coexist in one file. The subset tool rewrites
selected rows losslessly, recomputes stats, reloads the result, and asserts a
canonical RGB/state/action content hash. The manifest records this storage
decision explicitly.

The tool accepts raw episode UUIDs and includes all four derived phases for
each selected demonstration. It must consume the frozen A~D manifests rather
than choose a spatial rule implicitly.
