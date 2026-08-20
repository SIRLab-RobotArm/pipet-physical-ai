#!/usr/bin/python3
"""Legacy 2026-08-14 P5 board-alignment helper, not an evaluation target.

The hard-coded pose comes from the older ``episodes/main/p5`` diagnostic
batch.  Do not use it to populate ``experiment/positions.yaml`` or rollout
``p_target`` for the 2026-08-17 recollection experiment.
"""

from neuromeka import IndyDCP3


ROBOT_IP = "192.168.1.10"

HOME_JOINT_DEG = [
    0.005221,
    40.003174,
    -129.996640,
    90.000870,
    0.000435,
    0.001577,
]

# episodes/main/p5의 정상 success 52개에서 계산한 close EEF 평균
# [x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg]
P5_MEAN_POSE = [
    606.107,
    5.479,
    539.644,
    89.989,
    -0.003,
    89.997,
]

# P5 평균에 가장 가까운 실제 success 시연(episode_15, 1.313 mm 차이)의
# close 관절 자세. HOME은 wrist singular이므로 HOME에서 movel을 시작하지 않고
# 먼저 이 자세까지 joint-space로 이동한다.
P5_REFERENCE_JOINT_DEG = [
    14.781788,
    -5.660819,
    -92.645068,
    61.284241,
    16.923460,
    29.796335,
]

VELOCITY_RATIO = 5.0
ACCELERATION_RATIO = 20.0


def main():
    indy = IndyDCP3(robot_ip=ROBOT_IP, index=0)

    try:
        indy.stop_teleop()
        indy.stop_motion()

        print("HOME 이동")
        indy.movej(
            jtarget=HOME_JOINT_DEG,
            vel_ratio=VELOCITY_RATIO,
            acc_ratio=ACCELERATION_RATIO,
        )
        indy.wait_for_motion_state("is_target_reached")

        print("P5 기준 관절 자세 이동")
        indy.movej(
            jtarget=P5_REFERENCE_JOINT_DEG,
            vel_ratio=VELOCITY_RATIO,
            acc_ratio=ACCELERATION_RATIO,
        )
        indy.wait_for_motion_state("is_target_reached")

        print("P5 평균 위치 1.313 mm 보정")
        indy.movel(
            ttarget=P5_MEAN_POSE,
            vel_ratio=VELOCITY_RATIO,
            acc_ratio=ACCELERATION_RATIO,
        )
        indy.wait_for_motion_state("is_target_reached")

        print("P5 평균 위치 도착")

    except KeyboardInterrupt:
        indy.stop_motion()
        raise


if __name__ == "__main__":
    main()
