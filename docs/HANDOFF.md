# Indy7 ACT 그립 프로젝트 인수인계

최종 확인: **2026-08-20 (KST)**

저장소: `/opt/workspace/sirlab-paper-indy7-grip`

현재 단계: **수집·변환·12개 모델 학습 완료, 실로봇 정책 파일럿 1회 성공, 본 평가 준비 중**

> 새 팀원이나 새 에이전트는 이 문서를 가장 먼저 읽는다. 이 문서는 현재 운영 상태를
> 설명한다. 설계 의도는 `docs/experiment_design.md`, 세부 수집법은
> `docs/data_collection_guide.md`, 분석 계획 초안은 `experiment/preregistration.md`에
> 있지만, 일부 문서는 실제 진행보다 오래된 체크리스트를 포함한다.

## 1. 지금 무엇을 하면 되는가

원시 데이터를 다시 수집하거나 모델을 다시 학습할 필요는 없다. 다음 작업은 **본 평가
192회를 시작하기 전 평가 정의와 운영 절차를 동결하는 것**이다.

1. 성공 판정 기준을 확정한다. 현재 후보는 `50 mm 이상 들어 올려 3초 유지`이지만
   아직 공식 확정되지 않았다. 실패 코드와 육안 판정법도 함께 정한다.
2. `eval_1~eval_8`의 정답 EEF 위치 `p_target`과 조건별 최근접 학습 위치 거리 `d`를
   정하고 `experiment/positions.yaml` 및 rollout metadata에 넣는다.
3. 물체가 trial 중 움직였는지 기록하는 `object_move` 입력 방법을 구현하거나, 동일한
   정보를 빠짐없이 남길 수 있는 수동 절차를 동결한다.
4. G5 실행 게이트의 held-out 시연 재생 시험을 수행해 EEF RMS 오차가 3 mm 미만이고
   그리퍼 전환이 재현되는지 기록한다.
5. 12개 모델 × 8개 위치 × 2회에 대한 조건 블라인드 무작위 실행표를 생성한다.
6. 본 평가와 분리된 출력 폴더에서 2~3회 추가 파일럿을 수행해 metadata와 오프라인
   분석까지 확인한다.
7. 위 항목을 동결한 뒤 본 평가 192회를 수행하고 `ai.eval.analyze`로 분석한다.

**주의:** 이미 성공한 P5 파일럿 1회는 파이프라인 점검용이며 192회에 포함하지 않는다.

## 2. 실험의 목적과 고정된 조건

고정 overhead RGB 영상으로 세워진 PVC 파이프를 찾아 파지하고 들어 올리는 ACT
모방학습 실험이다. 시연 개수가 같을 때 위치 분포의 효과(A/B/C), 그리고 위치 분포가
같을 때 데이터 개수의 효과(C/D)를 비교한다.

- 로봇: Indy7
- 그리퍼: Mark7, `grasp` 프리셋은 엄지 0과 나머지 네 손가락 350
- 카메라: 고정 overhead Intel RealSense D435의 **RGB만 사용**
- Depth: 수집·학습·평가 모두 사용하지 않음
- 물체: ㈜대성산업 비압력용 경질 PVC-U, KS M 3404, SDR 9/VN 직관,
  규격 20×4 m, KS 인증 제6666호를 250 mm로 절단
- 물체 치수: 외경 25 mm, 내경 20 mm
- 표면: 오버그립 없음
- 물체 수: 동일한 PVC 1개, 예비 물체 없음
- 격자: 3×3, 실측 표식 간격은 가로 약 150 mm, 세로 약 130 mm
- 들어 올림 성공 여부는 지금까지 운영자가 육안 확인

수집과 현재 평가 launch는 사용자의 실험 결정에 따라 소프트웨어 workspace 경계를
사용하지 않는다. 물리 가림막으로 작업 범위를 제한한다. 다만 실행 드라이버는 한 번에
요청되는 이동량을 L2 25 mm로 제한하고 watchdog을 사용한다. 로봇을 움직일 때 운영자는
항상 E-stop에 손이 닿는 위치에 있어야 한다.

## 3. 진행 완료 내역

| 단계 | 상태 | 결과 |
|---|---|---|
| 새 데이터 재수집 | 완료 | P1~P4/P6~P9 각 20개, P5 60개, 총 220개 |
| 원시 HDF5 QA | 완료 | 새 재수집본 220/220 통과 |
| RGB-only LeRobot 변환 | 완료 | 전체 176,837개 5 Hz sample |
| A~D membership 동결 | 완료 | UUID manifest와 SHA-256 저장 |
| A~D dataset 생성 | 완료 | 네 개 subset 모두 생성 |
| RGB ACT smoke test | 완료 | A~D 각각 1-step 학습·checkpoint reload 성공 |
| 본 학습 | 완료 | A~D × seed 0/1/2, 총 12개, 각 100,000 step |
| checkpoint 확인 | 완료 | 각 모델 20k/40k/60k/80k/100k와 `last` 존재 |
| 실로봇 정책 파일럿 | 완료 | A/seed 0, P5에서 찾아가기·파지·들어 올림 성공 |
| 본 평가 | **미시작** | 평가 정의와 순서 동결 후 192회 수행 예정 |

## 4. 데이터 인벤토리

### 4.1 원시 데이터

경로: `episodes/main_recollection_20260817`

| 위치 | usable HDF5 수 |
|---|---:|
| P1 | 20 |
| P2 | 20 |
| P3 | 20 |
| P4 | 20 |
| P5 | 60 |
| P6 | 20 |
| P7 | 20 |
| P8 | 20 |
| P9 | 20 |
| 합계 | **220** |

총 원시 frame은 177,717개다. 각 HDF5는 RGB `uint8 [T,480,640,3]`, EEF pose,
6축 관절값, binary gripper command와 각 timestamp를 담는다. 원시 파일을 삭제하거나
덮어쓰지 않는다.

### 4.2 전체 변환 dataset

- 경로: `datasets/main_recollection_20260817_rgb_all`
- repo ID: `sirlab/grip_recollection_20260817_all`
- manifest: `experiment/manifests/main_recollection_20260817_rgb_all.json`
- 변환 sample: **176,837**
- 파생 trajectory: **880** (`220 raw episode × 4 phase offset`)
- dataset SHA-256: `abca0fcdccabb40035f344cef9b7c907ffda24915ae1081ee1ed96fbd65d016b`

파생 trajectory는 시연을 새로 만든 것이 아니다. 20 Hz 시연 하나를 시작 offset
0/1/2/3인 네 개의 5 Hz 궤적으로 나누어 모든 관측 frame을 보존한 것이다.

학습 계약은 다음과 같다.

- RGB: `(3,240,320)`
- observation state 10차원: EEF XYZ mm 3개 + joint rad 6개 + gripper 1개
- action 4차원: `ee_pose[t+4,:3] - ee_pose[t,:3]` + `gripper_cmd[t+4]`
- 회전 action은 사용하지 않음
- RGB/상태 관측은 20 Hz, action trajectory는 5 Hz

### 4.3 조건별 dataset과 membership

| 조건 | 원시 시연 구성 | 원시 수 | 파생 수 | frame 수 | membership SHA-256 |
|---|---|---:|---:|---:|---|
| A | P5×60 | 60 | 240 | 45,614 | `468f1494647bf7821a67fd2a7ef3e851beaf68f8deb4324d93e707a7d9850170` |
| B | P1/P6/P8 각 20 | 60 | 240 | 48,021 | `df7141750c1df619bb43496d48d26b13197320b02006ea7b0b035f846d81c56d` |
| C | P1~P9=`7,6,7/7,6,7/7,6,7` | 60 | 240 | 49,136 | `729128fa97e2b54e514ed5813a32674466456c72c92712fa61707c5ceda1d7da` |
| D | P1~P9 각 20 | 180 | 720 | 146,332 | `84d4ce373354cecbe0b406e1039341314f5c8dad3266f56f767d985c9284ff38` |

경로는 `datasets/main_recollection_20260817_rgb_{a,b,c,d}`이고, membership은
`experiment/manifests/main_recollection_20260817_condition_<a-d>_uuids.json`, subset
dataset manifest는 같은 이름의 `_dataset.json` 파일이다. 조건 C UUID는 조건 D의
부분집합으로 검증되어 있다.

## 5. 학습 결과

본 학습은 LeRobot ACT, RGB-only ResNet18 ImageNet backbone, CVAE, chunk size 40,
execution horizon 10, batch 64, seed 0/1/2, 100,000 optimization step으로 수행했다.
checkpoint는 20,000 step마다 저장했다. 12개 실행은 모두 `End of training`까지 끝났고
CUDA OOM이나 runtime error가 없었다.

| 조건 | seed 0 최종 보고 loss | seed 1 | seed 2 |
|---|---:|---:|---:|
| A | 0.019 | 0.018 | 0.017 |
| B | 0.019 | 0.019 | 0.019 |
| C | 0.019 | 0.018 | 0.018 |
| D | 0.030 | 0.027 | 0.028 |

loss는 조건별 dataset 규모와 분산이 다르므로 성공률처럼 직접 비교하면 안 된다. 실제
성능 결론은 동일한 평가 계획으로 수행한 rollout 결과로 내린다.

- 모델 경로: `ai/models/main_recollection_20260817_<a-d>_s<0-2>_100000`
- 평가 weight: 각 경로의 `checkpoints/last/pretrained_model`
- 중간 checkpoint: `020000`, `040000`, `060000`, `080000`, `100000`
- 학습 로그: `experiment/training_logs/main_recollection_20260817_<a-d>_s<0-2>_100000.log`
- 전체 본 모델 용량: 약 35 GB
- 학습 실행기: `scripts/train/run_main_matrix.sh`
- smoke 모델: `ai/models/_smoke_recollection_20260817_<a-d>_1step_rgb`

smoke 모델은 파이프라인 확인용이므로 실로봇 평가에 사용하지 않는다.

## 6. 성공한 실로봇 파일럿

2026-08-20에 조건 A, seed 0의 최종 모델을 P5 대응 `eval_1`에서 1회 실행했다.
운영자가 로봇이 PVC에 접근해 올바르게 파지하고 들어 올리는 것을 육안 확인하고
`success=true`를 기록했다.

- rollout ID: `a_s0_p5_pilot_01`
- 경로: `experiment/rollouts/_pilot/a_s0_p5_pilot_01`
- 산출물: `trace.parquet`, `events.json`, `meta.json`, `rollout.bag/`
- trace: 4,163 rows, 약 208.1초
- gripper close event: 1회
- `trial_end`: 존재
- partial 파일: 없음
- metadata: condition A, seed 0, position `eval_1`, success true

이 파일럿에서 `p_target`과 `d`는 `null`이고 `object_move` event도 없다. 따라서 성공한
동작 확인 자료로는 유효하지만 E1/E2/E3 본 분석 자료로는 완결되지 않았다.

## 7. 본 평가 설계

평가 위치는 다음 8개다.

| 평가 ID | 물리 위치 | 성격 |
|---|---|---|
| `eval_1` | G5 | 학습 grid와 동일 |
| `eval_2` | G1 | 학습 grid와 동일 |
| `eval_3` | G6 | 학습 grid와 동일 |
| `eval_4` | G8 | 학습 grid와 동일 |
| `eval_5` | Q1 | 격자 내부 보간 |
| `eval_6` | Q2 | 격자 내부 보간 |
| `eval_7` | Q3 | 격자 내부 보간 |
| `eval_8` | Q4 | 격자 내부 보간 |

각 모델을 각 위치에서 2회 실행한다.

```text
4 conditions × 3 seeds × 8 positions × 2 repeats = 192 rollouts
```

G5/G1/G6/G8 결과가 주평가이고 Q1~Q4는 격자 내부 보간 보조평가다. Q 위치를
외삽 일반화로 표현하지 않는다.

## 8. 본 평가 전에 해결해야 하는 차단 항목

### 8.1 정답 위치가 미완성

`experiment/positions.yaml`은 현재 대부분 비어 있다. `grid_1`/`eval_2`만 과거
2-sample 평균이 있으나 `taught:false`, 약 7.48 mm spread warning이 있다.
`eval_1`, `eval_3~eval_8`은 null이다. 오프라인 분석은 각 rollout metadata의
`p_target`을 요구하므로 이 상태로 본 평가를 시작하면 endpoint error 분석이 실패한다.

시연의 close 시점 평균을 정답으로 쓸지, 각 평가 위치를 3회 직접 teach-in한 평균을
쓸지 먼저 확정하고 모든 모델에 동일하게 적용한다. 방법을 결과를 본 뒤 바꾸면 안 된다.

### 8.2 성공 규칙과 실패 코드가 미확정

`experiment/preregistration.md`에 성공 tolerance, lift height, hold duration이 TBD다.
현재 후보 `50 mm/3초`를 그대로 쓸지 먼저 확정한다. 자동 timeout은 없으며 운영자가
결과가 결정된 뒤 `/grip_eval/stop`을 호출하는 방식은 고정되어 있다.

### 8.3 물체 이동 오염 표시가 없음

logger는 `object_move` event를 이해하지만 이를 보내는 서비스/버튼은 아직 없다.
E1/E2 clean trial을 분리하려면 trial 시작 후 파이프가 외력으로 움직인 시점을 반드시
기록해야 한다.

### 8.4 G5 정량 재생 게이트가 미완료

정책 파일럿 성공은 좋은 신호지만 `docs/gates/G5_execution.md`가 요구하는 held-out
시연 동일 executor 재생과 `<3 mm RMS` 검증은 아직 수행하지 않았다. 두 작업은 서로
다르므로 파일럿 성공만으로 G5 정량 게이트를 통과했다고 기록하지 않는다.

### 8.5 실행 순서가 동결되지 않음

조건을 모르는 운영자가 따를 192회 무작위 순서표와 고유 rollout ID 목록이 아직 없다.
수동으로 즉흥 순서를 정하면 시간·조명·운영자 피로가 특정 조건에 몰릴 수 있다.

### 8.6 사전등록 상태와 실제 수집 편차

`experiment/preregistration.md`는 **not frozen and not registered** 상태다. 실제
데이터는 위치별 블록으로 P1, P2, ... 순차 수집했고 P5를 60개 모았다. 이는 문서에 적힌
무작위·균형 interleaving 및 세션 분산 계획과 다르다. 또한 수집과 학습이 이미 끝났으므로
지금 `experiment-frozen` 태그를 만들어 “수집 전 사전등록”이라고 주장해서는 안 된다.

논문과 분석 기록에는 이 편차를 투명하게 남기고, 현재 문서를 retrospective analysis
plan으로 취급할지 지도교수와 확정해야 한다.

## 9. 파일럿/평가 실행 방법

본 평가를 실행하기 전에는 8절의 차단 항목을 먼저 해결한다. 아래는 이미 성공한
A/seed 0 파일럿과 같은 실행 절차다.

### 터미널 1: ACT sidecar

조건과 seed에 맞게 `--model`, `--dataset-root`, repo ID를 함께 바꾼다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/workspace/yuykim/miniconda3/etc/profile.d/conda.sh
conda activate act
export HF_HOME=/opt/workspace/sirlab-paper-indy7-grip/ai/.cache/huggingface

python -m ai.serve.zmq_act_server \
  --model ai/models/main_recollection_20260817_a_s0_100000/checkpoints/last/pretrained_model \
  --dataset-root datasets/main_recollection_20260817_rgb_a \
  --dataset-repo-id sirlab/grip_recollection_20260817_a \
  --device cuda
```

`ACT sidecar ready at tcp://127.0.0.1:5557`가 나와야 한다.

### 터미널 2: 로봇·그리퍼·카메라·executor·logger·bag

`rollout_id`는 절대 재사용하지 않는다. 파일럿은 반드시 `_pilot` 아래에 둔다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=0
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

ros2 launch grip_bringup eval.launch.py \
  rollout_id:=a_s0_p5_pilot_02 \
  output_root:=/opt/workspace/sirlab-paper-indy7-grip/experiment/rollouts/_pilot \
  show_camera:=true \
  meta_json:='{"condition":"A","seed":0,"position_id":"eval_1","experiment_tag":"pilot"}'
```

이 launch가 Indy driver, Mark7 driver, gripper preset node, RGB camera, RGB preview,
policy executor, rollout logger와 rosbag을 함께 시작한다. 따라서 별도의 `grip_indy`,
`grip_mark7`, `grip_gripper`를 동시에 켜지 않는다.

### 터미널 3: 한 trial 조작

1. E-stop 준비, 화면과 로봇 상태 확인
2. 홈 이동과 그리퍼 열기
3. PVC를 해당 위치에 세우기
4. logger 시작
5. 정책 실행 시작
6. 결과가 정해지면 정책 정지
7. logger가 살아 있는 동안 success/failure metadata 전송
8. logger 정지
9. 터미널 2를 종료해 rosbag을 정상 마감

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=0
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

./scripts/robot/back_home.sh
ros2 service call /gripper/open std_srvs/srv/Trigger "{}"

ros2 service call /grip_eval/log/start std_srvs/srv/Trigger "{}"
ros2 service call /grip_eval/start std_srvs/srv/Trigger "{}"

# 결과가 결정되면 실행
ros2 service call /grip_eval/stop std_srvs/srv/Trigger "{}"

# 성공 예시. 실패라면 false와 동결된 failure_code를 기록한다.
ros2 topic pub --once /grip_eval/rollout_meta std_msgs/msg/String \
  '{data: "{\"success\": true, \"failure_code\": null}"}'

ros2 service call /grip_eval/log/stop std_srvs/srv/Trigger "{}"
```

정책은 자동으로 끝나지 않는다. `/grip_eval/stop` 전까지 계속 chunk를 재계획하고
실행한다. 긴급 상황에서는 서비스 호출보다 E-stop을 우선한다.

## 10. 본 평가 rollout 체크리스트

각 rollout마다 다음을 확인한다.

- [ ] 실행표의 condition/seed/position/repeat와 모델 경로가 일치함
- [ ] 고유 `rollout_id` 사용
- [ ] camera와 테이블 위치가 변하지 않음
- [ ] PVC가 지정 표식 중심에 수직으로 섬
- [ ] 홈 위치, 열린 그리퍼, fault 없음
- [ ] logger start 성공 후 policy start
- [ ] policy stop 후 success/failure와 failure code 기록
- [ ] `p_target`, `d`, position ID가 metadata에 존재
- [ ] 물체 이동 오염 여부 기록
- [ ] logger stop 성공
- [ ] launch 종료 후 bag `metadata.yaml` 존재
- [ ] `.partial` 파일이 없음

본 평가 출력 root는 파일럿과 분리해 예를 들어 다음을 사용한다.

```text
experiment/rollouts/main_recollection_20260817_main/
```

권장 rollout ID 형식은 `a_s0_eval_1_r1`이다.

## 11. 평가 후 분석

metadata가 완결된 뒤 실행한다.

```bash
cd /opt/workspace/sirlab-paper-indy7-grip
source /opt/workspace/yuykim/miniconda3/etc/profile.d/conda.sh
conda activate act

python -m ai.eval.analyze \
  --rollouts experiment/rollouts/main_recollection_20260817_main \
  --output experiment/results/main_recollection_20260817_analysis.json
```

현재 `ai.eval.analyze`는 `meta["p_target"]`을 필수로 사용한다. 값이 null인 rollout을
본 분석에 넣지 않는다. 분석에는 성공률, E1/E2/E3, condition×거리 효과와 seed/position
random intercept가 포함된다. 사전에 계획한 독립 평가자의 무작위 20% 영상 재채점과
Cohen's kappa 절차도 본 평가 전에 구체화해야 한다.

## 12. 코드와 운영상 주의점

- 현재 branch/기준 commit은 확인 시점에 `master`, `8a580c1`이었다.
- 하지만 작업 트리는 **dirty**이며 데이터 변환, 학습, 평가 관련 수정과 새 파일이 아직
  HEAD에 모두 commit된 상태가 아니다. `git reset --hard`, `git clean`, 무분별한
  checkout을 사용하지 않는다.
- `eval.launch.py`는 현재 workspace guard를 의도적으로 끄고 RGB preview를 켠다.
- `back_home.sh`는 `/indy_srv`가 살아 있어야 하며 고정 collection HOME 서비스
  `{data: 2}`를 호출한다.
- RealSense Viewer와 ROS camera node를 동시에 실행하면 카메라 점유 충돌이 난다.
- 모든 새 터미널에서 동일한 `ROS_DOMAIN_ID=0`과
  `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`를 사용한다.
- raw HDF5, manifests, 변환 datasets, 본 모델, 학습 로그, 파일럿은 보존한다.
- 이전 `episodes/main`과 `_dev`, `_diagnostic` 자료를 새 재수집본과 섞지 않는다.
- 기존 `_smoke_1step`, `_bench_100`, `_overfit_5000` 같은 과거 RGB-D/4-channel
  artifact가 있으면 현재 RGB-only 본 모델과 혼동하지 않는다.

## 13. 새 세션의 에이전트에게 전달할 문장

다음 문장을 새 세션 첫 요청에 붙이면 현재 상태를 빠르게 이어갈 수 있다.

> `/opt/workspace/sirlab-paper-indy7-grip/docs/HANDOFF.md`를 먼저 끝까지 읽고 실제
> 파일 상태를 대조해라. 새 재수집 데이터 220개, A~D LeRobot dataset, 12개 100k ACT
> 모델과 성공한 A/seed0 P5 파일럿은 완료되어 있으므로 재수집·재변환·재학습하지 마라.
> 다음 목표는 본 평가 전 p_target/d, 성공 기준, object_move 기록, G5 정량 게이트와
> 192회 무작위 실행표를 동결하는 것이다. 기존 dirty worktree를 보존하고 파일럿을 본
> 평가에 포함하지 마라.

## 14. 관련 문서

- 실험 설계: [`experiment_design.md`](experiment_design.md)
- 데이터 수집 운영: [`data_collection_guide.md`](data_collection_guide.md)
- 평가 실행 게이트: [`gates/G5_execution.md`](gates/G5_execution.md)
- 실험 준비 체크리스트: [`experiment_setup_todo.md`](experiment_setup_todo.md)
- 분석 계획/사전등록 초안: [`../experiment/preregistration.md`](../experiment/preregistration.md)
- 위치 파일: [`../experiment/positions.yaml`](../experiment/positions.yaml)
- 저장소 시작 안내: [`../README.md`](../README.md)
