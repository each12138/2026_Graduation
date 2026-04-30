from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    ld = LaunchDescription()

    # 获取slam_toolbox包的路径
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')
    
    # 设置配置文件路径
    slam_toolbox_config = os.path.join(
        get_package_share_directory('go2_slam'),
        'config',
        'mapper_params_online_slam.yaml'
    )

    # 声明启动参数
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='mapping',
        description='SLAM mode: mapping or localization'
    )
    
    mode = LaunchConfiguration('mode')

    
    # 创建两个互斥的启动组：一个用于加载已有地图，另一个用于新建地图
    # 如果 load_map 为空字符串，则不加载地图；否则加载指定地图
    
    # # 带地图加载的 slam_toolbox 启动
    # slam_with_map = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([
    #         os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
    #     ]),
    #     launch_arguments={
    #         'params_file': slam_toolbox_config,
    #         'use_sim_time': 'false',
    #         'mode': mode,
    #         'slam_toolbox.map_file_name': load_map,
    #     }.items(),
    #     condition=IfCondition(load_map)
    # )

    # 不带地图加载的 slam_toolbox 启动（新建地图）
    slam_without_map = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
        ]),
        launch_arguments={
            'params_file': slam_toolbox_config,
            'use_sim_time': 'false',
            'mode': mode,
        }.items()
    )
    
    ld.add_action(mode_arg)
    ld.add_action(slam_without_map)
    
    return ld