from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    ld = LaunchDescription()

    go2_core_dir = get_package_share_directory('go2_core')
    go2_perception_dir = get_package_share_directory('go2_perception')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    go2_navigation_dir = get_package_share_directory('go2_navigation')

    map_file_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            os.environ.get('HOME', '/home/unitree'),
            'map',
            'go2_slam_ninelab.yaml'
        ),
        description='Full path to map yaml file'
    )

    rviz_enable_arg = DeclareLaunchArgument(
        'rviz_enable',
        default_value='true',
        description='Whether to enable RViz'
    )

    map_file = LaunchConfiguration('map')
    rviz_enable = LaunchConfiguration('rviz_enable')

    nav2_config = os.path.join(go2_navigation_dir, 'config', 'nav2_params.yaml')
    rviz_config_path = os.path.join(go2_core_dir, 'config', 'nav_only.rviz')

    go2_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(go2_core_dir, 'launch', 'go2_base.launch.py')
        ]),
        launch_arguments={
            'video_enable': 'false',
            'image_topic': '/camera/image_raw',
            'tcp_enable': 'true',
            'tcp_host': '127.0.0.1',
            'tcp_port': '5432',
            'target_fps': '30',
        }.items()
    )

    pointcloud_process_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(go2_perception_dir, 'launch', 'go2_pointcloud_process.launch.py')
        ])
    )

    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ]),
        launch_arguments={
            'slam': 'False',
            'map': map_file,
            'use_sim_time': 'false',
            'params_file': nav2_config,
            'autostart': 'true',
        }.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen',
        condition=IfCondition(rviz_enable)
    )

    ld.add_action(map_file_arg)
    ld.add_action(rviz_enable_arg)
    ld.add_action(go2_base_launch)
    ld.add_action(pointcloud_process_launch)
    ld.add_action(nav2_bringup_launch)
    ld.add_action(rviz_node)

    return ld