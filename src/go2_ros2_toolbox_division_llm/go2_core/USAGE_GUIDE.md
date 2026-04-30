# GO2 ROS2 Toolbox 使用指南

## 流程说明

本工具箱现在支持两种独立的工作模式：

### 1. SLAM 建图模式（Mapping Mode）
先使用 SLAM 算法构建环境地图，并保存到本地。

### 2. 定位导航模式（Localization & Navigation Mode）
加载已保存的地图，进行 AMCL 定位和自主导航。

---

## 使用方法

### 模式一：SLAM 建图

**启动命令：**
```bash
ros2 launch go2_core go2_mapping.launch.py
```

**可选参数：**
- `map_save_path`: 地图保存路径（不含文件扩展名）
  - 默认值：`~/maps/go2_map`
  - 示例：`map_save_path:=/home/user/maps/my_office`
  
- `rviz_enable`: 是否启用 RViz 可视化
  - 默认值：`true`
  - 示例：`rviz_enable:=false`

**完整示例：**
```bash
# 使用默认配置建图
ros2 launch go2_core go2_mapping.launch.py

# 自定义地图保存路径
ros2 launch go2_core go2_mapping.launch.py map_save_path:=/home/ninelab227/maps/office_map

# 禁用 RViz 以节省资源
ros2 launch go2_core go2_mapping.launch.py rviz_enable:=false

# 完整配置
ros2 launch go2_core go2_mapping.launch.py map_save_path:=/home/ninelab227/maps/office_map rviz_enable:=true
```

**建图流程：**
1. 启动机器人基础节点（视频流、TCP 通信）
2. 启动点云处理节点
3. 启动 SLAM Toolbox（建图模式）
4. 启动 RViz 可视化（可选）
5. 控制机器人在环境中移动，SLAM 会自动构建地图
6. 建图完成后，地图会自动保存到指定路径

**保存的地图文件：**
- `go2_map.yaml` - 地图配置文件
- `go2_map.pgm` - 地图图像文件

**注意事项：**
- 建图过程中应缓慢、全面地移动机器人，确保覆盖所有区域
- 可以通过 RViz 观察地图构建质量
- 建图完成后按 Ctrl+C 停止，地图会自动保存

---

### 模式二：定位导航

**启动命令：**
```bash
ros2 launch go2_core go2_localization_nav.launch.py map_file:=<地图文件路径>
```

**必需参数：**
- `map_file`: 已保存的地图文件路径（.yaml 格式）
  - 示例：`map_file:=/home/ninelab227/maps/office_map.yaml`

**可选参数：**
- `rviz_enable`: 是否启用 RViz 可视化
  - 默认值：`true`
  - 示例：`rviz_enable:=false`

**完整示例：**
```bash
# 加载地图并启动导航
ros2 launch go2_core go2_localization_nav.launch.py map_file:=/home/ninelab227/maps/office_map.yaml

# 禁用 RViz
ros2 launch go2_core go2_localization_nav.launch.py map_file:=/home/ninelab227/maps/office_map.yaml rviz_enable:=false
```

**导航流程：**
1. 启动机器人基础节点
2. 启动点云处理节点
3. 加载已保存的地图（map_server）
4. 启动 AMCL 定位
5. 启动 Nav2 导航系统
6. 启动 RViz 可视化（可选）

**使用导航功能：**
1. 在 RViz 中使用 "2D Pose Estimate" 工具设置机器人初始位置
2. 使用 "2D Nav Goal" 工具设置导航目标点
3. 机器人将自动规划路径并导航到目标点

---

## 启动的节点说明

### 建图模式（go2_mapping.launch.py）

| 节点 | 功能 |
|------|------|
| go2_base | 机器人基础控制、视频流、TCP 通信 |
| pointcloud_process | 点云数据处理 |
| slam_toolbox | SLAM 建图算法 |
| map_saver | 地图保存服务 |
| rviz2 | 可视化工具（可选） |

### 定位导航模式（go2_localization_nav.launch.py）

| 节点 | 功能 |
|------|------|
| go2_base | 机器人基础控制、视频流、TCP 通信 |
| pointcloud_process | 点云数据处理 |
| map_server | 加载已保存的地图 |
| amcl | 自适应蒙特卡洛定位 |
| nav2 | 导航规划与控制 |
| rviz2 | 可视化工具（可选） |

---

## 常见问题

### Q1: 建图质量不好怎么办？
- 确保机器人移动速度适中（不要太快）
- 尽量覆盖所有区域，包括角落
- 确保传感器（激光雷达/深度相机）工作正常
- 在特征丰富的环境中建图效果更好

### Q2: 定位失败或漂移严重？
- 检查地图文件路径是否正确
- 使用 "2D Pose Estimate" 重新设置机器人初始位置
- 确保当前环境与建图时变化不大
- 检查传感器数据是否正常发布

### Q3: 导航时机器人不移动？
- 检查代价地图（costmap）配置
- 确认局部和全局规划器参数设置正确
- 检查机器人是否被障碍物困住
- 查看终端输出是否有错误信息

### Q4: 如何修改地图保存路径？
```bash
ros2 launch go2_core go2_mapping.launch.py map_save_path:=/your/custom/path/map_name
```

---

## 文件结构

```
go2_core/launch/
├── go2_base.launch.py           # 基础启动文件
├── go2_mapping.launch.py        # SLAM 建图启动文件（新增）
├── go2_localization_nav.launch.py  # 定位导航启动文件（新增）
├── go2_startup.launch.py        # 完整系统启动（旧版）
├── go2_slam_startup.launch.py   # SLAM 启动（旧版）
└── go2_nav_startup.launch.py    # 导航启动（旧版）
```

---

## 推荐工作流程

1. **首次使用：**
   ```bash
   # 步骤 1: 建图
   ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/my_home
   
   # 步骤 2: 导航（下次使用时）
   ros2 launch go2_core go2_localization_nav.launch.py map_file:=~/maps/my_home.yaml
   ```

2. **多地图管理：**
   ```bash
   # 为不同环境创建不同地图
   ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/office
   ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/home
   ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/warehouse
   
   # 根据需要加载对应地图
   ros2 launch go2_core go2_localization_nav.launch.py map_file:=~/maps/office.yaml
   ```

---

## 技术支持

如有问题，请参考：
- ROS2 Nav2 官方文档：https://navigation.ros.org/
- SLAM Toolbox 文档：https://github.com/SteveMacenski/slam_toolbox
- Unitree GO2 文档：https://support.unitree.com/
