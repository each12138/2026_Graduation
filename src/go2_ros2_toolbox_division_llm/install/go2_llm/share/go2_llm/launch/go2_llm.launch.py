from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="go2_llm",
                executable="main.py",
                name="go2_llm_node",
                output="screen",
            )
        ]
    )
