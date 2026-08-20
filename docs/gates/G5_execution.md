# G5 continuous execution gate

## Software gate

The executor implements the fixed contract: one synchronized observation,
one ACT chunk of 40 actions, and execution/replanning in blocks of the first
10 deltas at 5 Hz. Each predicted XYZ delta is integrated into one cumulative
Indy task-relative target. Chunk boundaries do not issue an Indy STOP; task
teleoperation stays active while the next observation-conditioned chunk is
computed. The driver limits each new target increment to an L2 norm of 25 mm,
and rotation is always zero. The gripper uses trial-scoped binary hysteresis
(close above 0.6, open below 0.4) and calls one Trigger only on a transition.
There is no automatic trial timeout. Execution continues until the operator
calls `/grip_eval/stop`, or until a driver/inference fault stops the trial.

The eight archived rollout-tuning knobs are absent. ACT inference runs in the
`act` conda environment through `ai/serve/zmq_act_server.py`; ROS I/O remains in
the Jazzy system environment. The active `grip_act_rgb_v1` protocol sends one
three-channel RGB image and one state vector. The executor does not subscribe
to a Depth topic, the server does not accept a Depth payload, and the model
input has exactly three image channels.

Commit `4837480` preserves the archived loader and ZMQ pair byte-for-byte
before the protocol patch. The archived early-fusion modules remain only for
historical reproducibility and are not imported by the active RGB server. The
active protocol also removes the archived 7-D action assumption.

All 12 A~D/seed models use the same eight evaluation positions: G5, G1, G6,
G8, and Q1~Q4. Each model runs twice per location for 16 rollouts/model and 192
rollouts total. Exact-grid results are primary; Q1~Q4 are secondary within-grid
interpolation results.

The automated dry-run test reconstructs actions directly from raw EEF poses
at 5 Hz and checks byte-exact float32 equality between every unclamped recorded
XYZ action and executor command, plus exact binary gripper state. No action is
read from or written to raw HDF5.

## Raw rollout records

`rollout_logger_node` writes a 20 Hz `trace.parquet`, `events.json`, and
`meta.json`. In real evaluation, `eval.launch.py` also starts a foreground ROS
bag recorder at `rollout.bag`. Metrics are not computed online. Offline
`grasp_errors` interpolates the first close, cuts the trajectory before first
move/close/end, keeps E3 defined when no close occurs, and marks contaminated
E1/E2 trials. The analysis module encodes the preregistered crossed
seed/position random-intercept models and Wilson success intervals.

## Human hardware gate (pending)

### Policy pilot observation (2026-08-20, not the quantitative gate)

Condition A/seed 0의 100k 최종 모델을 P5(`eval_1`)에서 1회 실행했고, 운영자가
PVC에 접근해 파지하고 들어 올리는 데 성공했음을 확인했다. 기록은
`experiment/rollouts/_pilot/a_s0_p5_pilot_01`에 있으며 `success=true`, 4,163 trace
rows, gripper close 1회, `trial_end`와 완결된 rosbag이 있다. 다만 `p_target`과 `d`가
null이고 held-out demonstration trajectory에 대한 RMS 비교가 아니므로 아래 정량
게이트를 통과한 것으로 간주하지 않는다.

With an operator at the E-stop, replay one held-out demonstration through the
same executor and compare `/indy/ee_pose_stamped` against its demonstration
trajectory. Require less than 3 mm RMS EEF error and reproduced gripper
transitions. Record the measured RMS, position ID, raw episode UUID, rollout
ID, and any guard/watchdog event here. G5 is not claimed until a human performs
this test.

Do not create a retroactive `experiment-frozen` tag while preregistration still
contains TBD choices. As of 2026-08-20 all 12 A~D/seed training runs have already
completed, so a new tag cannot be described as a pre-training freeze. Resolve the
remaining choices and record this timing transparently before main evaluation.
