# Indy7 그립 데이터 수집 사용 안내

이 문서는 ICRiTA 실험용 시연 데이터를 수집하는 운영 절차를 설명한다.
관측은 D435의 RGB만 사용한다. 원시 데이터는 20 Hz HDF5로 기록하며, `action`은
저장하지 않는다. 학습용 5 Hz
delta EEF action은 변환할 때 `ee_pose[t+4] - ee_pose[t]`로 계산하고, 그리퍼
action은 같은 목표 시점의 `gripper_cmd[t+4]`를 사용한다.

> **2026-08-20 상태:** 새 재수집본 220개와 변환·12개 본 학습이 완료되었다.
> 특별히 재수집을 결정한 경우가 아니라면 이 절차로 데이터를 더 모으지 말고,
> [프로젝트 인수인계](HANDOFF.md)의 완료 내역과 본 평가 전 남은 작업부터 확인한다.
> 이 문서의 일부 “준비 상태” 체크리스트는 수집 전 계획을 보존한 기록이다.

위치별 수집량, A~D 조건과 평가 위치의 단일 기준은
`docs/experiment_design.md`이다.

## 1. 현재 준비 상태와 제한

Mock 수집은 바로 사용할 수 있다. 실제 로봇으로 본 데이터를 수집하기 전에는 다음
사항을 먼저 해결해야 한다.

1. G1 로봇 안전 게이트를 사람이 수행한다.
2. G2 RGB 카메라 게이트를 실제 D435와 PVC 원통으로 수행한다.
3. 실제 Indy base 좌표계의 workspace 경계를 측정한다.
4. 19개 position ID(서로 다른 물리 위치 15곳)를 teach-in하거나 동일 좌표로
   매핑해 `experiment/positions.yaml`에 저장한다.
5. 사전등록 문서의 TBD 항목을 확정한다.

통합 `collect.launch.py`에는 다음 실제 수집 배선이 아직 없다.

- `workspace_configured`, 실제 `workspace_min_mm`, `workspace_max_mm`를 포함된 Indy
  드라이버에 전달하지 않는다. 따라서 실제 로봇의 상대 이동 명령은 fail-closed로
  거부된다.
- `session_id`와 `operator_id`가 launch 인자로 노출되지 않았다.
- Xbox teleop 노드는 `collect.launch.py`와 별도로 실행해야 한다.
- Xbox schedule은 현재 grid 9곳×20 round=180개만 만든다. G5 추가 40개용
  schedule과 중단/재개 처리를 구현해야 한다.

본 수집에는 통합 launch 대신 위치가 고정된 `scripts/collection/collect_p*.sh`를
사용한다. 이 경로는 RGB-only recorder를 사용하고 Xbox의 랜덤 context 갱신을
무시한다. workspace 안전 게이트와 실제 카메라 게이트는 별도로 통과해야 한다.

## 2. 공통 터미널 설정

새 터미널마다 다음을 실행한다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH=/opt/workspace/yuykim/ros_pydeps:${PYTHONPATH:-}
```

코드를 변경한 뒤에는 다시 빌드한다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

`sudo`나 시스템 패키지 설치는 이 절차에 필요하지 않다. Mark7 또는 Xbox 장치에
권한 오류가 발생하면 임시 권한 우회를 하지 말고 장치 경로와 현재 사용자 그룹을
확인한 뒤 관리자 조치를 요청한다.

## 3. Mock 수집

Mock과 실기 수집 모두 RGB-only 계약을 사용한다. HDF5에는 RGB 영상과 로봇 상태를
저장하며 Depth 영상이나 Depth 토픽은 요구하지 않는다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH=/opt/workspace/yuykim/ros_pydeps:${PYTHONPATH:-}

ros2 run grip_collect episode_recorder_node \
  --mock \
  --frames 100 \
  --output-dir /opt/workspace/sirlab-paper-indy7-grip/episodes/_dev
```

완료되면 `episodes/_dev/episode_<UUID>.h5`가 생성된다. Mock 및 폐기용 실기
데이터는 항상 `episodes/_dev/`에 둔다.

통합 launch가 기동되는지만 확인하려면 다음 명령을 사용한다. 이 모드는 합성 프레임을
자동으로 완결해 저장하는 one-shot 명령이 아니라, mock 노드들의 연결을 점검하는
용도다.

```bash
ros2 launch grip_bringup collect.launch.py \
  mock:=true \
  output_dir:=/opt/workspace/sirlab-paper-indy7-grip/episodes/_dev \
  data_block:=dev \
  record_bag:=false
```

## 4. 실제 장비 사전 확인

로봇을 움직이기 전에 운영자가 E-stop에 즉시 손이 닿는 위치에 있어야 한다.

```bash
ping -c 1 192.168.1.10
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
ls -l /dev/input/js* /dev/input/event* 2>/dev/null
```

D435가 연결되어 있으면 다음도 확인한다.

```bash
rs-enumerate-devices | sed -n '1,100p'
```

확인할 실제 값:

- `INDY_IP`: 기본 예시는 `192.168.1.10`
- `MARK7_PORT`: 예시 `/dev/ttyACM0`
- `CAMERA_SERIAL`: 현재 예시 `_317222074298`
- `WORKSPACE_MIN_MM`: Indy base 기준 `[x_min, y_min, table_z + 15]`
- `WORKSPACE_MAX_MM`: Indy base 기준 `[x_max, y_max, table_z + 250]`

소스의 기본 z 값 `15`, `250`을 실제 table z로 오해하지 않는다. 테이블 높이가 Indy
base 원점의 z=0이 아니라면 반드시 실제 절대 좌표로 환산한다.

## 5. Teach-in

G1 절차에 따라 로봇을 조그한 뒤 다음 13개 위치를 직접 저장한다.

- `grid_1` ~ `grid_9`
- `eval_5` ~ `eval_8`

위치 매핑은 다음과 같다.

```text
G1 ───── G2 ───── G3
│    Q1   │   Q2    │
G4 ───── G5 ───── G6
│    Q3   │   Q4    │
G7 ───── G8 ───── G9
```

| position ID | 물리 위치 |
|---|---|
| `grid_1`~`grid_9` | G1~G9 |
| `eval_1`~`eval_4` | G5, G1, G6, G8 순서 |
| `eval_5`~`eval_8` | Q1~Q4 순서 |
| `pilot_1`, `pilot_2` | 본 학습·평가와 분리된 연습 위치 |

`eval_1~eval_4`는 대응 grid와 물리적으로 같은 위치다. Xbox teach-in에서
`grid_5/1/6/8`의 평균값을 각각 자동 복사하므로 직접 teach하지 않는다. 본 실험에서
직접 저장할 서로 다른 위치는 `grid 9 + Q 4 = 13곳`이다. `pilot_1/2`는 이번
teach-in에서 제외한다.

### Xbox EEF teach-in

Indy7, Mark7, 그리퍼 서비스와 Xbox 노드를 `docs/xbox_teleop_aliases.md`의 순서로
실행한다. Xbox 창에서 MODE 버튼을 누르면 teach-in 모드로 들어간다. 위치 순서는
`grid_1~grid_9`, `eval_5~eval_8(Q1~Q4)`이다.

각 위치에서 아래 사이클을 **서로 독립적으로 3회** 수행한다.

1. `B`로 그리퍼를 열어 직전 파지를 놓는다.
2. `BACK+Y`로 HOME에 이동한다.
3. PVC를 해당 표식의 중심에 다시 세운다.
4. D-pad와 LT/RT로 접근한다.
5. 실제 파지 위치에서 `A`로 PVC를 잡는다.
6. 파지가 안정된 것을 육안으로 확인하고 `X`를 눌러 저장한다.
7. 다음 반복은 다시 1번부터 수행한다.

버튼은 `LB/RB=이전/다음 위치`, `Y=현재 위치의 직전 샘플 취소`, `MODE=teach-in
종료`다. 한 위치가 3회 완료되면 다음 미완료 위치로 자동 이동한다. `START` 데이터
기록은 teach-in 중 차단된다. 각 샘플 전에 `B open`과 `BACK+Y HOME`을 모두
수행하지 않으면 저장이 거부된다.

각 저장 시점의 다음 값이 함께 기록된다.

- EEF pose: Indy base 기준 `[x, y, z, rx, ry, rz]` (mm/deg)
- Indy7 관절각: `[j1, ..., j6]` (deg)
- 3회 EEF 평균, 축별 표준편차, 최대 위치 편차

EEF 평균이 평가의 `p_target`이며 관절각은 재현·검증용 보조 기록이다. 기존
`teach_target_node`는 비상 수동 경로로만 남기며 Xbox 노드와 동시에 저장하지 않는다.

13개 위치를 완료한 뒤 값을 검사한다.

```bash
sed -n '1,240p' experiment/positions.yaml
```

세션 시작마다 다시 teach-in하고 이전 세션과의 차이를 기록한다.

## 6. 수집량과 A~D 조건

본 수집 목표는 usable demonstration 220개다.

| 위치 | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | 합계 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 개수 | 20 | 20 | 20 | 20 | 60 | 20 | 20 | 20 | 20 | 220 |

위치 순서는 무작위·균형 schedule로 섞는다. 수집 후 A=G5×60,
B=(G1,G6,G8)×20, C=`(7,6,7)`을 각 행에 적용한 9곳 총 60개,
D=9곳×20=180의 immutable subset을 만든다. 조건별 seed 0, 1, 2는 같은 episode
manifest를 사용한다.

수집은 `기본 20 rounds × 9곳 = 180개`와 `G5 추가 40개`의 두 단계다. G5 추가분은
시간 confound를 줄이도록 여러 세션에 나눠 배치한다. 현 Xbox 코드에는 G5-only
schedule이 없으므로 아래 명령은 기본 180개용이며, 본 수집 전에 추가 schedule을
구현·검증한다.

## 7. 평가 계획

모든 A~D seed 모델을 `eval_1~eval_8`에서 각각 2회 평가한다. 모델당 16회,
12모델 총 192회다. G5/G1/G6/G8의 동일 grid 위치를 주평가로, Q1~Q4의 격자 내부
보간을 보조평가로 보고한다. Q1~Q4에서는 demonstration을 수집하지 않는다.

## 8. G1/G2 게이트

본 수집 전 다음 문서의 절차와 통과 기준을 만족해야 한다.

- `docs/gates/G1_hardware.md`
- `docs/gates/G2_G3_collection.md`

핵심 기준:

- G1: 10 mm square 추종 RMS `<1 mm`, settling `<0.3 s`
- G1: workspace 밖 명령 거부, watchdog `0.5 s` 확인
- G2: RGB 해상도·프레임률과 RGB/로봇 상태 timestamp 안정성 확인
- G2: PVC가 15개 물리 위치에서 충분히 보이고 로봇 팔에 과도하게 가리지 않는지 확인
- 카메라 자동 노출을 끄고 exposure, gain, white balance readback 확인
- RGB exposure는 물리값 5,000 us에 대응하는 D435 raw 값 `50`을 사용한다.
  raw 값 `5000`은 약 500 ms 노출이 되어 RGB가 약 2 Hz로 떨어지므로 사용하지 않는다.

게이트 결과를 해당 문서에 기록한다.

## 9. P1~P9 위치별 본 데이터 수집

Indy7, Mark7, 그리퍼 서비스와 Xbox는 먼저 각각 실행한다. RealSense Viewer는 D435를
점유하므로 닫는다. 아래 명령은 RGB 카메라와 해당 위치에 고정된 recorder만 실행한다.
동시에 둘 이상의 위치 명령을 실행하지 않는다.

```bash
# P1 -> episodes/main/p1
./scripts/collection/collect_p1.sh

# P2 -> episodes/main/p2
./scripts/collection/collect_p2.sh

# P3 -> episodes/main/p3
./scripts/collection/collect_p3.sh

# P4 -> episodes/main/p4
./scripts/collection/collect_p4.sh

# P5 -> episodes/main/p5
./scripts/collection/collect_p5.sh

# P6 -> episodes/main/p6
./scripts/collection/collect_p6.sh

# P7 -> episodes/main/p7
./scripts/collection/collect_p7.sh

# P8 -> episodes/main/p8
./scripts/collection/collect_p8.sh

# P9 -> episodes/main/p9
./scripts/collection/collect_p9.sh
```

위치별 수집 스크립트를 실행하면 RGB 미리보기 창이 기본으로 함께 열린다. 창에는
`/overhead_camera/camera/color/image_raw`가 표시된다. 미리보기 창을 닫아도 recorder와
카메라 수집은 계속된다. GUI가 필요 없는 실행에서는 launch 인자
`show_camera:=false`를 사용할 수 있다.

각 명령은 내부적으로 `P1=grid_1`부터 `P9=grid_9`까지의 `position_id`를 고정한다.
Xbox가 발행하는 랜덤 schedule context는 recorder가 무시한다. 중단 후 같은 명령을
다시 실행하면 기존 폴더에 새 UUID episode를 추가하고 `round_index`를 이어간다.

목표 usable success episode는 P5가 60개, 나머지 위치가 각각 20개다. 실패 episode도
원본에는 `success_label=fail`로 보존하되 학습 subset에서는 제외한다.

세션과 운영자 ID를 바꾸려면 실행 전에 환경변수를 지정한다.

```bash
export GRIP_SESSION_ID=main_20260809
export GRIP_OPERATOR_ID=sirlab
./scripts/collection/collect_p1.sh
```

### 원본 HDF5 포맷

각 시연은 20 Hz RGB-only `episode_<UUID>.h5` 하나로 저장된다. 원본에는 action을
저장하지 않는다. 영상은 별도 MP4가 아니라 같은 파일의 `/obs/rgb` dataset에 저장된다.
따라서 RGB와 joint/EEF/gripper timestamp의 동기 관계가 하나의 episode 안에 유지된다.

| dataset | dtype / shape | 의미 |
|---|---|---|
| `/obs/rgb` | `uint8 [T,480,640,3]` | overhead RGB |
| `/state/ee_pose` | `float32 [T,6]` | Indy base TCP `[x,y,z,rx,ry,rz]` |
| `/state/joint_pos` | `float32 [T,6]` | Indy7 관절각 rad |
| `/state/gripper_cmd` | `uint8 [T]` | 0=open, 1=closed |
| `/time/stamp_rgb` | `float64 [T]` | RGB timestamp |
| `/time/stamp_joint` | `float64 [T]` | joint timestamp |
| `/time/stamp_ee` | `float64 [T]` | EEF timestamp |
| `/time/stamp_recv` | `float64 [T]` | recorder 수신 timestamp |

주요 attribute는 `schema_version=2`, `observation_mode=rgb_only`, `position_id`,
`round_index`, `session_id`, `operator_id`, `success_label`, `frame_count`, 카메라
내부 파라미터와 고정 노출 readback이다.

ACT 변환 후에는 5 Hz LeRobot 데이터셋이 된다.

- `observation.images.overhead`: RGB `[240,320,3]`
- `observation.state`: 10차원 = EEF XYZ 3 + joint 6 + gripper 1
- `action`: 4차원 = `EEF_xyz[t+4]-EEF_xyz[t]` 3 +
  목표 gripper `gripper_cmd[t+4]` 1

따라서 하나의 5 Hz 학습 step은 현재 `observation[t]`에서 0.2초 뒤의 EEF 이동량과
목표 그리퍼 상태를 예측한다. `observation.state`의 그리퍼는 현재 상태
`gripper_cmd[t]`이고, `action`의 그리퍼는 목표 상태 `gripper_cmd[t+4]`이므로
닫기 직전 observation에도 닫기 action이 정답으로 포함된다.

본 ACT 학습은 조건별·seed별로 100,000 optimization step을 수행한다. 체크포인트는
20,000 step마다 저장하며, 본 평가에는 100,000-step 최종 체크포인트를 사용한다.

## 10. Xbox 수집 조작

| 입력 | 동작 |
|---|---|
| D-pad | X/Y 이동 |
| LT / RT | Z 하강 / 상승 |
| 회전축 | 사용 안 함 |
| A | 그리퍼 닫기 |
| B | 그리퍼 열기 |
| START | 기록 시작 |
| 기록 중 START | 기록 종료 및 라벨 입력 대기 |
| 라벨 대기 중 A | success로 저장 |
| 라벨 대기 중 B | fail로 저장 |
| 라벨 대기 중 X | 현재 episode 폐기 |
| BACK | 텔레옵 정지 |
| BACK + A | fault 복구 |
| BACK + B | zero 이동 |
| BACK + Y | home 이동 |
| BACK + LB / RB | 이동 step 감소 / 증가 |

권장 episode 순서:

1. 실행한 `collect_pN.sh`와 실제 PVC 위치 Pn이 같은지 확인한다.
2. 물체와 그리퍼를 초기 상태로 리셋한다.
3. 필요하면 B로 그리퍼를 연다.
4. START를 눌러 기록을 시작한다.
5. D-pad와 trigger로 연속적인 파지 시연을 수행한다.
6. A로 그리퍼를 닫고 물체를 들어 올린다.
7. START를 누른다.
8. A/B/X로 success/fail/discard를 선택한다.
9. 저장 완료 메시지와 현재 폴더의 episode 수를 확인한다.

첫 번째 START를 누르면 Indy task teleop 전환을 완료한 뒤 HDF5 기록을 시작한다.
두 번째 START를 누르면 먼저 recorder의 프레임 추가를 일시정지한다. 라벨을 기다리는
동안에는 마지막 EEF 목표를 heartbeat로 계속 보내므로 로봇은 움직이지 않고
`watchdog_timeout`도 발생하지 않는다. A/B로 라벨을 확정하면 recorder가 HDF5를
먼저 닫은 뒤 task teleop을 정지한다. 따라서 라벨 선택 중 가만히 있던 구간과 teleop
시작·정지에 따른 약 0.3초 상태 공백은 episode 안에 포함되지 않는다. X(discard)는
파일을 폐기한 뒤 task teleop을 정지한다.

Indy 드라이버는 RTDE 상태 읽기 타이머와 제어 RPC를 서로 다른 callback group에서
처리한다. 따라서 `MoveTeleL` 호출 중에도 joint/EEF 상태의 20 Hz 발행이 계속된다.
또한 `raw_topic_counts`와 `dropped_sync_estimate`는 두 번째 START의 pause 경계에서
고정되며, 라벨 선택 중 도착한 토픽은 episode QA에 포함하지 않는다.

라벨을 선택하기 전에 노드를 종료하지 않는다. 기록 중 비정상 종료된 `.partial.h5`는
완료 episode로 사용하지 않는다.

## 11. ROS 서비스로 수동 제어

Xbox 없이 recorder만 시험할 때 사용할 수 있다.

```bash
# 반드시 기록 시작 전에 context 지정
ros2 topic pub --once /grip_collect/context std_msgs/msg/String \
  "{data: '{\"position_id\":\"pilot_1\",\"round_index\":0}'}"

ros2 service call /grip_collect/start std_srvs/srv/Trigger '{}'
ros2 service call /grip_collect/gripper/open std_srvs/srv/Trigger '{}'
ros2 service call /grip_collect/gripper/close std_srvs/srv/Trigger '{}'

# 둘 중 하나로 라벨 지정
ros2 service call /grip_collect/mark_success std_srvs/srv/Trigger '{}'
ros2 service call /grip_collect/mark_fail std_srvs/srv/Trigger '{}'

ros2 service call /grip_collect/stop std_srvs/srv/Trigger '{}'
```

현재 episode를 저장하지 않으려면 stop 대신 discard를 호출한다.

```bash
ros2 service call /grip_collect/discard std_srvs/srv/Trigger '{}'
```

서비스 기반 수집에서도 기록 전에 `position_id`가 실제 물체 위치와 같은지 확인한다.

## 12. 실행 중 모니터링

```bash
ros2 topic echo /grip_collect/status
ros2 topic echo /indy/teleop_status
ros2 topic hz /overhead_camera/camera/color/image_raw
ros2 topic hz /indy/ee_pose_stamped
```

즉시 중단해야 하는 상태:

- `fault_latch=true`
- `guard_count` 증가
- `workspace_unconfigured`
- `watchdog_timeout`
- RGB/EEF/joint 중 한 토픽의 중단
- 카메라 자동 노출이 켜지거나 exposure/gain/white balance가 고정값에서 변함
- 카메라, 지그, TCP 또는 물체 위치가 세션 중 변함

## 13. 저장 결과 확인

최근 생성 파일:

```bash
find episodes/main -mindepth 2 -maxdepth 2 -name '*.h5' \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort
```

HDF5 내용과 attrs:

```bash
/opt/workspace/yuykim/miniconda3/envs/act/bin/python - <<'PY'
from pathlib import Path
import h5py

path = max(Path('episodes/main').glob('p*/episode_*.h5'), key=lambda p: p.stat().st_mtime)
print('checking:', path)
with h5py.File(path, 'r') as f:
    f.visit(print)
    print('\nattrs:')
    for key, value in sorted(f.attrs.items()):
        print(f'{key}: {value}')
    required = (
        '/obs/rgb', '/state/ee_pose',
        '/state/joint_pos', '/state/gripper_cmd',
        '/time/stamp_rgb', '/time/stamp_joint',
        '/time/stamp_ee', '/time/stamp_recv',
    )
    assert all(key in f for key in required)
    assert '/action' not in f
    assert f.attrs['data_block'] == 'main'
    assert f.attrs['observation_mode'] == 'rgb_only'
    assert f.attrs['position_id'] != ''
    assert f.attrs['frame_count'] > 0
PY
```

필수 확인 항목:

- 모든 필수 dataset 존재
- `/action` 없음
- RGB compression이 LZF
- `data_block`이 의도한 값
- `session_id`, `operator_id`, `position_id`, `round_index` 정확
- `camera_readback_verified=true`
- `success_label`이 `success` 또는 `fail`
- `.partial.h5`가 아님

추가로 위치별 usable main episode 수가 G5=60, 나머지=20인지 집계하고, A~D
manifest의 UUID가 `docs/experiment_design.md`의 조건을 만족하는지 검사한다.

## 14. 데이터 블록 규칙

| 목적 | 디렉터리 | `data_block` |
|---|---|---|
| 구현·센서·동작 점검 | `episodes/_dev/` | `dev` |
| G6 파일럿 | `episodes/_pilot/` | `pilot` |
| 동결 후 본 수집 | `episodes/main/p1`~`p9` | `main` |

`dev`와 `pilot` 데이터를 본 학습 데이터에 섞지 않는다. 본 수집을 시작한 뒤 카메라
위치, 노출, timestamp 의미, EEF 좌표계, gripper 정의, 물체 또는 제외 규칙을 변경하면
앞서 모은 데이터를 폐기하거나 별도 block으로 분리한다.

## 15. 종료

정상 종료 순서:

1. 기록 중이면 라벨을 선택해 episode 저장 또는 discard를 완료한다.
2. BACK으로 Indy 텔레옵을 정지한다.
3. Xbox 노드를 `Ctrl+C`로 종료한다.
4. rosbag 및 collection launch를 각각 `Ctrl+C`로 종료한다.
5. 남은 `.partial.h5`와 `/indy/teleop_status`의 fault 여부를 확인한다.
6. 저장된 HDF5를 위 검증 스크립트로 검사한다.

본 수집 전 최종 체크리스트:

- [ ] G1 통과 기록
- [ ] RGB-only G2 통과 기록
- [ ] 모든 위치 teach-in 완료
- [ ] 실제 workspace 경계 적용
- [ ] G5/G1/G6/G8의 success first-close EEF 평균 계산 확인
- [ ] 사전등록 TBD 해소 및 외부 등록
- [ ] `experiment-frozen` 태그 생성
- [ ] RGB 카메라 readback 및 위치 배치 사진 보존
- [ ] RGB-only recorder/변환기 배선 검증
- [ ] 220개 수집 schedule과 A~D subset 규칙 동결
- [ ] 기본 180개 + G5 추가 40개 schedule 및 재개 동작 확인
- [ ] dev/pilot 데이터와 main 출력 경로 분리
