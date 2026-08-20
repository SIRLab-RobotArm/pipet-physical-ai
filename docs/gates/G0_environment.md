# G0 environment verification

Verified on 2026-08-03 (Asia/Seoul) before hardware connection.

## Selected environment

- Conda prefix: `/opt/workspace/yuykim/miniconda3`
- Environment: `act`
- Python: 3.12.13
- LeRobot: 0.5.1, editable from `ai/lerobot_source/lerobot`
- PyTorch: 2.10.0+cu130
- CUDA runtime bundled with PyTorch: 13.0
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Driver: 595.71.05
- NumPy: 2.2.6 (required by LeRobot 0.5.1)

The CUDA smoke test allocated a tensor on the GPU and completed a matrix
multiplication. `torch.cuda.is_available()` returned true.

## ROS and ABI decision

The ROS 2 Jazzy system Python packages provide working `rclpy` and
`cv_bridge` with the system NumPy 1.26.4. In the LeRobot environment,
`rclpy` imports, but loading `cv_bridge` emits the NumPy ABI diagnostic that
the extension was compiled against NumPy 1.x and must not run with NumPy
2.2.6.

Decision: use the preregistered ZMQ sidecar boundary. ROS image conversion and
robot I/O run in the Jazzy process with system NumPy; LeRobot inference runs in
the `act` environment. The two processes exchange RGB/state observations and
actions through `grip_eval/act_client.py` and `ai/serve/zmq_act_server.py`
using the RGB-only protocol. Do not import `cv_bridge` in the LeRobot process.

## Build result

`colcon build --symlink-install` completed all eight baseline packages. The
only stderr was an existing Mark7 hardware-interface deprecation warning; no
package failed.

## Recheck commands

```bash
source /opt/ros/jazzy/setup.bash
conda run -p /opt/workspace/yuykim/miniconda3/envs/act python -c \
  "import torch, lerobot, rclpy, zmq; print(torch.cuda.get_device_name(0))"

cd /opt/workspace/sirlab-paper-indy7-grip/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```
