#!/usr/bin/env python3
"""Evaluation graph. The ACT sidecar stays a separate foreground terminal."""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription,
    SetEnvironmentVariable, TimerAction)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution, PythonExpression)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock = LaunchConfiguration("mock")
    rollout_id = LaunchConfiguration("rollout_id")
    output_root = LaunchConfiguration("output_root")
    indy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("indy_driver"), "launch", "indy_bringup.launch.py"])),
        launch_arguments={
            "indy_ip": LaunchConfiguration("indy_ip"), "indy_type": "indy7",
            "launch_rviz": "false", "mock": mock,
            "enforce_workspace": "false", "workspace_configured": "false",
        }.items(), condition=UnlessCondition(mock))
    mark7 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("pipet_hand_mark7_driver"), "launch", "mark7_hardware.launch.py"])),
        condition=UnlessCondition(mock),
        launch_arguments={
            "port": LaunchConfiguration("mark7_port"),
            "use_mock_hardware": "false", "use_rviz": "false",
        }.items())
    gripper = Node(
        package="pipet_hand_mark7_teleop", executable="grip_preset_node",
        condition=UnlessCondition(mock),
        parameters=[PathJoinSubstitution([
            FindPackageShare("pipet_hand_mark7_driver"), "config", "grip_presets.yaml"])])
    camera = Node(
        package="realsense2_camera", executable="realsense2_camera_node",
        namespace="overhead_camera", name="camera", output="screen",
        condition=UnlessCondition(mock),
        parameters=[PathJoinSubstitution([
            FindPackageShare("grip_bringup"), "config", "camera_rgb_only.yaml"]), {
                "serial_no": LaunchConfiguration("camera_serial")}])
    executor = Node(
        package="grip_eval", executable="policy_executor_node", output="screen",
        condition=UnlessCondition(mock),
        arguments=[
            "--endpoint", LaunchConfiguration("act_endpoint"),
            "--workspace-min", LaunchConfiguration("workspace_x_min"),
            LaunchConfiguration("workspace_y_min"), LaunchConfiguration("workspace_z_min"),
            "--workspace-max", LaunchConfiguration("workspace_x_max"),
            LaunchConfiguration("workspace_y_max"), LaunchConfiguration("workspace_z_max"),
            "--no-workspace",
        ],
        additional_env={"GRIP_REPO_ROOT": "/opt/workspace/sirlab-paper-indy7-grip"})
    mock_executor = Node(
        package="grip_eval", executable="policy_executor_node", output="screen",
        condition=IfCondition(mock), arguments=["--mock"])
    logger = Node(
        package="grip_eval", executable="rollout_logger_node", output="screen",
        condition=UnlessCondition(mock),
        arguments=["--output-root", output_root, "--rollout-id", rollout_id,
                   "--meta-json", LaunchConfiguration("meta_json")])
    mock_logger = Node(
        package="grip_eval", executable="rollout_logger_node", output="screen",
        condition=IfCondition(mock),
        arguments=["--mock", "--output-root", output_root, "--rollout-id", rollout_id,
                   "--meta-json", LaunchConfiguration("meta_json")])
    rgb_preview = Node(
        package="image_tools", executable="showimage",
        name="evaluation_rgb_preview", output="screen",
        condition=IfCondition(PythonExpression([
            "'", LaunchConfiguration("show_camera"), "' == 'true' and '",
            mock, "' == 'false'",
        ])),
        remappings=[("image", "/overhead_camera/camera/color/image_raw")],
    )
    bag = TimerAction(period=1.0, actions=[ExecuteProcess(
        condition=UnlessCondition(mock),
        cmd=["ros2", "bag", "record", "-a", "-o", [output_root, "/", rollout_id, "/rollout.bag"]],
        output="screen")])
    return LaunchDescription([
        DeclareLaunchArgument("mock", default_value="false"),
        DeclareLaunchArgument("rollout_id"),
        DeclareLaunchArgument("indy_ip", default_value="192.168.1.10"),
        DeclareLaunchArgument(
            "mark7_port",
            default_value=(
                "/dev/serial/by-id/"
                "usb-Arduino_LLC_Arduino_Micro-if00")),
        DeclareLaunchArgument("camera_serial", default_value="_317222074298"),
        DeclareLaunchArgument("show_camera", default_value="true"),
        DeclareLaunchArgument("output_root", default_value="experiment/rollouts"),
        DeclareLaunchArgument("act_endpoint", default_value="tcp://127.0.0.1:5557"),
        DeclareLaunchArgument("meta_json", default_value="{}"),
        DeclareLaunchArgument("workspace_x_min", default_value="-250"),
        DeclareLaunchArgument("workspace_y_min", default_value="-250"),
        DeclareLaunchArgument("workspace_z_min", default_value="15"),
        DeclareLaunchArgument("workspace_x_max", default_value="250"),
        DeclareLaunchArgument("workspace_y_max", default_value="250"),
        DeclareLaunchArgument("workspace_z_max", default_value="250"),
        SetEnvironmentVariable("PYTHONPATH", [
            "/opt/workspace/yuykim/ros_pydeps:/opt/workspace/sirlab-paper-indy7-grip:",
            EnvironmentVariable("PYTHONPATH", default_value="")]),
        indy, mark7, gripper, camera,
        executor, mock_executor, logger, mock_logger, rgb_preview, bag,
    ])
