from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    patrol_distance_arg = DeclareLaunchArgument('patrol_distance', default_value='2.5')
    laps_arg = DeclareLaunchArgument('laps', default_value='2')
    edge_number_arg = DeclareLaunchArgument('edge_number', default_value='4')
    cancel_after_arg = DeclareLaunchArgument('cancel_after', default_value='0.0')

    patrol_distance = LaunchConfiguration('patrol_distance')
    laps = LaunchConfiguration('laps')
    edge_number = LaunchConfiguration('edge_number')
    cancel_after = LaunchConfiguration('cancel_after')

    turtlesim_node = Node(
        package='turtlesim',          # 對應到ros2 run turtlesim turtlesim_node
        executable='turtlesim_node',
        output='screen'
    )

    action_server_node = Node(
        package='turtle_patrol',      # 對應到ros2 run turtle_patrol square_patrol_action_server
        executable='square_patrol_action_server',
        output='screen'
    )

    action_client_node = Node(
        package='turtle_patrol',
        executable='square_patrol_action_client',
        output='screen',
        parameters=[{
            'patrol_distance': ParameterValue(
                patrol_distance,
                value_type=float
            ),
            'laps': ParameterValue(
                laps,
                value_type=int
            ),
            'edge_number': ParameterValue(
                edge_number,
                value_type=int
            ),
            'cancel_after': ParameterValue(
                cancel_after,
                value_type=float
            )
        }]
    )

    delayed_action_client = TimerAction(
        period=5.0,
        actions=[action_client_node]
    )

    return LaunchDescription([
        patrol_distance_arg,
        laps_arg,
        edge_number_arg,
        cancel_after_arg,

        turtlesim_node,
        action_server_node,
        delayed_action_client,
    ])
