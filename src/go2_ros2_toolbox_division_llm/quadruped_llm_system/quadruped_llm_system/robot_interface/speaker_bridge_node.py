import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.config import load_yaml
from quadruped_llm_system.common.events import make_event
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg


class SpeakerBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("speaker_bridge_node")

        runtime_cfg = load_yaml("runtime.yaml")
        speaker_cfg = runtime_cfg.get("speaker", {})
        self.simulated_playback_sec = float(speaker_cfg.get("simulated_playback_sec", 1.2))

        self.sub_audio = self.create_subscription(String, "/to_human_audio", self._on_audio, 20)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)

        self.get_logger().info("Speaker bridge ready. Using simulated playback.")

    def _on_audio(self, msg: String) -> None:
        payload = parse_json_msg(msg)
        if not payload:
            return

        stream_id = str(payload.get("stream_id", "")).strip()
        request_id = str(payload.get("request_id", "")).strip()
        speech_kind = str(payload.get("speech_kind", "general")).strip()
        text = str(payload.get("text", "")).strip()

        self.get_logger().info(f"[speak:{speech_kind}] {text}")
        time.sleep(self.simulated_playback_sec)

        self.pub_events.publish(
            json_msg(
                make_event(
                    "speech_done",
                    source="speaker_bridge",
                    request_id=request_id,
                    speech_kind=speech_kind,
                    stream_id=stream_id,
                )
            )
        )


def main() -> None:
    rclpy.init()
    node = SpeakerBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
