import re
from typing import Any, Dict, List, Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.config import config_dir, load_yaml
from quadruped_llm_system.common.events import make_event, new_request_id
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg
from quadruped_llm_system.cognition.llm_client import LLMClient
from quadruped_llm_system.cognition.place_repository import PlaceRepository


class DialogueRouterNode(Node):
    def __init__(self) -> None:
        super().__init__("dialogue_router_node")

        self.runtime_cfg = load_yaml("runtime.yaml")
        self.places = PlaceRepository("destinations.yaml", config_dir() / "memory_points.json")
        self.llm = LLMClient(self.runtime_cfg)

        dialogue_cfg = self.runtime_cfg.get("dialogue", {})
        self.nav_conf_threshold = float(dialogue_cfg.get("nav_confidence_threshold", 0.72))
        self.nav_match_threshold = float(dialogue_cfg.get("nav_match_threshold", 0.45))
        self.max_candidates = int(dialogue_cfg.get("max_candidates", 3))
        self.max_clarify_turns = int(dialogue_cfg.get("max_clarify_turns", 2))

        self.mode = "IDLE"
        self.clarify_candidates = []  # type: List[str]
        self.clarify_turn = 0

        self.sub_text = self.create_subscription(String, "/from_human_text", self._on_text, 10)
        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)

        self.get_logger().info("Dialogue router ready.")

    def _publish_event(self, payload: Dict[str, Any]) -> None:
        self.pub_events.publish(json_msg(payload))

    def _looks_like_navigation(self, text: str) -> bool:
        text = text.lower()
        keys = [
            "go to", "take me to", "navigate to", "where is", "find",
            "去", "带我去", "导航到", "去往", "我要去", "在哪", "找到",
        ]
        return any(k in text for k in keys)

    def _extract_destination_query(self, text: str) -> str:
        cleaned = text.strip()
        patterns = [
            r"^(go to|take me to|navigate to|where is|find)\s+",
            r"^(带我去|导航到|去往|我要去|去|找到)",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned or text.strip()

    def _ordinal_pick(self, text: str, candidates: List[str]) -> Optional[str]:
        mapping = {
            "1": 0, "one": 0, "first": 0, "第一个": 0,
            "2": 1, "two": 1, "second": 1, "第二个": 1,
            "3": 2, "three": 2, "third": 2, "第三个": 2,
        }
        lower = text.lower()
        for token, idx in mapping.items():
            if token in lower and idx < len(candidates):
                return candidates[idx]
        return None

    def _emit_ack(self, dest_id: str, request_source: str, confidence: float) -> None:
        dest = self.places.get(dest_id)
        request_id = new_request_id("nav")
        self.mode = "IDLE"
        self.clarify_candidates = []
        self.clarify_turn = 0
        self._publish_event(
            make_event(
                "nav_ack_requested",
                source="dialogue_router",
                request_id=request_id,
                destination_id=dest_id,
                destination_name=dest["name"],
                request_source=request_source,
                confidence=round(confidence, 3),
            )
        )

    def _emit_clarification(self, utterance: str, candidates: List[str], reason: str) -> None:
        self.mode = "AWAITING_CLARIFICATION"
        self.clarify_candidates = candidates[: self.max_candidates]
        self.clarify_turn += 1
        self._publish_event(
            make_event(
                "nav_clarification_needed",
                source="dialogue_router",
                utterance=utterance,
                candidates=[
                    {
                        "index": i + 1,
                        "id": cid,
                        "name": self.places.get(cid)["name"],
                    }
                    for i, cid in enumerate(self.clarify_candidates)
                ],
                reason=reason,
                turn=self.clarify_turn,
                max_turns=self.max_clarify_turns,
            )
        )

    def _handle_clarification_reply(self, text: str) -> None:
        picked = self._ordinal_pick(text, self.clarify_candidates)
        if picked is None:
            direct = self.places.resolve_direct(text)
            if direct in self.clarify_candidates:
                picked = direct

        if picked:
            self._emit_ack(picked, "clarification", 1.0)
            return

        if self.clarify_turn >= self.max_clarify_turns:
            self.mode = "IDLE"
            self.clarify_candidates = []
            self.clarify_turn = 0
            self._publish_event(
                make_event(
                    "nav_clarification_timeout",
                    source="dialogue_router",
                    utterance=text,
                    reason="clarification_attempts_exceeded",
                )
            )
            return

        self._emit_clarification(text, self.clarify_candidates, "clarification_reply_unresolved")

    def _handle_navigation_request(self, text: str) -> None:
        query = self._extract_destination_query(text)

        direct = self.places.resolve_direct(query)
        if direct:
            self._emit_ack(direct, "direct_alias", 0.95)
            return

        scored = self.places.scored_candidates(query, self.max_candidates)
        if not scored:
            self._publish_event(
                make_event(
                    "nav_unresolved",
                    source="dialogue_router",
                    utterance=text,
                    reason="no_candidates",
                )
            )
            return

        top_score = float(scored[0].get("score", 0.0))
        if top_score < self.nav_match_threshold:
            self._publish_event(
                make_event(
                    "nav_unresolved",
                    source="dialogue_router",
                    utterance=text,
                    normalized_utterance=query,
                    reason="low_similarity",
                    top_score=round(top_score, 3),
                )
            )
            return

        ranked = [str(item["destination_id"]) for item in scored]

        if len(ranked) == 1:
            self._emit_ack(ranked[0], "heuristic_single", max(0.78, top_score))
            return

        llm_parsed = self.llm.parse_nav_intent(query, self.places.as_catalog())
        dest_id = llm_parsed.get("destination_id")
        conf = float(llm_parsed.get("confidence", 0.0) or 0.0)
        if isinstance(dest_id, str) and self.places.get(dest_id) and conf >= self.nav_conf_threshold:
            self._emit_ack(dest_id, "llm_direct", conf)
            return

        self._emit_clarification(query, ranked, "ambiguous_destination")

    def _on_text(self, msg: String) -> None:
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info("user_text={0}".format(text))

        if self.mode == "AWAITING_CLARIFICATION":
            self._handle_clarification_reply(text)
            return

        if self._looks_like_navigation(text):
            self._handle_navigation_request(text)
            return

        self._publish_event(
            make_event(
                "general_response_requested",
                source="dialogue_router",
                utterance=text,
            )
        )

    def _on_event(self, msg: String) -> None:
        payload = parse_json_msg(msg)
        if not payload:
            return

        ev_type = str(payload.get("type", "")).strip()
        if ev_type in {"nav_ack_requested", "nav_start", "nav_succeeded", "nav_failed", "nav_canceled"}:
            self.mode = "IDLE"


def main() -> None:
    rclpy.init()
    node = DialogueRouterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
