# SmartRobot ROS2 工作区说明

`src_ROS` 是 SmartRobot 的 ROS2 Python 工作区，负责把用户输入、LLM 决策、技能执行、状态读取和地点记忆串成一条完整流程。

## 包结构

- `smartrobot_voice_input`：键盘输入和 Whisper 语音识别输入。
- `smartrobot_agent_controller`：调用 LLM，根据用户任务、机器人状态和地点记忆生成动作包。
- `smartrobot_skill_controller`：执行动作包，封装 Unitree GO2 动作和导航目标发送。
- `smartrobot_state_client`：读取机器人状态，默认从 `/amcl_pose` 获取全局位姿。
- `smartrobot_place_memory`：保存和读取命名地点。
- `smartrobot_bringup`：主流程入口，编排 `voice -> agent -> skills`。

## 主流程

```text
用户输入 -> Agent 决策 -> 技能执行
              ↑
        状态读取 / 地点记忆
```

导航相关的 `go_to()` 通过 TCP 把目标点发送给 `navigation_command_tcpbridge.py`，当前语义是“目标已发送”，不会等待机器人实际抵达目标点后再返回。

## 简便启动命令

以下命令使用默认环境变量：

- 导航 TCP 地址：`127.0.0.1:5432`
- 导航坐标系：`map`
- 全局位姿话题：`/amcl_pose`
- 默认输入方式：键盘输入

### 终端 1：启动导航 / Nav2

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/Graduation/go2_ros2_toolbox_division
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_core go2_localization_nav.launch.py
```

如果需要使用完整启动流程，也可以改用：

```bash
ros2 launch go2_core go2_startup.launch.py
```

### 终端 2：启动 TCP Bridge

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/Graduation/go2_ros2_toolbox_division
source install/setup.bash
python3 src/go2_ros2_toolbox_division/go2_navigation/go2_navigation/navigation_command_tcpbridge.py
```

### 终端 3：启动 SmartRobot Pipeline

键盘输入：

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/Graduation/2026_Graduation/src_ROS
colcon build --symlink-install
source install/setup.bash
ros2 run smartrobot_bringup smartrobot_pipeline
```

语音输入：

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/Graduation/2026_Graduation/src_ROS
colcon build --symlink-install
source install/setup.bash
SMARTROBOT_USE_WHISPER=1 ros2 run smartrobot_bringup smartrobot_pipeline
```

如果需要指定 Unitree 网卡，例如 `eth0`：

```bash
ros2 run smartrobot_bringup smartrobot_pipeline eth0
```

## 推荐启动顺序

```text
1. 启动导航 / Nav2
2. 启动 TCP Bridge
3. 启动 SmartRobot Pipeline
```

## 常用检查命令

查看全局位姿：

```bash
ros2 topic echo /amcl_pose
```

查看 Nav2 action：

```bash
ros2 action list
ros2 action info /navigate_to_pose
```

查看当前 ROS 包是否被识别：

```bash
ros2 pkg list | grep smartrobot
```

## 主要环境变量

通常不需要手动设置，默认值如下：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SMARTROBOT_USE_WHISPER` | `0` | 是否启用 Whisper 语音输入 |
| `GO2_NAV_HOST` | `127.0.0.1` | SmartRobot 发送导航目标的 TCP 地址 |
| `GO2_NAV_PORT` | `5432` | SmartRobot 发送导航目标的 TCP 端口 |
| `GO2_NAV_FRAME` | `map` | 导航目标坐标系 |
| `GO2_GLOBAL_POSE_ENABLE` | `1` | 是否读取全局位姿 |
| `GO2_GLOBAL_POSE_TOPIC` | `/amcl_pose` | 全局位姿话题 |
| `GO2_GLOBAL_POSE_TIMEOUT` | `2.0` | 位姿超时时间 |
| `GO2_NAV_TCP_HOST` | `127.0.0.1` | TCP Bridge 监听地址 |
| `GO2_NAV_TCP_PORT` | `5432` | TCP Bridge 监听端口 |
| `GO2_NAV_FRAME_ID` | `map` | TCP Bridge 默认导航坐标系 |

## 编译检查

```bash
python3 -m compileall -q .
```
