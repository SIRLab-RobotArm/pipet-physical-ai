# ICRiTA 제출을 위한 ACT 기반 RGB 로봇 물체 집기 실험 및 논문 작성 계획서

> 파일명에는 초기 RGB-D 기획의 흔적이 남아 있지만, 2026년 8월 9일 결정에 따라
> 본 실험은 **RGB-only**로 수행한다. Depth 수집·학습·평가는 하지 않는다.

## 1. 연구 목적

Indy7, Mark7 그리퍼와 고정 오버헤드 D435 RGB 영상을 이용해 수직 PVC 파이프를
집어 들어 올리는 ACT 모방학습 task를 구성한다. 같은 하드웨어와 ACT 정책에서
시연 데이터를 **얼마나 많이, 몇 개 위치에 분산해 수집하는가**가 실제 성공률과 실패
유형에 어떤 영향을 주는지 분석한다.

핵심 연구 질문은 다음과 같다.

> 같은 60개 시연에서 한 위치에 집중하는 것과 여러 위치에 분산하는 것 중 무엇이
> ACT 파지 성능에 유리한가? 9개 위치를 고정한 상태에서 60개를 180개로 늘리면
> 성능이 계속 향상되는가?

## 2. 연구 범위와 주장

포함 범위:

- 단일 PVC 물체, 단일 파지 task
- 고정 D435 RGB 카메라 한 대
- ACT 정책 한 종류
- 시연 개수와 XY 위치 분포 비교
- 성공률, 접근 오차, 완료 시간과 실패 유형 분석
- 시연 위치 재현 및 같은 격자 내부의 가까운 위치 보간

제외 범위:

- Depth/RGB-D 실험
- 여러 물체·조명·카메라·작업으로의 일반화
- 학습 격자 밖 외삽 일반화
- ACT와 다른 모방학습 모델의 성능 비교
- 새로운 네트워크 구조 제안

ACT는 관찰된 행동을 모방하는 모델이므로 넓은 일반화를 핵심 주장으로 삼지 않는다.
동일 grid 위치의 재현 성능을 주평가로 두고, 격자 내부 Q 위치는 보조적인 국소 보간
확인으로만 해석한다.

## 3. 하드웨어와 물체

- 로봇: Neuromeka Indy7
- 그리퍼: Mark7 5-finger hand
- 카메라: Intel RealSense D435의 RGB 스트림만 사용
- 물체: ㈜대성산업 비압력용 경질 PVC-U
- 규격: 20×4 m, KS M 3404, SDR 9 / VN 직관, KS 인증 제6666호
- 실험 물체 치수: 길이 250 mm, 외경 25 mm, 내경 20 mm
- 표면: 오버그립 없음
- 물체 수: 동일 물체 한 개

카메라, 테이블, 조명과 workspace는 파일럿 전에 고정한다. 물체의 들어 올림 성공은
우선 육안으로 확인하고, 최종 성공 높이·유지 시간은 파일럿 후 사전등록에서
동결한다. 코드상의 자동 rollout timeout은 사용하지 않으며, 결과가 결정되면
운영자가 `/grip_eval/stop`으로 종료한다.

## 4. 데이터 수집 위치

안전 workspace 안에 3×3 격자 G1~G9를 둔다. Q1~Q4는 네 격자 cell의 중심이다.

```text
G1 ───── G2 ───── G3
│    Q1   │   Q2    │
G4 ───── G5 ───── G6
│    Q3   │   Q4    │
G7 ───── G8 ───── G9
```

격자 중심 `(x0,y0)`과 간격 `dx,dy`는 실제 Indy base 좌표로 측정하고 본 수집 전에
동결한다. 모든 위치는 카메라 시야, 로봇 도달성, 팔 가림과 software workspace를
통과해야 한다.

## 5. 본 데이터 220개 수집

검수와 제외 규칙을 통과한 usable demonstration 기준으로 다음과 같이 수집한다.

| 위치 | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | 합계 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 개수 | 20 | 20 | 20 | 20 | 60 | 20 | 20 | 20 | 20 | **220** |

수집 위치는 무작위·균형 schedule로 섞는다. 위치별로 연속 수집해 시간, 운영자 피로,
조명 변화가 위치와 결합하지 않도록 한다. 실패·discard·손상 episode는 usable 220개에
포함하지 않고 별도 사유를 남긴다.

운영은 G1~G9를 20 rounds 순환하는 기본 180개와 G5 추가 40개로 나눈다. G5 추가분도
한 블록에 몰지 않고 여러 세션에 분산한다. 본 수집 전에 Xbox에 G5-only schedule과
중단 후 재개 기능을 구현·검증한다.

## 6. A~D 학습 조건

220개를 한 번만 수집하고, 모델 결과를 보기 전에 UUID manifest로 아래 부분집합을
동결한다.

| 조건 | 위치와 개수 | 합계 | 목적 |
|---|---|---:|---|
| A | G5×60 | 60 | 한 위치 집중 |
| B | G1·G6·G8에서 각 20 | 60 | 같은 개수, 3위치 분산 |
| C | G1~G9에 6~7개씩 | 60 | 같은 개수, 9위치 분산 |
| D | G1~G9에서 각 20 | 180 | 9위치 고정, 개수 증가 |

조건 C는 다음의 고정 배분을 사용한다.

```text
G1=7   G2=6   G3=7
G4=7   G5=6   G6=7
G7=7   G8=6   G9=7
```

- 분포 효과: A vs B vs C
- 개수 효과: C vs D
- 학습 seed: 0, 1, 2
- 조건별 세 seed는 동일한 dataset manifest 사용
- 전체 본 모델: 4조건×3 seeds = 12개

## 7. 평가 위치와 횟수

모든 12개 모델을 같은 8개 위치에서 평가한다.

| 평가 ID | 실제 위치 | 분석 역할 |
|---|---|---|
| `eval_1` | G5 | 동일 grid 주평가 |
| `eval_2` | G1 | 동일 grid 주평가 |
| `eval_3` | G6 | 동일 grid 주평가 |
| `eval_4` | G8 | 동일 grid 주평가 |
| `eval_5` | Q1 | 내부 보간 보조평가 |
| `eval_6` | Q2 | 내부 보간 보조평가 |
| `eval_7` | Q3 | 내부 보간 보조평가 |
| `eval_8` | Q4 | 내부 보간 보조평가 |

Q1~Q4에서는 demonstration을 수집하지 않는다. `eval_1~eval_4`는 대응 grid의
teach-in 좌표를 그대로 사용한다.

- 위치당 2회
- 모델당 16회
- 전체 12모델×16회 = 192 rollout

조건마다 본 위치가 다르므로 평가 위치를 단순 ID/OOD 이진값으로만 나누지 않는다.
각 평가점에서 해당 조건의 가장 가까운 학습 위치까지 거리 `d`를 함께 기록한다.
다만 논문의 1차 결과는 G5/G1/G6/G8의 동일 grid 성공률이고, Q1~Q4는 보조 결과다.

## 8. Pilot과 위치 ID

`pilot_1`, `pilot_2`는 조작 연습, 파이프라인 확인과 성공 기준 결정에만 사용하고
본 학습·평가에서 제외한다. `positions.yaml`에는 19개 ID가 있지만 실제 서로 다른
물리 위치는 grid 9 + Q 4 + pilot 2 = 15곳이다.

## 9. 기록 계약

- 원시 관측률: 20 Hz
- 학습 관측률: 5 Hz phase split
- 관측: RGB, EEF pose, joint position, gripper state, timestamp
- action: 원시 파일에 저장하지 않음
- 변환 action: `ee_pose[t+4] - ee_pose[t]`와 binary gripper
- 회전 action: 제외
- 카메라 설정: 해상도/FPS/exposure/gain/white balance 고정 및 readback 기록
- 세션 메타데이터: session/operator/position/round ID 기록

## 10. 안전 및 실기 게이트

본 수집 전 다음을 완료한다.

1. 실제 Indy base workspace min/max 측정 및 software guard 적용
2. 10 mm square 추종, out-of-workspace 거부와 0.5 s watchdog 확인
3. RGB 프레임률, timestamp, PVC 대비와 15개 위치의 팔 가림 확인
4. RGB-only recorder/변환기 smoke test
5. 개발 데이터 3~10개와 pilot 20개 검수
6. held-out demonstration 재생 RMS `<3 mm` 확인
7. 성공 기준과 모든 TBD 동결 후 `experiment-frozen` 태그 생성

## 11. 결과와 통계

주요 결과:

- 조건별 전체 성공률과 95% Wilson interval
- 동일 grid 위치 성공률
- Q1~Q4 내부 보간 성공률(보조)
- 위치별 성공률과 최근접 학습 위치 거리 `d`
- 실패 유형별 빈도
- 성공 rollout 완료 시간
- 안전 정지 및 제외 현황

주요 비교는 A/B/C와 C/D다. 혼합효과 분석은 `condition * d`를 고정효과로,
학습 seed와 평가 위치를 random intercept로 고려한다. 적은 rollout에서 나온 작은
차이를 강한 일반화나 통계적 확증으로 과장하지 않는다.

## 12. 논문 구성

1. Introduction: 실제 로봇에서 시연 개수와 위치 분포 선택 문제
2. Related Work: ACT, imitation learning data scaling, demonstration diversity
3. System: Indy7, Mark7, D435 RGB와 PVC task
4. Method: 220개 수집 및 A~D 부분집합
5. Evaluation: 동일 grid 주평가와 Q 내부 보간 보조평가
6. Results: 성공률, 실패 유형, 개수/분포 비교
7. Discussion: ACT 모방 범위, 파지력 한계와 재현성
8. Conclusion

정확한 위치 좌표와 성공 기준 수치는 실기 파일럿 뒤
`experiment/preregistration.md`에 기록하고 본 수집 전에 동결한다.
