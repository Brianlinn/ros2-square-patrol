import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from turtlesim.msg import Pose


class PatrolController(Node):
    def __init__(self):
        super().__init__('patrol_controller')

        # 可由終端修改的 controller 參數
        self.declare_parameter('patrol_distance', 2.0)
        self.declare_parameter('edge_number', 4)
        # self.declare_parameter('linear_gain', 1.5)
        # self.declare_parameter('angular_gain', 6.0)
        # self.declare_parameter('max_linear_speed', 2.0)
        # self.declare_parameter('max_angular_speed', 2.0)
        # self.declare_parameter('position_tolerance', 0.1)

        self.enable_service = self.create_service(
            SetBool,
            '/patrol_enable',
            self.enable_callback
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        self.pose_subscriber = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.enable = False
        self.state = 'STOPPED'
        self.current_pose = None

        self.timer = self.create_timer(0.01, self.control_loop)

        self.get_logger().info('Patrol Controller Started')

    def pose_callback(self, pose):
        # 讀取目前參數
        self.patrol_distance = self.get_parameter('patrol_distance').value
        self.edge_number = self.get_parameter('edge_number').value
        # self.linear_gain = self.get_parameter('linear_gain').value
        # self.angular_gain = self.get_parameter('angular_gain').value
        # self.max_linear = self.get_parameter('max_linear_speed').value
        # self.max_angular = self.get_parameter('max_angular_speed').value
        # self.tolerance = self.get_parameter('position_tolerance').value
        self.current_pose = pose

    def enable_callback(self, request, response):  # Service的callback
        if request.data:
            if self.current_pose is None:
                response.success = False
                response.message = 'Pose has not been received'
                return response

            self.enable = True
            self.state = 'MOVING'
            self.edge_count = 0     # 重置已走過的邊數
            self.start_x = self.current_pose.x
            self.start_y = self.current_pose.y
            self.start_theta = self.current_pose.theta

            response.success = True
            response.message = 'Patrol started'

        else:
            self.enable = False
            self.state = 'STOPPED'
            self.stop_turtle()

            response.success = True
            response.message = 'Patrol stopped'

        return response

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
            angular_speed = max(-angular_speed, min(max_angular_speed, angular_speed))
            command.angular.z = -angular_speed
            self.cmd_vel_publisher.publish(command)

        elif abs(angle_error) <= angle_tolerance:
            command = Twist()
            self.cmd_vel_publisher.publish(command)

            if self.edge_count >= self.edge_number:
                self.enable = False
                self.state = 'STOPPED'
                self.stop_turtle()
                return

            self.start_x = self.current_pose.x
            self.start_y = self.current_pose.y
            self.state = 'MOVING'

    def stop_turtle(self):
        command = Twist()
        self.cmd_vel_publisher.publish(command)

    def normalized_angle(self, angle):
        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )


def main(args=None):
    rclpy.init(args=args)

    patrol_controller = PatrolController()

    try:
        rclpy.spin(patrol_controller)
    except KeyboardInterrupt:
        pass
    finally:
        patrol_controller.stop_turtle()
        patrol_controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
