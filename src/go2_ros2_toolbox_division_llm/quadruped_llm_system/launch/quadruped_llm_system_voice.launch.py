from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="quadruped_llm_system",
                executable="text_bridge_node",
                name="text_bridge_node",
                output="screen",
            ),
            Node(
                package="quadruped_llm_system",
                executable="dialogue_router_node",
                name="dialogue_router_node",
                output="screen",
            ),
            Node(
                package="quadruped_llm_system",
                executable="response_generator_node",
                name="response_generator_node",
                output="screen",
            ),
            Node(
                package="quadruped_llm_system",
                executable="speaker_bridge_node",
                name="speaker_bridge_node",
                output="screen",
            ),
            Node(
                package="quadruped_llm_system",
                executable="nav_controller_node",
                name="nav_controller_node",
                output="screen",
            ),
            Node(
                package="quadruped_llm_system",
                executable="nav_goal_relay_node",
                name="nav_goal_relay_node",
                output="screen",
            ),
        ]
    )
