# Indy7 + Mark7 Xbox 텔레옵 alias 설정

## 1. 개요

Indy7, Mark7, 그리퍼 서비스, Xbox 텔레옵을 각각 별도 터미널에서 간단히
실행하기 위해 Bash alias 4개를 등록했다.

이 alias 문서는 수동 조작 확인용이다. 본 RGB-only 실험은
`docs/experiment_design.md`의 G1~G9 220개 수집과 8곳 평가 설계를 따른다. 현재
Xbox 자동 schedule은 G1~G9 각 20개인 기본 180개까지만 지원하며, G5 추가 40개용
schedule과 software workspace가 구현·검증되기 전에는 본 수집에 사용하지 않는다.

| Alias | 역할 |
|---|---|
| `grip_indy` | Indy7 ROS 드라이버 실행 |
| `grip_mark7` | Mark7 하드웨어 및 ros2_control 실행 |
| `grip_gripper` | Mark7 open/grasp preset 서비스 실행 |
| `grip_xbox` | Xbox 컨트롤러 텔레옵 노드 실행 |

alias는 다음 파일에 저장되어 있다.

```text
/home/sirlab/.bash_aliases
```

`/home/sirlab/.bashrc`가 이 파일을 자동으로 불러오므로 새 터미널에서는 별도
설정 없이 사용할 수 있다. 이미 열려 있는 터미널에는 다음 명령으로 즉시
반영한다.

```bash
source ~/.bash_aliases
```

## 2. 실행 순서

터미널 4개를 열고 다음 순서대로 하나씩 실행한다. 각 프로세스는 해당
터미널의 전경에서 계속 실행되어야 한다.

### 터미널 1: Indy7

```bash
grip_indy
```

다음 내용을 확인한다.

```text
Indy connector has been initialised.
ROBOT IP: 192.168.1.10
ROBOT TYPE: indy7
```

### 터미널 2: Mark7

```bash
grip_mark7
```

Mark7 시리얼 포트가 열리고 controller가 활성화됐는지 확인한다.

### 터미널 3: 그리퍼 서비스

```bash
grip_gripper
```

다음 로그가 나오면 준비된 상태다.

```text
Grip preset node ready
```

### 터미널 4: Xbox

```bash
grip_xbox
```

다음 로그가 나온 뒤 조작한다.

```text
indy_srv connected
```

## 3. 실제 alias 정의

현재 `/home/sirlab/.bash_aliases`에는 다음과 같이 등록되어 있다.

```bash
# Indy7 + Mark7 Xbox teleoperation
alias grip_indy='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run indy_driver indy_driver.py --ros-args -p indy_ip:=192.168.1.10 -p indy_type:=indy7 -p enforce_workspace:=false -p vel_ratio:=0.8 -p acc_ratio:=7.0'

alias grip_mark7='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 launch pipet_hand_mark7_driver mark7_hardware.launch.py port:=/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00 use_mock_hardware:=false use_rviz:=false'

alias grip_gripper='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run pipet_hand_mark7_teleop grip_preset_node --ros-args --params-file /opt/workspace/sirlab-paper-indy7-grip/ros2_ws/src/mark7/pipet_hand_mark7_driver/config/grip_presets.yaml'

alias grip_xbox='cd /opt/workspace/sirlab-paper-indy7-grip && source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && export PYTHONPATH=/opt/workspace/yuykim/ros_pydeps:${PYTHONPATH:-} && export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 run indy7_teleop xbox_servo_node --ros-args -p indy_ip:=192.168.1.10 -p input_backend:=linuxevdev -p event_device:=/dev/input/by-id/usb-Microsoft_Controller_3039373130333239373237343238-event-joystick -p linear_step_mm:=0.5 -p debug_input:=true'
```

## 4. 주요 설정값

### ROS 발견 범위

모든 alias가 다음 값을 사용한다.

```bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
```

여러 네트워크 인터페이스 때문에 같은 PC의 ROS 노드들이 서로 발견되지 않던
문제를 방지한다. 네 alias 중 하나라도 다른 발견 범위로 실행하면 서비스나
토픽을 찾지 못할 수 있다.

### Indy7

- 로봇 IP: `192.168.1.10`
- 작업공간 경계 검사: `enforce_workspace=false`
- 속도 비율: `0.8`
- 가속도 비율: `7.0`
- 회전 명령 차단과 통신 watchdog은 유지된다.

작업공간 경계가 비활성화되어 있으므로 컨트롤러를 계속 누르면 누적 이동한다.
로봇 주변을 비우고 비상정지를 바로 사용할 수 있는 상태에서 조작한다.
이 alias는 workspace 측정 전 저속 점검용이며 본 데이터 수집용이 아니다. 본 수집은
측정된 `workspace_min_mm`/`workspace_max_mm`와 `workspace_configured=true`가
적용된 launch만 사용한다.

### Mark7

Mark7 Arduino Micro의 고정 장치 경로를 사용한다.

```text
/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00
```

`/dev/ttyACM0`보다 `by-id` 경로가 재연결 후에도 안정적이다.

### Xbox

Xbox 컨트롤러의 고정 장치 경로를 사용한다.

```text
/dev/input/by-id/usb-Microsoft_Controller_3039373130333239373237343238-event-joystick
```

기본 누적 이동 step은 `0.5 mm`이며 `debug_input=true`로 입력 상태를 출력한다.

## 5. alias 확인 및 종료

등록 상태 확인:

```bash
type grip_indy
type grip_mark7
type grip_gripper
type grip_xbox
```

실행 중인 각 프로세스는 해당 터미널에서 `Ctrl+C`로 종료한다. 동일 노드를
중복 실행하지 않는다.

실행 상태 확인:

```bash
ps aux | grep -E 'indy_driver.py|ros2_control_node|grip_preset_node|xbox_servo_node' | grep -v grep
```

## 6. 컨트롤러 조작

| 입력 | 동작 |
|---|---|
| D-pad | X/Y 연속 이동 |
| LT / RT | Z 하강/상승 |
| A | 그리퍼 닫기 |
| B | 그리퍼 열기 |
| BACK | 텔레옵 정지 |
| BACK + A | Indy fault 복구 |
| BACK + B | zero 위치 이동 |
| BACK + Y | home 위치 이동 |
| BACK + LB / RB | 이동 step 감소/증가 |
| MODE | EEF teach-in 진입/종료 |

## 7. 13개 위치 EEF teach-in

Teach-in 모드는 `grid_1~grid_9`와 `eval_5~eval_8`을 위치당 3회 저장한다.
`eval_1~eval_4`는 `grid_5/1/6/8`에서 자동 생성된다. 저장값은 Indy base 기준
EEF pose와 같은 시점의 6축 관절각이다.

MODE를 눌러 진입한 뒤 각 샘플마다 다음 순서를 지킨다.

```text
B open → BACK+Y HOME → PVC 다시 세우기 → 접근 → A close → 육안 확인 → X save
```

같은 위치에서 이 사이클을 HOME부터 3회 반복한다. 첫 샘플을 저장한 뒤 그리퍼를
열지 않으면 다음 저장은 거부된다.

| teach-in 입력 | 동작 |
|---|---|
| `X` | 현재 EEF pose와 관절각 저장 |
| `Y` | 현재 위치의 직전 샘플 취소 |
| `LB` / `RB` | 이전 / 다음 위치 |
| `A` / `B` | 그리퍼 닫기 / 열기 |
| `BACK+Y` | HOME 이동 |
| `MODE` | teach-in 종료 |
| `START` | 차단됨 |

화면에서 `samples 3/3`, 최종적으로 `completed 13/13`을 확인한다. 저장 파일은
`experiment/positions.yaml`이다. MODE 버튼이 입력되지 않으면 `debug_input=true`
출력에서 버튼 8을 확인하고, 해당 패드가 MODE를 전달하지 않는 경우 Xbox 실행
파라미터 `teach_toggle_button:=10`으로 오른쪽 스틱 클릭을 사용할 수 있다.

Indy 드라이버를 재시작했다면 Xbox 노드도 재시작한다. 두 노드의 텔레옵 상태가
어긋나면 `Ignoring /indy/teleop_pose because task-relative teleop is not active`
경고가 반복될 수 있다.
