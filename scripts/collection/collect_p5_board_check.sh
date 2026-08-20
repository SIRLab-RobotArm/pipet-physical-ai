#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT=/opt/workspace/sirlab-paper-indy7-grip
BOARD_CHECK_ID=${GRIP_BOARD_CHECK_ID:-board_shift_check_20260814}
export GRIP_OUTPUT_DIR=${PROJECT_ROOT}/episodes/_diagnostic/${BOARD_CHECK_ID}/p5
export GRIP_DATA_BLOCK=pilot
export GRIP_SESSION_ID=${GRIP_BOARD_CHECK_SESSION_ID:-${BOARD_CHECK_ID}}

exec "${PROJECT_ROOT}/scripts/collection/collect_position.sh" grid_5 p5
