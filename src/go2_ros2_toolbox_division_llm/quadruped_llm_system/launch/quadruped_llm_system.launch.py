from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            # 用户输入节点
            Node(
                package="quadruped_llm_system",
                executable="text_input_node",
                name="text_input_node",
                output="screen",
            ),
            # 对话路由节点，负责将用户输入分发给不同的处理模块（如导航、对话等）
            Node(
                package="quadruped_llm_system",
                executable="dialogue_router_node",
                name="dialogue_router_node",
                output="screen",
            ),
            # 响应生成节点
            Node(
                package="quadruped_llm_system",
                executable="response_generator_node",
                name="response_generator_node",
                output="screen",
            ),
            # 语音合成桥接节点，将文本响应转换为语音输出
            Node(
                package="quadruped_llm_system",
                executable="speaker_bridge_node",
                name="speaker_bridge_node",
                output="screen",
            ),
            # 导航控制节点
            Node(
                package="quadruped_llm_system",
                executable="nav_controller_node",
                name="nav_controller_node",
                output="screen",
            ),
            # 导航目标转发节点，负责将导航指令从对话系统转发给导航控制器
            Node(
                package="quadruped_llm_system",
                executable="nav_goal_relay_node",
                name="nav_goal_relay_node",
                output="screen",
            ),
        ]
    )
