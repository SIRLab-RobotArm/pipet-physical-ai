# ROS 2 Jazzy packages

The collection and evaluation graph for Indy7 + Mark7 + a fixed overhead D435,
RGB only.

| Path | Role |
| --- | --- |
| `indy7_ros2/indy_interfaces` | Indy service and message definitions |
| `indy7_ros2/indy_driver` | Indy7 hardware driver |
| `indy7_ros2/indy_description` | Indy7 URDF, xacro and meshes |
| `indy7_teleop` | Xbox Cartesian teleoperation, home and teach-in control |
| `mark7/` | Mark7 messages, hardware driver, description and teleoperation |
| `grip_collect` | Synchronised HDF5 demonstration recorder |
| `grip_eval` | ACT client, policy executor, rollout logger |
| `grip_bringup` | Launch files that compose the collection and evaluation graphs |

`indy7_ros2` and `mark7/pipet_hand_mark7_description` come from third parties;
see [`../../NOTICE.md`](../../NOTICE.md). `indy_description` has been trimmed to
the Indy7 alone - the meshes for the other Neuromeka arms were removed, because
this experiment does not use them and they added 150 MB to every clone.

## Building

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install \
  --packages-select indy_interfaces indy_driver \
  pipet_hand_mark7_msgs pipet_hand_mark7_driver pipet_hand_mark7_teleop \
  indy7_teleop grip_collect grip_eval grip_bringup
source install/setup.bash
```

## Launch files

| Launch file | What it brings up |
| --- | --- |
| `grip_bringup/collect_position.launch.py` | Camera plus recorder, pinned to one grid position |
| `grip_bringup/collect.launch.py` | The full collection graph, with a mock path |
| `grip_bringup/eval.launch.py` | The evaluation graph: arm, hand, camera, policy executor, logger |
| `indy_driver/indy_bringup.launch.py` | The Indy7 driver on its own |
| `pipet_hand_mark7_driver/mark7_hardware.launch.py` | The Mark7 hand on its own |

Robot IP, camera serial and hand serial port default to the values in
`config/local.env` (through `scripts/env.sh`), and can still be overridden per
launch, for example `indy_ip:=192.168.0.42`.

The finished evaluation was run through `./scripts/eval/evaluation_ui.sh`.
Starting individual nodes by hand on top of a running graph will collide over the
camera, `/indy_srv` and the ZMQ endpoint.

The design and results are in
[`../../docs/experiment_design.md`](../../docs/experiment_design.md) and
[`../../experiment/evaluation/main_recollection_20260817/results/README.md`](../../experiment/evaluation/main_recollection_20260817/results/README.md).
