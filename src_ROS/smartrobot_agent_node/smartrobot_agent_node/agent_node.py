import json

from .llm import LLMClient
from .prompt import build_prompt


class AgentNode:
    """Decision node: text + state + place memory -> action packet."""

    def __init__(self, llm=None):
        self.llm = llm or LLMClient()
        self.history = []

    def decide(self, user_text, state, place_memory, skill_registry):
        prompt = build_prompt(
            state=state,
            task=user_text,
            history=self.history,
            place_memory=place_memory,
        )
        raw = self.llm.generate(prompt)
        action_packet = self._parse(raw, skill_registry=skill_registry)
        return action_packet, raw

    def remember_result(self, task, state, action_packet, result):
        self.history.append(
            {
                "task": task,
                "state": state,
                "action": action_packet.get("action"),
                "params": action_packet.get("params", {}),
                "result": result,
            }
        )

    @staticmethod
    def _parse(raw, skill_registry):
        fallback = {"thought": "fallback", "action": "stand_up", "params": {}}
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return fallback

        if not isinstance(obj, dict):
            return fallback

        action = obj.get("action")
        if not isinstance(action, str) or not action.strip():
            return fallback
        action = action.strip()

        if action not in skill_registry:
            return fallback

        params = obj.get("params", {})
        if not isinstance(params, dict):
            params = {}

        thought = obj.get("thought", "")
        if not isinstance(thought, str):
            thought = ""

        return {"thought": thought, "action": action, "params": params}
