# 快速开始 - GO2 ROS2 Toolbox

## 🚀 两种工作模式

### 📍 模式 1: SLAM 建图（先建图）

```bash
# 基础用法 - 使用默认配置
ros2 launch go2_core go2_mapping.launch.py

# 自定义地图保存路径
ros2 launch go2_core go2_mapping.launch.py map_save_path:=/home/ninelab227/maps/office_map

# 禁用 RViz 节省资源
ros2 launch go2_core go2_mapping.launch.py rviz_enable:=false
```

**操作流程：**
1. 启动命令
2. 遥控机器人在环境中移动（覆盖所有区域）
3. 在 RViz 中观察地图构建质量
4. 建图完成后按 `Ctrl+C` 停止
5. 地图自动保存到 `~/maps/go2_map.yaml`

---

### 🧭 模式 2: 定位导航（后导航）

```bash
# 加载地图并启动导航
ros2 launch go2_core go2_localization_nav.launch.py map_file:=/home/ninelab227/maps/office_map.yaml

# 禁用 RViz
ros2 launch go2_core go2_localization_nav.launch.py map_file:=/home/ninelab227/maps/office_map.yaml rviz_enable:=false
```

**操作流程：**
1. 启动命令（指定地图文件路径）
2. 在 RViz 中使用 **"2D Pose Estimate"** 设置机器人初始位置
3. 使用 **"2D Nav Goal"** 设置导航目标点
4. 机器人自动规划路径并导航

---

## 📝 完整工作流示例

### 第一次使用（建图）
```bash
# 1. 建图
ros2 launch go2_core go2_mapping.launch.py map_save_path:=/home/ninelab227/maps/my_office
```
→ 控制机器人探索环境 → 按 Ctrl+C 保存地图

### 后续使用（导航）
```bash
# 2. 导航
ros2 launch go2_core go2_localization_nav.launch.py map_file:=/home/ninelab227/maps/my_office.yaml
```
→ 设置初始位置 → 设置目标点 → 自动导航

---

## 🎯 常用参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `map_save_path` | 建图时保存路径（不含扩展名） | `~/maps/go2_map` | `/home/user/maps/office` |
| `map_file` | 导航时地图文件路径（.yaml） | 必需参数 | `/home/user/maps/office.yaml` |
| `rviz_enable` | 是否启用 RViz | `true` | `true` / `false` |

---

## 🔧 多地图管理

```bash
# 为不同环境创建地图
ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/office
ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/home
ros2 launch go2_core go2_mapping.launch.py map_save_path:=~/maps/warehouse

# 根据需要加载对应地图
ros2 launch go2_core go2_localization_nav.launch.py map_file:=~/maps/office.yaml
ros2 launch go2_core go2_localization_nav.launch.py map_file:=~/maps/home.yaml
```

---

## ⚠️ 注意事项

1. **建图质量**
   - 移动速度适中，不要太快
   - 覆盖所有区域（包括角落）
   - 确保传感器正常工作

2. **定位初始化**
   - 启动导航后必须先用 "2D Pose Estimate" 设置初始位置
   - 初始位置应尽量接近机器人实际位置

3. **地图文件**
   - 建图后生成两个文件：`.yaml`（配置）和 `.pgm`（图像）
   - 导航时只需指定 `.yaml` 文件

4. **旧版启动文件**
   - `go2_startup.launch.py` - 完整系统启动（包含 SLAM+Nav，不推荐）
   - `go2_slam_startup.launch.py` - SLAM 启动（旧版）
   - `go2_nav_startup.launch.py` - 导航启动（旧版）
   - **推荐使用新的 `go2_mapping.launch.py` 和 `go2_localization_nav.launch.py`**

---

## 📚 详细文档

查看完整使用指南：[USAGE_GUIDE.md](USAGE_GUIDE.md)

---

## 🆘 快速故障排除

| 问题 | 解决方案 |
|------|----------|
| 建图质量差 | 降低移动速度，确保覆盖所有区域 |
| 定位失败 | 使用 "2D Pose Estimate" 重新设置初始位置 |
| 导航不移动 | 检查代价地图配置，确认无障碍物困住机器人 |
| 找不到地图文件 | 检查路径是否正确，确保 `.yaml` 文件存在 |

---

**祝使用愉快！🤖**
