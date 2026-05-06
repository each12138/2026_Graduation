import time
from typing import Optional

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.events import make_event
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg


class NavGoalRelayNode(Node):
    def __init__(self) -> None:
        super().__init__("nav_goal_relay_node")

        self.sub_goal = self.create_subscription(PoseStamped, "/goal_pose", self._on_goal, 10)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)
        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)

        self._action_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        self.active_request_id = ""
        self.active_destination_id = ""
        self.active_destination_name = ""

        self.server_timeout_s = 5.0
        self.result_timeout_s = 120.0
        self.goal_response_timeout_s = 10.0

        self.get_logger().info("Nav goal relay ready. Using real NavigateToPose action.")

    def _on_event(self, msg: String) -> None:
        payload = parse_json_msg(msg)
        if not payload:
            return

        if str(payload.get("type", "")).strip() != "nav_start":
            return

        self.active_request_id = str(payload.get("request_id", "")).strip()
        self.active_destination_id = str(payload.get("destination_id", "")).strip()
        self.active_destination_name = str(payload.get("destination_name", "")).strip()

    def _publish_nav_result(self, event_type: str, reason: str = "") -> None:
        self.pub_events.publish(
            json_msg(
                make_event(
                    event_type,
                    source="nav_goal_relay",
                    request_id=self.active_request_id,
                    destination_id=self.active_destination_id,
                    destination_name=self.active_destination_name,
                    reason=reason,
                )
            )
        )

    def _wait_for_future(self, future, timeout_sec: float):
        deadline = time.time() + timeout_sec
        while rclpy.ok() and time.time() < deadline:
            if future.done():
                return future.result()
            time.sleep(0.05)
        return None

    def _status_to_event(self, status: int) -> str:
        if status == GoalStatus.STATUS_SUCCEEDED:
            return "nav_goal_succeeded"
        if status == GoalStatus.STATUS_CANCELED:
            return "nav_goal_canceled"
        return "nav_goal_failed"

    def _on_goal(self, msg: PoseStamped) -> None:
        self.get_logger().info(
            "goal received x={0:.2f} y={1:.2f} request_id={2}".format(
                msg.pose.position.x,
                msg.pose.position.y,
                self.active_request_id or "unknown",
            )
        )

        if not self._action_client.wait_for_server(timeout_sec=self.server_timeout_s):
            self.get_logger().error("navigate_to_pose action server not available")
            self._publish_nav_result("nav_goal_failed", "action_server_unavailable")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = msg

        send_goal_future = self._action_client.send_goal_async(goal_msg)
        goal_handle = self._wait_for_future(send_goal_future, self.goal_response_timeout_s)

        if goal_handle is None:
            self.get_logger().error("Goal response timed out")
            self._publish_nav_result("nav_goal_failed", "goal_response_timeout")
            return

        if not goal_handle.accepted:
            self.get_logger().warning("Goal rejected by action server")
            self._publish_nav_result("nav_goal_failed", "goal_rejected")
            return

        self.get_logger().info("Goal accepted by NavigateToPose")

        result_future = goal_handle.get_result_async()
        result = self._wait_for_future(result_future, self.result_timeout_s)

        if result is None:
            self.get_logger().error("Navigation result timed out")
            try:
                goal_handle.cancel_goal_async()
            except Exception:
                pass
            self._publish_nav_result("nav_goal_failed", "result_timeout")
            return

        event_type = self._status_to_event(result.status)
        self.get_logger().info("Navigation finished with status={0}".format(result.status))
        self._publish_nav_result(event_type)

    def destroy_node(self):
        self._action_client.destroy()
        super().destroy_node()


def main() -> None:
    rclpy.init()
    node = NavGoalRelayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
