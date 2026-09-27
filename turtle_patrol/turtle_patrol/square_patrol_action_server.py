import math
from threading import Event

from geometry_msgs.msg import Twist
import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from turtle_patrol_interfaces.action import SquarePatrol
from turtlesim.msg import Pose


class SquarePatrolActionServer(Node):

    def __init__(self):
        super().__init__('square_patrol_action_server')

        self.current_pose = None
        self.enable = False
        self.state = 'STOPPED'
        self.active_goal_handle = None
        self.callback_group = ReentrantCallbackGroup()
        self.patrol_done = Event()
        self.cancel_request = False

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            'turtle1/cmd_vel',
            10
        )

        self.pose_subscriber = self.create_subscription(
            Pose,
            'turtle1/pose',
            self.pose_callback,
            10,
            callback_group=self.callback_group
        )

        self.squarepatrol_server = ActionServer(
            self,
            SquarePatrol,
            'square_patrol',
            self.execute_callback,

            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info('Action Server started')
        self.timer = self.create_timer(0.01, self.control_loop, callback_group=self.callback_group)

    def pose_callback(self, pose):
        self.current_pose = pose

    def execute_callback(self, goal_handle):
        self.cancel_request = False
        result = SquarePatrol.Result()
        feedback = SquarePatrol.Feedback()

        if self.current_pose is None:
            self.get_logger().info('No current pose of turtle')
            goal_handle.abort()
            result.success = False
            result.message = 'No turtle pose received'

            return result

        self.active_goal_handle = goal_handle

        # 拿 action 請求中 goal 的參數
        self.patrol_distance = goal_handle.request.patrol_distance
        self.laps = goal_handle.request.laps
        self.edge_number = goal_handle.request.edge_number

        self.get_logger().info(
            f'Received goal: patrol_distance={self.patrol_distance}, '
            f'laps={self.laps}, edge_number={self.edge_number}')

        if (self.patrol_distance <= 0.0 or self.laps < 1 or self.edge_number < 3):
            goal_handle.abort()
            result.success = False
            result.message = 'Invalid patrol parameters'

            self.active_goal_handle = None

            return result

        # 紀錄現在的 pose
        self.start_x = self.current_pose.x
        self.start_y = self.current_pose.y

        # 更新現在的狀態
        self.patrol_done.clear()
        self.enable = True
        self.state = 'MOVING'
        self.edge_count = 0
        self.laps_count = 0
        feedback.state = 'Patrol Started'
        feedback.completed_edge = 0
        goal_handle.publish_feedback(feedback)

        # 在此處等待 patrol 跑完
        self.patrol_done.wait()

        if self.cancel_request:
            goal_handle.canceled()
            result.success = False
            result.message = 'Patrol canceled'

        else:
            goal_handle.succeed()
            result.success = True
            result.message = 'Patrol completed'

        self.active_goal_handle = None

        return result

    def control_loop(self):
        if not self.enable:
            return

        if self.state == 'MOVING':
            self.control_moving()

        elif self.state == 'TURNING':
            self.control_turning()

    def control_moving(self):
        if self.current_pose is None:
            return

        command = Twist()
        distance_tolerance = 0.01
        pass_distance_x = self.current_pose.x - self.start_x
        pass_distance_y = self.current_pose.y - self.start_y
        eu_distance = math.sqrt(pass_distance_x**2 + pass_distance_y**2)
        remaining_distance = self.patrol_distance - eu_distance

        if remaining_distance > distance_tolerance:
            linear_gain = 2.0
            max_linear_speed = 1.5
            linear_speed = linear_gain * remaining_distance
            linear_speed = min(linear_speed, max_linear_speed)
            command.linear.x = linear_speed
            self.cmd_vel_publisher.publish(command)

        elif remaining_distance <= distance_tolerance:
            command = Twist()
            self.cmd_vel_publisher.publish(command)

            self.edge_count += 1

            self.state = 'TURNING'
            self.publish_patrol_feedback()
            inner_angle = math.pi * (self.edge_number - 2) / self.edge_number
            outer_angle = math.pi - inner_angle
            self.target_theta = self.normalized_angle(
                self.current_pose.theta - outer_angle
            )

    def control_turning(self):
        command = Twist()
        angle_error = self.normalized_angle(self.target_theta - self.current_pose.theta)
        angle_tolerance = 0.005
        angular_gain = 4.0
        max_angular_speed = 1.5

        if abs(angle_error) > angle_tolerance:
            angular_speed = angular_gain * angle_error
            angular_speed = max(-max_angular_speed, min(max_angular_speed, angular_speed))
            command.angular.z = angular_speed
            self.cmd_vel_publisher.publish(command)

        elif abs(angle_error) <= angle_tolerance:
            command = Twist()
            self.cmd_vel_publisher.publish(command)

            if self.edge_count >= self.edge_number:
                self.laps_count += 1
                self.edge_count = 0

                if self.laps_count >= self.laps:
                    self.enable = False
                    self.state = 'STOPPED'
                    self.publish_patrol_feedback()
                    self.stop_turtle()
                    self.patrol_done.set()
                    return

            self.start_x = self.current_pose.x
            self.start_y = self.current_pose.y
            self.state = 'MOVING'
            self.publish_patrol_feedback()

    def publish_patrol_feedback(self):
        if self.active_goal_handle is None:
            return

        feedback = SquarePatrol.Feedback()
        feedback.completed_edge = (self.laps_count * self.edge_number + self.edge_count)
        feedback.state = self.state

        self.active_goal_handle.publish_feedback(feedback)

    def stop_turtle(self):
        command = Twist()
        self.cmd_vel_publisher.publish(command)

    def normalized_angle(self, angle):
        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    def cancel_callback(self, goal_handle):
        self.get_logger().warning('Cancel request received')
        self.cancel_request = True
        self.enable = False
        self.state = 'CANCELED'
        self.stop_turtle()
        self.publish_patrol_feedback()
        self.patrol_done.set()

        return CancelResponse.ACCEPT

    def goal_callback(self, goal_request):
        if self.enable or self.active_goal_handle is not None:
            self.get_logger().warning(
                'Patrol already running, reject new goal'
            )
            return GoalResponse.REJECT

        if (goal_request.patrol_distance <= 0.0 or goal_request.laps <
                1 or goal_request.edge_number < 3):
            self.get_logger().warning(
                'Invalid patrol parameters'
            )
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT


def main(args=None):
    rclpy.init(args=args)

    square_patrol_action_server = SquarePatrolActionServer()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(square_patrol_action_server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        square_patrol_action_server.stop_turtle()
        executor.shutdown()
        square_patrol_action_server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
