# ROS 2 Square Patrol

A ROS 2 Jazzy project that drives a turtlesim turtle around a regular polygon using an action server. The action client can run the patrol to completion or request cancellation after a configurable delay.

## Architecture

```text
ros2-square-patrol/
├── turtle_patrol/
│   ├── launch/square_patrol.launch.py
│   └── turtle_patrol/
│       ├── square_patrol_action_server.py
│       └── square_patrol_action_client.py
└── turtle_patrol_interfaces/
    └── action/SquarePatrol.action
```

- `turtle_patrol_interfaces` generates the `SquarePatrol` action type.
- `square_patrol_action_server` subscribes to `/turtle1/pose`, publishes velocity commands to `/turtle1/cmd_vel`, and reports patrol progress.
- `square_patrol_action_client` sends a goal, displays feedback and the final status, and optionally requests cancellation.
- `square_patrol.launch.py` starts turtlesim, the action server, and the action client after a five-second delay.

The action name is `/square_patrol`.

## Action interface

```text
# Goal
float64 patrol_distance
int32 laps
int32 edge_number
---
# Result
bool success
string message
---
# Feedback
int32 completed_edge
string state
```

| Field | Meaning |
| --- | --- |
| `patrol_distance` | Length of each polygon edge in turtlesim units; must be greater than zero. |
| `laps` | Number of complete laps; must be at least 1. |
| `edge_number` | Number of polygon edges; must be at least 3. |
| `completed_edge` | Total number of completed edges across all laps. |
| `state` | Current server state, such as `MOVING`, `TURNING`, `STOPPED`, or `CANCELED`. |
| `success` | `true` only when the requested patrol finishes normally. |
| `message` | Human-readable result description. |

The server returns the ROS action terminal states `SUCCEEDED`, `CANCELED`, and `ABORTED`. Invalid goals are rejected before execution.

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy
- `turtlesim`
- `colcon` and `rosdep`

Install ROS 2 Jazzy by following the official ROS documentation, then install the project dependencies:

```bash
sudo apt update
sudo apt install ros-jazzy-turtlesim python3-colcon-common-extensions python3-rosdep
```

## Clone and build

Create a workspace and clone this repository into its `src` directory:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/YOUR_GITHUB_USERNAME/ros2-square-patrol.git
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select turtle_patrol_interfaces turtle_patrol
source install/setup.bash
```

Run the final `source install/setup.bash` command in every new terminal used for this project.

## Run individual nodes

Start turtlesim:

```bash
ros2 run turtlesim turtlesim_node
```

Start the action server in a second terminal:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run turtle_patrol square_patrol_action_server
```

Send a goal from a third terminal. Set `cancel_after` to `0.0` to let the patrol finish:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run turtle_patrol square_patrol_action_client --ros-args \
  -p patrol_distance:=2.5 \
  -p laps:=2 \
  -p edge_number:=4 \
  -p cancel_after:=0.0
```

A positive `cancel_after` value requests cancellation after that many seconds:

```bash
ros2 run turtle_patrol square_patrol_action_client --ros-args \
  -p patrol_distance:=2.0 \
  -p laps:=3 \
  -p edge_number:=5 \
  -p cancel_after:=5.0
```

## Launch

Start turtlesim, the server, and the delayed client together:

```bash
ros2 launch turtle_patrol square_patrol.launch.py
```

Override any patrol parameter on the command line:

```bash
ros2 launch turtle_patrol square_patrol.launch.py \
  patrol_distance:=1.5 \
  laps:=3 \
  edge_number:=6 \
  cancel_after:=0.0
```

| Launch argument | Type | Default | Description |
| --- | --- | --- | --- |
| `patrol_distance` | float | `2.5` | Length of each polygon edge. |
| `laps` | integer | `2` | Number of complete laps. |
| `edge_number` | integer | `4` | Number of edges in the regular polygon. |
| `cancel_after` | float | `0.0` | Seconds before cancellation; values at or below zero disable automatic cancellation. |

## Test examples

Run the package tests:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon test --packages-select turtle_patrol_interfaces turtle_patrol
colcon test-result --verbose
```

Send a goal directly with the ROS 2 CLI to observe feedback and a `SUCCEEDED` result:

```bash
ros2 action send_goal --feedback \
  /square_patrol \
  turtle_patrol_interfaces/action/SquarePatrol \
  "{patrol_distance: 2.0, laps: 1, edge_number: 4}"
```

To test `CANCELED`, run the client with a positive `cancel_after` value. To test `ABORTED`, start the action server without turtlesim and send a valid goal; the server aborts because no turtle pose has been received.

## License

This project is licensed under the Apache License 2.0.
