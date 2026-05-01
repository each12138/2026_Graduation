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

    # 获取包路径
    go2_core_dir = get_package_share_directory('go2_core')
    go2_navigation_dir = get_package_share_directory('go2_navigation')
    go2_perception_dir = get_package_share_directory('go2_perception')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # 启动参数
    map_file_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            os.environ.get('HOME', '/home/unitree'), 'map', 'go2_slam_ninelab.yaml'
        ),
        description='Path to saved map yaml file'
    )
    
    rviz_enable_arg = DeclareLaunchArgument(
        'rviz_enable',
        default_value='true',
        description='Whether to enable RViz visualization'
    )

    map_file = LaunchConfiguration('map')
    rviz_enable = LaunchConfiguration('rviz_enable')

    # 配置文件路径
    rviz_config_path = os.path.join(go2_core_dir, 'config', 'nav_only.rviz')
    nav2_config = os.path.join(go2_navigation_dir, 'config', 'nav2_division.yaml')

    # 1. 机器人基础节点
    go2_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(go2_core_dir, 'launch', 'go2_base.launch.py')]),
        launch_arguments={
            'video_enable': 'false',
            'image_topic': '/camera/image_raw',
            'tcp_enable': 'true',
            'tcp_host': '127.0.0.1',
            'tcp_port': '5432',
            'target_fps': '30',
        }.items()
    )

    # 2. 点云处理
    pointcloud_process_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(go2_perception_dir, 'launch', 'go2_pointcloud_process.launch.py')])
    )

    # 3. 定位（map_server + amcl + lifecycle manager）
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(nav2_bringup_dir, 'launch', 'localization_launch.py')]),
        launch_arguments={
            'map': map_file,
            'params_file': nav2_config,
            'use_sim_time': 'false',
            'autostart': 'true',
            'use_lifecycle_mgr': 'true',
        }.items()
    )

    # 4. 导航
    go2_nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(
                'nav2_bringup'), 'launch', 'navigation_launch.py')
        ]),
        launch_arguments={
            'params_file': nav2_config,
            'use_sim_time': 'false',
            'autostart': 'true',
            'use_lifecycle_mgr': 'true',
            'map_subscribe_transient_local': 'true', #必须传入参数才能让nav2的map_server发布的map topic具有transient_local的latching特性，否则amcl无法正确获取地图数
        }.items(),
    )


    # 5. RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen',
        condition=IfCondition(rviz_enable)
    )

    # Add all actions to the launch description
    ld.add_action(map_file_arg)
    ld.add_action(rviz_enable_arg)
    ld.add_action(go2_base_launch)
    ld.add_action(pointcloud_process_launch)
    ld.add_action(localization_launch)
    ld.add_action(go2_nav2_launch)
    ld.add_action(rviz_node)

    return ld