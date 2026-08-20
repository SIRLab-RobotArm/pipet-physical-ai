# Indy7 RGB-only grasp data collection

Indy7, Mark7 그리퍼, 고정 overhead RealSense RGB 카메라를 이용해 PVC 파지·들어올림
시연을 수집하고 ACT를 학습·평가하는 저장소다. 본 실험은 Depth를 사용하지 않는다.

> **현재 진행 상태:** 새 재수집 데이터 220개, LeRobot 변환, A~D×3 seeds의 ACT
> 본 학습 12개가 완료되었고 실로봇 파일럿 1회가 성공했다. 본 평가를 시작하기 전에
> 남은 작업과 정확한 산출물 경로는 [프로젝트 인수인계](docs/HANDOFF.md)를 먼저 읽는다.
> 아래 수집 명령의 기본 `episodes/main` 경로는 과거 운영 설명이며 완료된 재수집본은
> `episodes/main_recollection_20260817`에 보존되어 있다.

## 빌드

```bash
cd /opt/workspace/sirlab-paper-indy7-grip/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 실행 alias

다음 alias는 `/home/sirlab/.bash_aliases`에 등록되어 있다. 새 터미널에서 alias가
보이지 않으면 `source ~/.bashrc`를 한 번 실행한다.

```bash
alias grip_indy='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run indy_driver indy_driver.py --ros-args -p indy_ip:=192.168.1.10 -p indy_type:=indy7 -p enforce_workspace:=false -p vel_ratio:=0.8 -p acc_ratio:=7.0'

alias grip_mark7='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 launch pipet_hand_mark7_driver mark7_hardware.launch.py port:=/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00 use_mock_hardware:=false use_rviz:=false'

alias grip_gripper='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run pipet_hand_mark7_teleop grip_preset_node --ros-args --params-file /opt/workspace/sirlab-paper-indy7-grip/ros2_ws/src/mark7/pipet_hand_mark7_driver/config/grip_presets.yaml'

alias grip_xbox='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export PYTHONPATH=/opt/workspace/yuykim/ros_pydeps:${PYTHONPATH:-} && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run indy7_teleop xbox_servo_node --ros-args -p indy_ip:=192.168.1.10 -p input_backend:=linuxevdev -p event_device:=/dev/input/by-id/usb-Microsoft_Controller_3039373130333239373237343238-event-joystick -p linear_step_mm:=0.5 -p debug_input:=true'
```

실기 수집은 각 명령을 서로 다른 터미널에서 다음 순서로 실행한다.

```bash
grip_indy
grip_mark7
grip_gripper
grip_xbox
```

## P1~P9 데이터 수집

RealSense Viewer는 카메라를 점유하므로 먼저 닫는다. 수집 세션마다 환경변수를 지정하고
실제 PVC 위치와 같은 스크립트 하나만 실행한다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
export GRIP_SESSION_ID=main_20260810
export GRIP_OPERATOR_ID=sirlab

./scripts/collection/collect_p1.sh  # grid_1 -> episodes/main/p1
./scripts/collection/collect_p2.sh  # grid_2 -> episodes/main/p2
./scripts/collection/collect_p3.sh  # grid_3 -> episodes/main/p3
./scripts/collection/collect_p4.sh  # grid_4 -> episodes/main/p4
./scripts/collection/collect_p5.sh  # grid_5 -> episodes/main/p5
./scripts/collection/collect_p6.sh  # grid_6 -> episodes/main/p6
./scripts/collection/collect_p7.sh  # grid_7 -> episodes/main/p7
./scripts/collection/collect_p8.sh  # grid_8 -> episodes/main/p8
./scripts/collection/collect_p9.sh  # grid_9 -> episodes/main/p9
```

한 번에 한 위치의 수집 스크립트만 실행한다. 스크립트를 실행하면 RGB 미리보기 창이
자동으로 열린다. 미리보기 없이 실행해야 할 때만 직접 launch하며
`show_camera:=false`를 지정한다.

### 한 episode 수집 순서

1. PVC를 해당 위치에 세우고 그리퍼를 연다.
2. Xbox `START`로 기록을 시작한다.
3. D-pad와 LT/RT로 접근하고 `A`로 그리퍼를 닫는다.
4. PVC를 들어 올린 뒤 `START`를 다시 누른다.
5. `A=success`, `B=fail`, `X=discard` 중 하나를 선택한다.

두 번째 `START` 시점에 프레임 추가가 멈추므로 라벨 선택 중 정지 화면은 episode에
들어가지 않는다. HDF5를 닫은 뒤 Indy task teleop이 정지한다.

## 저장 데이터

각 시연은 `episodes/main/pN/episode_<UUID>.h5`로 저장된다. 영상은 별도 MP4가
아니라 HDF5의 `/obs/rgb`에 `uint8 [T,480,640,3]`으로 들어 있다.

- `/obs/rgb`: overhead RGB
- `/state/ee_pose`: Indy base 기준 EEF pose
- `/state/joint_pos`: 6축 관절각 rad
- `/state/gripper_cmd`: `0=open`, `1=closed`
- `/time/stamp_*`: RGB, joint, EEF, recorder timestamp

ACT observation state는 EEF XYZ, 6축 관절각, 그리퍼 상태의 10차원이다. 학습 action은
5 Hz에서 미래 EEF 이동량과 같은 목표 시점의 그리퍼 명령으로 변환한다.

최근 저장 파일은 다음 명령으로 확인한다.

```bash
find episodes/main -mindepth 2 -maxdepth 2 -name '*.h5' \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort
```

세부 운영 절차와 QA 기준은 [데이터 수집 가이드](docs/data_collection_guide.md),
실험 위치·수집량은 [실험 설계](docs/experiment_design.md)를 따른다.
