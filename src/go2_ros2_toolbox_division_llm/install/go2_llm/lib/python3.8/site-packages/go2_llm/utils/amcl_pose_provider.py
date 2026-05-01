import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
import math
import time


"""
geometry_msgs.msg.PoseWithCovarianceStamped(header=std_msgs.msg.Header(stamp=builtin_interfaces.msg.Time(sec=1777547883, nanosec=504253959), frame_id='map'), pose=geometry_msgs.msg.PoseWithCovariance(pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=3.0862733854702276, y=3.676388341526121, z=0.0), orientation=geometry_msgs.msg.Quaternion(x=0.0, y=0.0, z=-0.939852863314486, w=0.34157955928240497)), covariance=array([ 2.29996155, -0.12814369,  0.        ,  0.        ,  0.        ,
        0.        , -0.12814369,  2.45824129,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        2.27383372])))
"""

def extract_amcl_pose_info(msg):
    pose = msg.pose.pose
    position = pose.position
    orientation = pose.orientation
    qx = float(orientation.x)
    qy = float(orientation.y)
    qz = float(orientation.z)
    qw = float(orientation.w)
    yaw = math.atan2(
        2.0 * (qw * qz + qx * qy),
        1.0 - 2.0 * (qy * qy + qz * qz),
    )

    return {
        "frame_id": msg.header.frame_id,
        "position": {
            "x": float(position.x),
            "y": float(position.y),
            "z": float(position.z),
        },
        "orientation": {
            "x": qx,
            "y": qy,
            "z": qz,
            "w": qw,
        },
        "yaw": float(yaw),
    }


class AmclPoseProvider(Node):
    def __init__(self):
        self._owns_rclpy = not rclpy.ok()
        if self._owns_rclpy:
            rclpy.init()
        super().__init__("go2_amcl_pose_provider")
        self.latest_pose = None
        self.create_subscription(
            PoseWithCovarianceStamped,
            "/amcl_pose",
            self._pose_callback,
            10,
        )

    def _pose_callback(self, msg):
        self.latest_pose = msg

    def get_pose(self, timeout_sec=None):
        start_time = time.monotonic()
        while rclpy.ok() and self.latest_pose is None:
            # 允许外部为首次定位设置等待上限，避免客户端无期限阻塞。
            if timeout_sec is not None and (time.monotonic() - start_time) >= timeout_sec:
                raise TimeoutError(
                    f"amcl_pose_not_received_within_{float(timeout_sec):.3f}s"
                )
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.latest_pose

    def get_pose_info(self, timeout_sec=None):
        return extract_amcl_pose_info(self.get_pose(timeout_sec=timeout_sec))

    def close(self):
        self.destroy_node()
        if self._owns_rclpy and rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    provider = AmclPoseProvider()
    try:
        print(provider.get_pose_info())
    finally:
        provider.close()
