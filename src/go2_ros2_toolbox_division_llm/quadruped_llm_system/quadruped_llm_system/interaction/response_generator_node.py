from typing import Any, Dict, Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.config import load_yaml
from quadruped_llm_system.common.events import new_request_id
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg


class ResponseGeneratorNode(Node):
    def __init__(self) -> None:
        super().__init__("response_generator_node")

        self.runtime_cfg = load_yaml("runtime.yaml")

        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)
        self.pub_text = self.create_publisher(String, "/to_human_text", 10)
        self.pub_audio = self.create_publisher(String, "/to_human_audio", 10)

        self.get_logger().info("Response generator ready.")

    def _publish_text(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.pub_text.publish(msg)

    def _publish_audio_packet(self, text: str, speech_kind: str, request_id: str) -> None:
        payload = {
            "type": "final",
            "stream_id": new_request_id("stream"),
            "speech_kind": speech_kind,
            "request_id": request_id,
            "text": text,
        }
        self.pub_audio.publish(json_msg(payload))

    def _render(self, payload: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        ev_type = str(payload.get("type", "")).strip()

        if ev_type == "nav_ack_requested":
            return ("好的，现在带你去 {0}。".format(payload.get("destination_name", "目标点")), "nav_ack")

        if ev_type == "nav_clarification_needed":
            cands = payload.get("candidates", [])
            names = [str(x.get("name", "")).strip() for x in cands if isinstance(x, dict)]
            return ("你是想去 {0} 吗？请直接说名称或者编号。".format(", ".join(names)), "nav_clarification")

        if ev_type == "nav_clarification_timeout":
            return ("我暂时没有确认你的目标地点，请再说一遍。", "nav_clarification")

        if ev_type == "nav_unresolved":
            return ("我没能理解你要去哪里，请换一种说法。", "nav_clarification")

        if ev_type == "nav_succeeded":
            return ("已经到达 {0}。接下来需要我做什么？".format(payload.get("destination_name", "目标点")), "nav_result")

        if ev_type in {"nav_failed", "nav_canceled"}:
            return ("前往 {0} 的导航没有完成。你可以让我重试或换一个目标。".format(payload.get("destination_name", "目标点")), "nav_result")

        if ev_type == "general_response_requested":
            utterance = str(payload.get("utterance", "")).strip()
            return ("我收到了你的指令：{0}。当前演示系统优先处理导航类任务。".format(utterance), "general")

        return None

    def _on_event(self, msg: String) -> None:
        payload = parse_json_msg(msg)
        if not payload:
            return

        rendered = self._render(payload)
        if rendered is None:
            return

        text, speech_kind = rendered
        request_id = str(payload.get("request_id", "")).strip()
        self._publish_text(text)
        self._publish_audio_packet(text, speech_kind, request_id)
        self.get_logger().info("spoken_text={0}".format(text))


def main() -> None:
    rclpy.init()
    node = ResponseGeneratorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
