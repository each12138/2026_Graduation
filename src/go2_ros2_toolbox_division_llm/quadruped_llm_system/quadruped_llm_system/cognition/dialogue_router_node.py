import re

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.config import load_yaml, config_dir
from quadruped_llm_system.common.events import make_event, new_request_id
from quadruped_llm_system.common.ros_json_topic import json_msg, parse_json_msg
from quadruped_llm_system.cognition.llm_client import LLMClient
from quadruped_llm_system.cognition.place_repository import PlaceRepository


class DialogueRouterNode(Node):
    # 认知层入口：把用户文本分流到导航、澄清或普通对话响应链路。
    def __init__(self) -> None:
        super().__init__("dialogue_router_node")

        self.runtime_cfg = load_yaml("runtime.yaml")
        self.places = PlaceRepository("destinations.yaml", config_dir() / "memory_points.json")
        self.llm = LLMClient(self.runtime_cfg)

        dialogue_cfg = self.runtime_cfg.get("dialogue", {})
        self.nav_conf_threshold = float(dialogue_cfg.get("nav_confidence_threshold", 0.72))
        self.max_candidates = int(dialogue_cfg.get("max_candidates", 3))
        self.max_clarify_turns = int(dialogue_cfg.get("max_clarify_turns", 2))

        self.mode = "IDLE"
        self.clarify_candidates: list[str] = []
        self.clarify_turn = 0

        self.sub_text = self.create_subscription(String, "/from_human_text", self._on_text, 10)
        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)

        self.get_logger().info("Dialogue router ready.")

    def _publish_event(self, payload: dict) -> None:
        self.pub_events.publish(json_msg(payload))

    def _looks_like_navigation(self, text: str) -> bool:
        # 先用轻量关键词判断，避免所有输入都走 LLM。
        text = text.lower()
        keys = [
            "go to", "take me to", "navigate to", "where is", "find",
            "去", "带我去", "导航到", "去往", "我要去", "在哪",
        ]
        return any(k in text for k in keys)

    # 澄清阶段用户可能会说“第一个/第二个”，这里做个简单的映射。
    def _ordinal_pick(self, text: str, candidates: list[str]) -> str | None:
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

    # 导航请求确认：发送 nav_ack_requested 事件，包含目的地 ID、名称、请求来源和置信度等信息。
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

    # 澄清请求：发送 nav_clarification_needed 事件，包含候选地点列表、用户原话、澄清原因等信息。
    def _emit_clarification(self, utterance: str, candidates: list[str], reason: str) -> None:
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

    # 澄清回复处理：如果用户选择了候选项或直接说了地点名，发送确认事件；如果超过澄清轮次，发送澄清失败事件；否则继续请求澄清。
    def _handle_clarification_reply(self, text: str) -> None:
        # 澄清阶段优先接受“第一个/第二个”这类选择，也支持再次直呼地点名。
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

    # 导航请求处理：先尝试精确别名匹配，再用轻量关键词排序，如果仍不确定则调用 LLM 辅助解析，最后进入澄清流程。
    def _handle_navigation_request(self, text: str) -> None:
        # 导航解析顺序：精确别名 -> 轻量排序 -> LLM 辅助 -> 进入澄清。
        direct = self.places.resolve_direct(text)
        if direct:
            self._emit_ack(direct, "direct_alias", 0.95)
            return

        ranked = self.places.rank_candidates(text, self.max_candidates)
        if not ranked:
            self._publish_event(
                make_event(
                    "nav_unresolved",
                    source="dialogue_router",
                    utterance=text,
                    reason="no_candidates",
                )
            )
            return

        if len(ranked) == 1:
            self._emit_ack(ranked[0], "heuristic_single", 0.78)
            return

        llm_parsed = self.llm.parse_nav_intent(text, self.places.as_catalog())
        dest_id = llm_parsed.get("destination_id")
        conf = float(llm_parsed.get("confidence", 0.0) or 0.0)
        if isinstance(dest_id, str) and self.places.get(dest_id) and conf >= self.nav_conf_threshold:
            self._emit_ack(dest_id, "llm_direct", conf)
            return

        self._emit_clarification(text, ranked, "ambiguous_destination")


    # 普通对话处理：把用户输入原样转发给对话系统，等待后续事件触发响应生成。
    def _on_text(self, msg: String) -> None:
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f"user_text={text}")

        # 如果当前处于澄清轮次，优先把输入解释成对候选地点的回答。
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

    # 监听导航相关事件，如果检测到导航开始或结束（成功/失败/取消），则重置状态回到 IDLE。
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
