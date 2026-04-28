import os
import sys
import time
import threading

from unitree_sdk2py.core.channel import ChannelFactoryInitialize


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


class _GlobalPoseReader:
    """从 ROS2 全局位姿话题读取机器人最新位姿。"""

    def __init__(self):
        self.enabled = _env_flag("GO2_GLOBAL_POSE_ENABLE", True)
        self.topic = os.getenv("GO2_GLOBAL_POSE_TOPIC", "/amcl_pose")
        self.timeout_sec = float(os.getenv("GO2_GLOBAL_POSE_TIMEOUT", "1.0"))
        self.default_frame = os.getenv("GO2_NAV_FRAME", "map").strip() or "map"
        self._latest = None
        self._latest_time = 0.0
        self._alive = False
        self._thread = None
        self._lock = threading.Lock()

        if not self.enabled:
            return
        self._alive = True
        self._thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._thread.start()

    def _spin_loop(self):
        try:
            import rclpy
            from rclpy.node import Node
            from geometry_msgs.msg import PoseWithCovarianceStamped
        except Exception:
            self.enabled = False
            self._alive = False
            return

        node = None
        try:
            if not rclpy.ok():
                rclpy.init(args=None)

            class _PoseNode(Node):
                def __init__(self, owner):
                    super().__init__("smartrobot_global_pose_reader")
                    self._owner = owner
                    self.create_subscription(
                        PoseWithCovarianceStamped,
                        owner.topic,
                        self._on_pose,
                        10,
                    )

                def _on_pose(self, msg):
                    pose = msg.pose.pose
                    frame_id = (msg.header.frame_id or "").strip() or self._owner.default_frame
                    payload = {
                        "frame_id": frame_id,
                        "position": {
                            "x": float(pose.position.x),
                            "y": float(pose.position.y),
                            "z": float(pose.position.z),
                        },
                        "orientation": {
                            "x": float(pose.orientation.x),
                            "y": float(pose.orientation.y),
                            "z": float(pose.orientation.z),
                            "w": float(pose.orientation.w),
                        },
                        "source": "amcl_pose",
                    }
                    with self._owner._lock:
                        self._owner._latest = payload
                        self._owner._latest_time = time.time()

            node = _PoseNode(self)
            while self._alive:
                rclpy.spin_once(node, timeout_sec=0.1)
        except Exception:
            self.enabled = False
        finally:
            self._alive = False
            if node is not None:
                try:
                    node.destroy_node()
                except Exception:
                    pass

    def get_state(self):
        if not self.enabled:
            return None
        with self._lock:
            if self._latest is None:
                return None
            if (time.time() - self._latest_time) > self.timeout_sec:
                return None
            return dict(self._latest)

    def close(self):
        self._alive = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)


class StateReader:
    """对外提供机器人状态读取接口。"""

    def __init__(self):
        self.global_reader = _GlobalPoseReader()

    def get_state(self):
        return self.global_reader.get_state()

    def close(self):
        self.global_reader.close()


def main():
    network_interface = sys.argv[1] if len(sys.argv) > 1 else None
    if network_interface:
        ChannelFactoryInitialize(0, network_interface)
    else:
        ChannelFactoryInitialize(0)

    reader = StateReader()
    print("state reader started...")
    try:
        while True:
            state = reader.get_state()
            if state is not None:
                print(state)
            time.sleep(1.0)
    finally:
        reader.close()


if __name__ == "__main__":
    main()
