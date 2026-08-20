#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT=/opt/workspace/sirlab-paper-indy7-grip

cd "${PROJECT_ROOT}"
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=0
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

if ! ros2 service list | grep -Fxq '/indy_srv'; then
  echo 'ERROR: /indy_srv is unavailable. Start the Indy driver first.' >&2
  exit 1
fi

echo 'Moving Indy7 to the fixed collection HOME...'
ros2 service call /indy_srv indy_interfaces/srv/IndyService '{data: 2}'
