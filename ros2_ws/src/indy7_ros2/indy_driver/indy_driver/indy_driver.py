#!/usr/bin/python3
#-*- coding: utf-8 -*-
# import sys
import json
import math
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
# from rclpy.callback_groups import ReentrantCallbackGroup

from std_msgs.msg import Float64MultiArray, Int32MultiArray, String
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint, JointTrajectory

from indy_interfaces.srv import IndyService
from indy_interfaces.msg import EefPose, ServoTx, ServoRx, ServoDataArray

from indy_define import *


COLLECTION_HOME_JOINT_DEG = [
    0.005221,
    40.003174,
    -129.996640,
    90.000870,
    0.000435,
    0.001577,
]


def validate_relative_command(current_pose, delta_pose, workspace_min, workspace_max,
                              max_delta_mm=25.0, enforce_workspace=True,
                              previous_delta_pose=None):
    """Return ``(accepted, reason)`` for a cumulative task-relative target.

    Indy task coordinates are millimetres/degrees. Rotation is intentionally
    disabled. ``max_delta_mm`` applies to the increment from the previous
    cumulative target, while workspace bounds apply to the absolute target.
    """
    if len(current_pose) < 3 or len(delta_pose) != 6:
        return False, "invalid_shape"
    if any(not math.isfinite(float(value)) for value in delta_pose):
        return False, "non_finite"
    if any(abs(float(value)) > 1e-9 for value in delta_pose[3:]):
        return False, "rotation_disabled"
    previous = [0.0] * 6 if previous_delta_pose is None else previous_delta_pose
    if len(previous) != 6:
        return False, "invalid_previous_shape"
    if any(not math.isfinite(float(value)) for value in previous):
        return False, "non_finite_previous"
    step = [float(delta_pose[i]) - float(previous[i]) for i in range(3)]
    norm_mm = math.sqrt(sum(value ** 2 for value in step))
    if norm_mm > float(max_delta_mm) + 1e-9:
        return False, "max_delta"
    if enforce_workspace:
        target = [float(current_pose[i]) + float(delta_pose[i]) for i in range(3)]
        if any(target[i] < float(workspace_min[i]) or target[i] > float(workspace_max[i])
               for i in range(3)):
            return False, "workspace"
    return True, "ok"


class MockIndy:
    """Small deterministic IndyDCP3 substitute used by G0--G5 dry runs."""

    def __init__(self, dof=6):
        self.dof = dof
        self.q = [0.0] * dof
        self.qdot = [0.0] * dof
        self.pose = [0.0, 0.0, 100.0, 0.0, 0.0, 0.0]
        self.op_state = OP_IDLE
        self.stop_count = 0

    def get_control_data(self):
        return {"q": list(self.q), "qdot": list(self.qdot),
                "p": list(self.pose), "op_state": self.op_state}

    def get_control_state(self):
        return {"tau_act": [0.0] * self.dof}

    def get_home_pos(self):
        return {"jpos": [0.0] * self.dof}

    def start_teleop(self, method=None):
        self.op_state = TELE_OP

    def stop_teleop(self):
        self.op_state = OP_IDLE

    def stop_motion(self):
        self.stop_count += 1
        self.op_state = OP_IDLE

    def recover(self):
        self.op_state = OP_IDLE

    def movej(self, jtarget):
        self.q = list(jtarget)

    def wait_for_motion_state(self, _state):
        return True

    def movetelel_rel(self, tpos, vel_ratio=None, acc_ratio=None):
        self.pose = [self.pose[i] + float(tpos[i]) for i in range(6)]

    def movetelej_rel(self, jpos, vel_ratio=None, acc_ratio=None):
        self.q = [self.q[i] + float(jpos[i]) for i in range(self.dof)]

    def movetelej_abs(self, jpos, vel_ratio=None, acc_ratio=None):
        self.q = list(jpos)


class MockEtherCAT:
    def get_servo_rx(self, _index):
        return [0] * 5

    def get_servo_tx(self, _index):
        return [0] * 5

    def set_servo_rx(self, *_args):
        return None

def rads2degs(rad_list):
    degs = [math.degrees(rad) for rad in rad_list]
    return degs

def degs2rads(deg_list):
    rads = [math.radians(deg) for deg in deg_list]
    return rads

class IndyROSConnector(Node):

    PUBLISH_RATE = 20 # Hz

    def __init__(self, force_mock=False):
        super().__init__('indy_driver')
        qos_profile = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE
        )
        # RTDE state reads and control commands use separate IndyDCP3 gRPC
        # channels. Serialize each path independently so a blocking MoveTeleL
        # RPC cannot delay the 20 Hz state-publication timer.
        self.state_callback_group = MutuallyExclusiveCallbackGroup()
        self.command_callback_group = MutuallyExclusiveCallbackGroup()

        # Initialize joint control servers
        self.jtc_action_server = ActionServer(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.command_callback_group,
            )

        self.joint_trajectory_sub = self.create_subscription(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            self.joint_trajectory_callback,
            qos_profile,
            callback_group=self.command_callback_group,
            )
        self.joint_trajectory_sub  # prevent unused variable warning

        # Initialize topics
        self.timer = self.create_timer(
            1/self.PUBLISH_RATE,
            self.timer_callback,
            callback_group=self.state_callback_group,
        )
        self.joint_state_pub = self.create_publisher(JointState, 'joint_states', qos_profile)
        self.ee_pose_pub = self.create_publisher(
            Float64MultiArray, '/indy/ee_pose', qos_profile)
        self.ee_pose_stamped_pub = self.create_publisher(
            EefPose, '/indy/ee_pose_stamped', qos_profile)
        self.teleop_status_pub = self.create_publisher(
            String, '/indy/teleop_status', qos_profile)

        self.teleop_pose_sub = self.create_subscription(
            Float64MultiArray,
            '/indy/teleop_pose',
            self.teleop_pose_callback,
            qos_profile,
            callback_group=self.command_callback_group,
        )
        self.teleop_joint_sub = self.create_subscription(
            Float64MultiArray,
            '/indy/teleop_joint',
            self.teleop_joint_callback,
            qos_profile,
            callback_group=self.command_callback_group,
        )
        
        self.servo_rx_pub = self.create_publisher(ServoDataArray, 'get_servo_rx', qos_profile)
        self.servo_tx_pub = self.create_publisher(ServoDataArray, 'get_servo_tx', qos_profile)
        
        self.set_servo_rx_sub = self.create_subscription(
            Int32MultiArray,
            'set_servo_rx',
            self.set_servo_rx_callback,
            qos_profile,
            callback_group=self.command_callback_group,
        )
        
        # Servicer
        self.indy_srv = self.create_service(
            IndyService,
            'indy_srv',
            self.indy_srv_callback,
            callback_group=self.command_callback_group,
        )

        # Initialize parameters  with default values
        self.declare_parameter('indy_ip', "127.0.0.1")
        self.declare_parameter('indy_type', "indy7")
        self.declare_parameter('mock', bool(force_mock))
        self.declare_parameter('vel_ratio', 0.2)
        self.declare_parameter('acc_ratio', 2.0)
        self.declare_parameter('max_delta_mm', 25.0)
        self.declare_parameter('watchdog_sec', 0.5)
        self.declare_parameter('enforce_workspace', True)
        self.declare_parameter('workspace_configured', bool(force_mock))
        self.declare_parameter('workspace_min_mm', [-250.0, -250.0, 15.0])
        self.declare_parameter('workspace_max_mm', [250.0, 250.0, 250.0])
        self.declare_parameter('home_joint_deg', COLLECTION_HOME_JOINT_DEG)
        self.mock = bool(force_mock or self.get_parameter('mock').value)
        self.vel_ratio = float(self.get_parameter('vel_ratio').value)
        self.acc_ratio = float(self.get_parameter('acc_ratio').value)
        requested_max_delta = float(self.get_parameter('max_delta_mm').value)
        self.max_delta_mm = min(requested_max_delta, 25.0)
        if requested_max_delta > 25.0:
            self.get_logger().warning(
                'max_delta_mm is capped at the preregistered 25 mm safety limit')
        self.watchdog_sec = float(self.get_parameter('watchdog_sec').value)
        self.enforce_workspace = bool(self.get_parameter('enforce_workspace').value)
        self.workspace_configured = bool(self.get_parameter('workspace_configured').value)
        self.workspace_min = list(self.get_parameter('workspace_min_mm').value)
        self.workspace_max = list(self.get_parameter('workspace_max_mm').value)
        self.home_joint_deg = list(self.get_parameter('home_joint_deg').value)
        if (len(self.home_joint_deg) != 6 or
                any(not math.isfinite(float(value)) for value in self.home_joint_deg)):
            raise ValueError('home_joint_deg must contain six finite joint angles')
        if (len(self.workspace_min) != 3 or len(self.workspace_max) != 3 or
                any(lo >= hi for lo, hi in zip(self.workspace_min, self.workspace_max))):
            self.workspace_configured = False
            self.get_logger().error('Invalid workspace bounds; relative commands will be rejected')
        self.indy = None
        self.indy_ip = None
        self.indy_type = None
        self.indy_msg_status = MSG_TELE_STOP

        self.ecat = None
        self.robot_dof = 6
        self.data_per_servo = 5

        # Initialize variable
        # self.vel = 3 # level 1 -> 3
        # self.blend = 0.2 # rad 0 -> 0.4
        self.joint_state_list = []
        self.joint_state_feedback = JointTrajectoryPoint()
        self.execute = False
        self.previous_joint_trajectory_sub = None
        self.last_teleop_command = None
        self.last_command_monotonic = None
        self.teleop_origin_pose = None
        self.fault_latch = False
        self.fault_reason = ""
        self.guard_count = 0

        print("Indy connector has been initialised.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    '''
    Connecting to Indy
    '''
    # Connect to Indy
    def connect(self):
        self.indy_ip = self.get_parameter('indy_ip').get_parameter_value().string_value
        self.indy_type = self.get_parameter('indy_type').get_parameter_value().string_value
        print("ROBOT IP: ", self.indy_ip)
        print("ROBOT TYPE: ", self.indy_type)
        self.robot_dof = 7 if (self.indy_type == 'indyrp2' or self.indy_type == 'indyrp2_v2') else 6
        if self.mock:
            self.indy = MockIndy(self.robot_dof)
            self.ecat = MockEtherCAT()
            self.get_logger().warning('Indy driver running in mock mode')
            return
        try:
            from neuromeka import EtherCAT, IndyDCP3
        except ImportError as exc:
            raise RuntimeError('neuromeka is required unless --mock is used') from exc
        self.indy = IndyDCP3(self.indy_ip)
        self.ecat = EtherCAT(self.indy_ip)

    # Disconnect to Indy
    def disconnect(self):
        print("DISCONNECT TO ROBOT")
        if self.indy is None:
            return
        self.indy.stop_teleop()
        if not self.mock:
            time.sleep(1)
        self.indy.stop_motion()
        if not self.mock:
            time.sleep(1)
        del self.indy 

    '''
    Indy subscribe
    '''

    def indy_srv_callback(self, request, response):                        
        self.get_logger().info('Incoming request | MODE: %d' % (request.data))

        # The state timer runs in a separate callback group.  Disarm the
        # task-teleop watchdog before the blocking robot stop calls below so
        # it cannot race the intentional stop/settle interval and latch a
        # false watchdog fault.
        if request.data == MSG_TELE_STOP:
            self._disarm_watchdog_for_stop()

        self.indy.stop_motion()

        if request.data == MSG_RECOVER:
            self.indy.stop_teleop()
            time.sleep(0.3)
            while self.indy.get_control_data()['op_state'] != OP_IDLE:
                time.sleep(0.1)
            self.indy.recover()
            self.fault_latch = False
            self.fault_reason = ""
            self.indy_msg_status = request.data
            self.teleop_origin_pose = None
            self.last_teleop_command = None

        elif request.data == MSG_MOVE_HOME:
            self.indy.stop_teleop()
            time.sleep(0.3)
            while self.indy.get_control_data()['op_state'] != OP_IDLE:
                time.sleep(0.1)
            self.indy.movej(jtarget=self.home_joint_deg)
            self.indy.wait_for_motion_state('is_target_reached')
            self.indy_msg_status = request.data
            response.message = f'collection HOME reached: {self.home_joint_deg}'

            
        elif request.data == MSG_MOVE_ZERO:
            self.indy.stop_teleop()
            time.sleep(0.3)
            while self.indy.get_control_data()['op_state'] != OP_IDLE:
                time.sleep(0.1)
            self.indy.movej(jtarget = [0,0,0,0,0,0])
            time.sleep(0.2)
            self.indy_msg_status = request.data

        elif request.data == MSG_TELE_STOP:
            self.indy.stop_teleop()
            time.sleep(0.3)
            while self.indy.get_control_data()['op_state'] != OP_IDLE:
                time.sleep(0.1)
                
        elif request.data in [MSG_TELE_TASK_ABS, MSG_TELE_TASK_RLT, MSG_TELE_JOINT_ABS, MSG_TELE_JOINT_RLT]:
            method = TELE_TASK_RELATIVE # default is task
            if request.data == MSG_TELE_TASK_ABS: # Joint
                method = TELE_TASK_ABSOLUTE
            elif request.data == MSG_TELE_JOINT_ABS:
                method = TELE_JOINT_ABSOLUTE
            elif request.data == MSG_TELE_JOINT_RLT:
                method = TELE_JOINT_RELATIVE

            # start teleop
            self.indy.stop_teleop()
            time.sleep(0.1)
            self.indy.start_teleop(method=method) 
            time.sleep(0.2)

            # wait for telemode actually start
            cur_time = time.time()
            timeout = time.time()
            while self.indy.get_control_data()['op_state'] != TELE_OP:
                if (time.time() - cur_time) > 0.5:
                    self.indy.start_teleop(method=method) 
                    cur_time = time.time()
                if (time.time() - timeout) > 3:
                    response.success = False
                    response.message = "TIMEOUT WHEN TRYING TO START TELEOP!!!"
                    return response
                time.sleep(0.2)
            self.indy_msg_status = request.data
            self.last_command_monotonic = time.monotonic()
            self.last_teleop_command = None
            self.teleop_origin_pose = (
                list(self.indy.get_control_data()['p'])
                if request.data == MSG_TELE_TASK_RLT else None
            )

        response.success = True
        return response

    def _disarm_watchdog_for_stop(self):
        self.indy_msg_status = MSG_TELE_STOP
        self.last_command_monotonic = None
        self.teleop_origin_pose = None
        self.last_teleop_command = None

    def joint_trajectory_callback(self, msg): # servoing -> teleop
        joint_state_list = []
        if msg.points:
            joint_state_list = [p.positions for p in msg.points]
        else:
            self.indy.stop_motion()
            return
        # print("joint state list: ", joint_state_list) #rad/s rad
        if self.previous_joint_trajectory_sub != joint_state_list[0]:
            # if TELE MODE
            if self.indy_msg_status == MSG_TELE_JOINT_ABS:
                self.indy.movetelej_abs(
                    jpos=rads2degs(joint_state_list[0]),
                    vel_ratio=self.vel_ratio,
                    acc_ratio=self.acc_ratio)

            self.previous_joint_trajectory_sub = joint_state_list[0]

    def teleop_pose_callback(self, msg):
        if len(msg.data) != 6:
            self.get_logger().warn(
                f'Ignoring /indy/teleop_pose with {len(msg.data)} values; expected 6')
            return
        if self.indy_msg_status != MSG_TELE_TASK_RLT:
            self.get_logger().warn(
                'Ignoring /indy/teleop_pose because task-relative teleop is not active')
            return

        if self.fault_latch:
            self.get_logger().error(
                f'Ignoring /indy/teleop_pose while fault is latched: {self.fault_reason}')
            return
        if self.enforce_workspace and not self.workspace_configured:
            self._latch_fault('workspace_unconfigured')
            return

        origin_pose = self.teleop_origin_pose
        if origin_pose is None:
            origin_pose = list(self.indy.get_control_data()['p'])
            self.teleop_origin_pose = origin_pose
        accepted, reason = validate_relative_command(
            origin_pose, msg.data, self.workspace_min, self.workspace_max,
            self.max_delta_mm, enforce_workspace=self.enforce_workspace,
            previous_delta_pose=self.last_teleop_command)
        if not accepted:
            self.guard_count += 1
            self._latch_fault(f'guard:{reason}')
            self.indy.stop_motion()
            return

        # The Xbox node repeats its last cumulative target as a heartbeat.
        # Refresh the watchdog without resending an unchanged target to Indy.
        is_zero_target = (
            self.last_teleop_command is None
            and not any(abs(float(value)) > 1e-9 for value in msg.data)
        )
        is_duplicate_target = (
            self.last_teleop_command is not None
            and all(
                abs(float(value) - float(previous)) <= 1e-9
                for value, previous in zip(msg.data, self.last_teleop_command)
            )
        )
        if is_zero_target or is_duplicate_target:
            self.last_teleop_command = list(msg.data)
            self.last_command_monotonic = time.monotonic()
            return

        self.indy.movetelel_rel(
            tpos=list(msg.data),
            vel_ratio=self.vel_ratio,
            acc_ratio=self.acc_ratio
        )
        self.last_teleop_command = list(msg.data)
        self.last_command_monotonic = time.monotonic()

    def teleop_joint_callback(self, msg):
        if len(msg.data) != self.robot_dof:
            self.get_logger().warn(
                f'Ignoring /indy/teleop_joint with {len(msg.data)} values; '
                f'expected {self.robot_dof}')
            return
        if self.indy_msg_status != MSG_TELE_JOINT_RLT:
            self.get_logger().warn(
                'Ignoring /indy/teleop_joint because joint-relative teleop is not active')
            return

        self.indy.movetelej_rel(
            jpos=list(msg.data),
            vel_ratio=self.vel_ratio,
            acc_ratio=self.acc_ratio
        )
        self.last_teleop_command = list(msg.data)
        self.last_command_monotonic = time.monotonic()

    def _latch_fault(self, reason):
        self.fault_latch = True
        self.fault_reason = str(reason)
        self.get_logger().error(f'Indy safety fault latched: {self.fault_reason}')

    def _watchdog_check(self):
        if self.indy_msg_status != MSG_TELE_TASK_RLT or self.last_command_monotonic is None:
            return
        if time.monotonic() - self.last_command_monotonic <= self.watchdog_sec:
            return
        self.indy.stop_motion()
        self.indy_msg_status = MSG_TELE_STOP
        self._latch_fault('watchdog_timeout')
        self.last_command_monotonic = None

    def publish_teleop_status(self):
        msg = String()
        msg.data = json.dumps({
            'mode': int(self.indy_msg_status),
            'op_state': int(self.indy.get_control_data()['op_state']),
            'last_command': self.last_teleop_command,
            'fault_latch': bool(self.fault_latch),
            'fault_reason': self.fault_reason,
            'guard_count': int(self.guard_count),
            'enforce_workspace': bool(self.enforce_workspace),
            'mock': bool(self.mock),
        }, sort_keys=True)
        self.teleop_status_pub.publish(msg)
    
    def set_servo_rx_callback(self, msg):
        data = msg.data
        if len(data) < 6:
            self.get_logger().warn('Received data is not complete or incorrect size')
            return
        
        servoIndex      = data[0]
        controlWord     = data[1]
        modeOp          = data[2]
        targetPosition  = data[3]
        targetVelocity  = data[4]
        targetTorque    = data[5]

        # Call the ecat.set_servo_rx method with the received data
        self.ecat.set_servo_rx(servoIndex, controlWord, modeOp, targetPosition, targetVelocity, targetTorque)
        self.get_logger().info(f'Set servo {servoIndex} with values: {controlWord}, {modeOp}, {targetPosition}, {targetVelocity}, {targetTorque}')

    '''
    Indy publish
    '''
    # Publish jointstates
    def joint_state_publisher(self):
        joint_state_msg = JointState()
        joint_state_msg.header.stamp = self.get_clock().now().to_msg()
        
        if self.indy_type == 'indyrp2' or self.indy_type == 'indyrp2_v2':
            joint_state_msg.name = ['joint0', 'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        else:
            joint_state_msg.name = ['joint0', 'joint1', 'joint2', 'joint3', 'joint4', 'joint5']
        
        control_data = self.indy.get_control_data()
        joint_state_msg.position = degs2rads(control_data['q'])
        joint_state_msg.velocity = degs2rads(control_data['qdot'])
        joint_state_msg.effort = self.indy.get_control_state()['tau_act']
        self.joint_state_feedback.positions = joint_state_msg.position
        self.joint_state_pub.publish(joint_state_msg)

        ee_pose_msg = Float64MultiArray()
        ee_pose_msg.data = [float(value) for value in control_data['p']]
        self.ee_pose_pub.publish(ee_pose_msg)
        ee_pose_stamped_msg = EefPose()
        ee_pose_stamped_msg.header.stamp = joint_state_msg.header.stamp
        ee_pose_stamped_msg.header.frame_id = 'indy_base'
        ee_pose_stamped_msg.pose = ee_pose_msg.data
        self.ee_pose_stamped_pub.publish(ee_pose_stamped_msg)
    
    # Publish servo rx, tx
    def publish_servo_rx_data(self):
        msg = ServoDataArray()
        msg.rx = []

        for i in range(self.robot_dof):
            servo_data = self.ecat.get_servo_rx(i)
            
            if isinstance(servo_data, list) and len(servo_data) == self.data_per_servo:
                row = ServoRx(
                    control_word=int(servo_data[0]),
                    mode_op=int(servo_data[1]),
                    target_pos=int(servo_data[2]),
                    target_vel=int(servo_data[3]),
                    target_tor=int(servo_data[4])
                )
                msg.rx.append(row)
            else:
                self.get_logger().error(f'Invalid data format for servo {i}: {servo_data}')
                return
        
        self.servo_rx_pub.publish(msg)
        # self.get_logger().info(f'Published: {msg}')
        
    def publish_servo_tx_data(self):
        msg = ServoDataArray()
        msg.tx = []

        for i in range(self.robot_dof):
            servo_data = self.ecat.get_servo_tx(i)
            
            if isinstance(servo_data, list) and len(servo_data) == self.data_per_servo:
                row = ServoTx(
                    status_word=servo_data[0],
                    mode_op_disp=servo_data[1],
                    actual_pos=int(servo_data[2]),
                    actual_vel=int(servo_data[3]),
                    actual_tor=int(servo_data[4])
                )
                msg.tx.append(row)
            else:
                self.get_logger().error(f'Invalid data format for servo {i}: {servo_data}')
                return
        
        self.servo_tx_pub.publish(msg)
    
    # Timer callback for publish
    def timer_callback(self):
        self._watchdog_check()
        self.joint_state_publisher()
        self.publish_teleop_status()
        # self.publish_servo_rx_data()
        # self.publish_servo_tx_data()

    '''
    Indy follow joint trajectory 
    '''
    def goal_callback(self, goal_request):
        # Accepts or rejects a client request to begin an action
        self.get_logger().info('Received goal request!')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        # Accepts or rejects a client request to cancel an action
        self.get_logger().info('Received cancel request!')
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        print('FollowJointTrajectory callback...')

        result = FollowJointTrajectory.Result()
        feedback_msg = FollowJointTrajectory.Feedback()

        # check if robot is in ILDE mode
        if self.indy.get_control_data()['op_state'] != OP_IDLE:
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            result.error_string = "ROBOT IS NOT READY"
            return result

        # last_time = self.get_clock().now()
        goal = goal_handle.request.trajectory.points.copy()
        
        # download planned path from ros moveit
        self.joint_state_list = []
        if goal:
            self.joint_state_list = [p.positions for p in goal]
            
        is_cancel = False
        # Do something for OP_IDLE state
        if self.joint_state_list:
            #-------------------------------------------------------
            # start teleop
            self.indy.stop_teleop()
            time.sleep(0.1)
            self.indy.start_teleop(method=TELE_JOINT_ABSOLUTE) 
            time.sleep(0.2)

            # wait for telemode actually start
            cur_time = time.time()
            while self.indy.get_control_data()['op_state'] != TELE_OP:
                if (time.time() - cur_time) > 0.5:
                    self.indy.start_teleop(method=TELE_JOINT_ABSOLUTE)  
                    cur_time = time.time()
                time.sleep(0.2)

            # send waypoints
            for j_pos in self.joint_state_list:
                try:
                    self.indy.movetelej_abs(
                        jpos=rads2degs(j_pos),
                        vel_ratio=self.vel_ratio,
                        acc_ratio=self.acc_ratio)
                except Exception as e:
                    self.get_logger().error('THERE ARE ISSUE WHEN EXECUTE WAYPOINT, PLEASE TRY AGAIN!')
                    is_cancel = True
                    break

                if goal_handle.is_cancel_requested:
                    is_cancel = True
                    break

                feedback_msg.desired.positions = rads2degs(j_pos)
                feedback_msg.actual.positions = self.joint_state_feedback.positions
                goal_handle.publish_feedback(feedback_msg)
                time.sleep(0.05) #20Hz

            time.sleep(0.5) # wait for robot stable

            self.indy.stop_teleop()
            time.sleep(0.3)
            while self.indy.get_control_data()['op_state'] != OP_IDLE:
                time.sleep(0.2)

        if is_cancel:
            goal_handle.canceled()
        else:                
            goal_handle.succeed()
            result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result


def main(args=None):
    raw_args = list(sys.argv if args is None else args)
    force_mock = '--mock' in raw_args
    ros_args = [arg for arg in raw_args if arg != '--mock']
    rclpy.init(args=ros_args)
    with IndyROSConnector(force_mock=force_mock) as indy_driver:
        executor = MultiThreadedExecutor()
        executor.add_node(indy_driver)
        try:
            executor.spin()
        finally:
            executor.shutdown()
            indy_driver.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        if rclpy.ok():
            rclpy.shutdown()
