from action_msgs.msg import GoalStatus
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from turtle_patrol_interfaces.action import SquarePatrol


class SquarePatrolActionClient(Node):
    def __init__(self):
        super().__init__('square_patrol_action_client')

        self.declare_parameter('patrol_distance', 2.5)
        self.declare_parameter('laps', 2)
        self.declare_parameter('edge_number', 4)
        self.declare_parameter('cancel_after', 5.0)
        self.patrol_distance = self.get_parameter('patrol_distance').value
        self.laps = self.get_parameter('laps').value
        self.edge_number = self.get_parameter('edge_number').value
        self.cancel_after = self.get_parameter('cancel_after').value

        self.squarepatrol_client = ActionClient(
            self,
            SquarePatrol,
            'square_patrol'
        )

    def send_goal(self):
        goal = SquarePatrol.Goal()
        goal.patrol_distance = self.patrol_distance
        goal.laps = self.laps
        goal.edge_number = self.edge_number

        self.get_logger().info('Waiting for server...')

        self.squarepatrol_client.wait_for_server()

        self.get_logger().info(
            f'Sending goal: patrol_distance={goal.patrol_distance}, '
            f'laps={goal.laps}, edge_number={goal.edge_number}')

        self.send_goal_future = (
            self.squarepatrol_client.send_goal_async(
                goal,
                feedback_callback=self.feedback_callback  # 預先登記 server 回傳 feedback 時要呼叫的函式
            )
        )

        self.send_goal_future.add_done_callback(
            self.goal_response_callback
        )

    def cancel_goal(self):
        self.cancel_timer.cancel()
        self.get_logger().warning('Goal canceling...')

        cancel_future = self.goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(
            self.cancel_response_callback
        )

    def feedback_callback(self, feedback_message):
        feedback = feedback_message.feedback

        self.get_logger().info(
            f'Feedback: completed_edge={feedback.completed_edge}, '
            f'state={feedback.state}'
        )

    def goal_response_callback(self, future):
        self.goal_handle = future.result()

        if not self.goal_handle.accepted:
            self.get_logger().warning('Goal rejected')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted')

        if self.cancel_after > 0:
            self.cancel_timer = self.create_timer(
                self.cancel_after,
                self.cancel_goal
            )
        elif self.cancel_after <= 0:
            pass

        self.result_future = self.goal_handle.get_result_async()
        self.result_future.add_done_callback(
            self.result_callback
        )

    def cancel_response_callback(self, future):
        cancel_response = future.result()

        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info('Cancel request accepted')
        else:
            self.get_logger().warning('Cancel request rejected')

    def result_callback(self, future):
        response = future.result()
        result = response.result
        status = response.status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(
                f'Result: status= {status}, {result.message}'
            )
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info(
                f'Result: status= {status}, {result.message}'
            )
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().info(
                f'Result: status= {status}, {result.message}'
            )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    square_patrol = SquarePatrolActionClient()
    square_patrol.send_goal()
    rclpy.spin(square_patrol)
    square_patrol.destroy_node()


if __name__ == '__main__':
    main()
