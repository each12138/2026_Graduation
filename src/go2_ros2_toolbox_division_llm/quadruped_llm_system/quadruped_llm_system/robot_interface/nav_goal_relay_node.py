import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String

from quadruped_llm_system.common.events import make_event
from quadruped_llm_system.common.ros_json_topic import json_msg


class NavGoalRelayNode(Node):
    def __init__(self) -> None:
        super().__init__("nav_goal_relay_node")

        self.sub_goal = self.create_subscription(PoseStamped, "/goal_pose", self._on_goal, 10)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)

        self.active_request_id = ""
        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)

        self.get_logger().info("Nav goal relay ready. Using simulated navigation result.")

    def _on_event(self, msg: String) -> None:
        try:
            import json
            payload = json.loads(msg.data)
        except Exception:
            return
        if isinstance(payload, dict) and payload.get("type") == "nav_start":
            self.active_request_id = str(payload.get("request_id", "")).strip()

    def _on_goal(self, msg: PoseStamped) -> None:
        self.get_logger().info(
            f"goal received x={msg.pose.position.x:.2f} y={msg.pose.position.y:.2f}"
        )
        time.sleep(3.0)
        self.pub_events.publish(
            json_msg(
                make_event(
                    "nav_goal_succeeded",
                    source="nav_goal_relay",
                    request_id=self.active_request_id,
                )
            )
        )


def main() -> None:
    rclpy.init()
    node = NavGoalRelayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
