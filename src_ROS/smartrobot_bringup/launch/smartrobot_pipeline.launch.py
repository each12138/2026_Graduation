from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="smartrobot_bringup",
                executable="smartrobot_pipeline",
                name="smartrobot_pipeline",
                output="screen",
            )
        ]
    )
