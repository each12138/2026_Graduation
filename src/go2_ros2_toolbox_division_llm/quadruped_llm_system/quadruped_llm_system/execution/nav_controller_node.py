import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped

from quadruped_llm_system.common.config import load_yaml, config_dir
from quadruped_llm_system.common.events import make_event
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg
from quadruped_llm_system.cognition.place_repository import PlaceRepository


class NavControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("nav_controller_node")

        self.runtime_cfg = load_yaml("runtime.yaml")
        self.places = PlaceRepository("destinations.yaml", config_dir() / "memory_points.json")

        nav_cfg = self.runtime_cfg.get("navigation", {})
        self.ack_timeout_s = float(nav_cfg.get("ack_timeout_s", 20.0))
        self.result_timeout_s = float(nav_cfg.get("result_timeout_s", 90.0))

        self.mode = "IDLE"
        self.pending_request_id = ""
        self.pending_destination_id = ""
        self.active_request_id = ""
        self.active_destination_id = ""
        self.active_started_at = 0.0

        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)
        self.pub_goal = self.create_publisher(PoseStamped, "/goal_pose", 10)

        self.timer = self.create_timer(0.2, self._watchdog)

        self.get_logger().info("Nav controller ready.")

    def _publish_event(self, payload: dict) -> None:
        self.pub_events.publish(json_msg(payload))

    def _send_goal(self, dest_id: str) -> None:
        pose_dict = self.places.pose_stamped_dict(dest_id)
        msg = PoseStamped()
        msg.header.frame_id = pose_dict["header"]["frame_id"]
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = float(pose_dict["pose"]["position"]["x"])
        msg.pose.position.y = float(pose_dict["pose"]["position"]["y"])
        msg.pose.position.z = 0.0
        msg.pose.orientation.x = float(pose_dict["pose"]["orientation"]["x"])
        msg.pose.orientation.y = float(pose_dict["pose"]["orientation"]["y"])
        msg.pose.orientation.z = float(pose_dict["pose"]["orientation"]["z"])
        msg.pose.orientation.w = float(pose_dict["pose"]["orientation"]["w"])
        self.pub_goal.publish(msg)

    def _on_event(self, msg: String) -> None:
        payload = parse_json_msg(msg)
        if not payload:
            return

        ev_type = str(payload.get("type", "")).strip()
        request_id = str(payload.get("request_id", "")).strip()

        if ev_type == "nav_ack_requested":
            self.mode = "AWAITING_ACK_PLAYBACK"
            self.pending_request_id = request_id
            self.pending_destination_id = str(payload.get("destination_id", "")).strip()
            return

        if ev_type == "speech_done" and str(payload.get("speech_kind", "")) == "nav_ack":
            if self.mode != "AWAITING_ACK_PLAYBACK" or request_id != self.pending_request_id:
                return
            self.active_request_id = self.pending_request_id
            self.active_destination_id = self.pending_destination_id
            self.active_started_at = time.monotonic()
            self.mode = "AWAITING_NAV_RESULT"
            dest = self.places.get(self.active_destination_id)
            self._publish_event(
                make_event(
                    "nav_start",
                    source="nav_controller",
                    request_id=self.active_request_id,
                    destination_id=self.active_destination_id,
                    destination_name=dest["name"],
                )
            )
            self._send_goal(self.pending_destination_id)
            self.pending_request_id = ""
            self.pending_destination_id = ""
            return

        if ev_type in {"nav_goal_succeeded", "nav_goal_failed", "nav_goal_canceled"}:
            if self.mode != "AWAITING_NAV_RESULT":
                return
            if request_id and request_id != self.active_request_id:
                return

            event_map = {
                "nav_goal_succeeded": "nav_succeeded",
                "nav_goal_failed": "nav_failed",
                "nav_goal_canceled": "nav_canceled",
            }
            result_ev = event_map[ev_type]
            dest = self.places.get(self.active_destination_id)
            self._publish_event(
                make_event(
                    result_ev,
                    source="nav_controller",
                    request_id=self.active_request_id,
                    destination_id=self.active_destination_id,
                    destination_name=dest["name"],
                    resolved_by="relay",
                )
            )
            self.mode = "IDLE"
            self.active_request_id = ""
            self.active_destination_id = ""
            self.active_started_at = 0.0
            return

    def _watchdog(self) -> None:
        if self.mode == "AWAITING_NAV_RESULT" and self.active_started_at > 0.0:
            if (time.monotonic() - self.active_started_at) > self.result_timeout_s:
                dest = self.places.get(self.active_destination_id)
                self._publish_event(
                    make_event(
                        "nav_failed",
                        source="nav_controller",
                        request_id=self.active_request_id,
                        destination_id=self.active_destination_id,
                        destination_name=dest["name"],
                        resolved_by="timeout",
                        reason="navigation_timeout",
                    )
                )
                self.mode = "IDLE"
                self.active_request_id = ""
                self.active_destination_id = ""
                self.active_started_at = 0.0


def main() -> None:
    rclpy.init()
    node = NavControllerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
