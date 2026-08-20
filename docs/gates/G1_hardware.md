# G1 driver verification

## Mock verification completed

The mock driver publishes `/joint_states`, `/indy/ee_pose`, and the JSON
`/indy/teleop_status` topic without IndyDCP3. The following checks passed:

- a valid 10 mm task-relative command updated the mock EEF pose;
- a 26 mm command was rejected and latched `guard:max_delta`;
- non-zero rotation and out-of-box targets are rejected by unit tests;
- after 0.5 s without a command in task-relative mode, the watchdog called
  `stop_motion()` and latched `watchdog_timeout`;
- an empty `JointTrajectory.points` message returns after stopping, so the
  archived `joint_state_list[0]` IndexError cannot occur;
- mock teach-in wrote a six-value `pilot_1` pose to a disposable copy of
  `experiment/positions.yaml`.

Start the mock driver with:

```bash
source /opt/ros/jazzy/setup.bash
source /opt/workspace/sirlab-paper-indy7-grip/ros2_ws/install/setup.bash
ros2 run indy_driver indy_driver.py --mock
```

## Human hardware gate (pending)

Real task-relative commands are fail-closed until
`workspace_configured:=true` is supplied. Before enabling it, measure the
actual Indy-base-frame bounds and set `workspace_min_mm` / `workspace_max_mm`.
The z bounds must implement `table + 15 mm` through `table + 250 mm`; no
untaught absolute table coordinate is embedded in source code.

With an operator at the E-stop:

1. Send a 10 mm square through `/indy/teleop_pose` and record
   `/indy/ee_pose`; require RMS error below 1 mm and settling below 0.3 s.
2. Command an out-of-box target; require a latched `guard:workspace` status
   and no motion.
3. Stop the command publisher while in `MSG_TELE_TASK_RLT`; require
   `watchdog_timeout` within 0.5 s and stopped motion.
4. Teach and confirm reachability of all nine grid and eight evaluation
   positions using `teach_target_node`.

Record measured values here before G1 is marked passed. Hardware G1 remains a
human gate and is not claimed by the mock result.
