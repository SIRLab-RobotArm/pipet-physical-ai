# Training configuration matrix (not frozen)

The experiment has 12 RGB-only models: `condition={a,b,c,d}` crossed with
`seed={0,1,2}`.

Condition membership and counts are defined in `docs/experiment_design.md`:
A=G5×60, B=(G1,G6,G8)×20, C=60 distributed across G1~G9, and
D=G1~G9×20=180. Materialization must record exact UUID membership in an
immutable subset manifest. All three training seeds use the same manifest for
a condition.

All main models use one three-channel RGB observation only. The A--D
configuration files contain no additional sensor channel.

Every main run uses 100,000 optimization steps and saves a checkpoint every
20,000 steps. Evaluation uses the final 100,000-step checkpoint. Interrupted
runs are not resumed.
