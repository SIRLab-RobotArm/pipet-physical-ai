# G2 RGB camera / G3 collection gate

The main experiment is RGB-only. Depth streaming, alignment, depth QA, and
RGB-D training are out of scope. Both the real and mock recorder operate
without a depth topic.

## Implemented collection contract

- One fixed overhead D435 RGB stream at 640x480x30.
- RGB/joint/EEF header synchronization uses `slop=0.03` seconds.
- The driver publishes stamped EEF poses on `/indy/ee_pose_stamped`; the
  legacy `/indy/ee_pose` topic remains available.
- RGB exposure, gain, and white balance are explicit in
  `camera_rgb_only.yaml` and must be confirmed by readback.
- The camera must be physically mounted at a 15--20 degree tilt before G2.
- Real collection starts `ros2 bag record -a`; set `record_bag:=false` only
  for a deliberate diagnostic run.
- Episodes are incrementally appended as chunked HDF5. RGB uses LZF.
  Raw action is never stored.
- Development episodes are accepted only below an `_dev` directory and carry
  `data_block=dev`.

## Mock verification (2026-08-03)

```bash
cd /opt/workspace/sirlab-paper-indy7-grip/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export PYTHONPATH=/opt/workspace/yuykim/ros_pydeps:${PYTHONPATH:-}
ros2 run grip_collect episode_recorder_node \
  --mock --frames 12 \
  --output-dir /opt/workspace/sirlab-paper-indy7-grip/episodes/_dev
ros2 launch grip_bringup collect.launch.py \
  mock:=true \
  output_dir:=/opt/workspace/sirlab-paper-indy7-grip/episodes/_dev
ros2 run indy7_teleop xbox_servo_node --mock
```

Observed historically: all five Phase 3 packages built, the integrated launch
started the mock Indy driver and recorder and shut down cleanly, and Xbox mock
started without `pygame` or a controller. The active recorder contract is now
RGB-only and should be checked again as part of the pre-collection pilot.

## Human RGB G2 procedure (pending)

1. Keep the fixed camera/table geometry and place the final bare PVC cylinder
   at all 15 distinct physical locations from `docs/experiment_design.md`.
2. Confirm configured RGB parameters by readback. The saved episode
   must have `camera_readback_verified=true`; do not accept configured values
   as proof of readback.
3. Record a stationary 60-second episode.
4. Measure effective RGB frame rate and RGB/robot-state timestamp jitter.
5. Confirm that the PVC contour/top opening remains visible and that robot-arm
   occlusion is acceptable at every grid, Q, and pilot location.

Final numerical timestamp and frame-rate tolerances remain to be frozen in the
preregistration. G2 remains pending until a human runs this procedure with the
real RGB stream and object.

G3 is prepared but its complete three-episode HDF5-to-dataset chain belongs
to Phase 4.
