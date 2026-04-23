import json

import global_vars
from . import prompt


class ReActAgent:
    def __init__(self):
        self.history = []

    def step(self, task):
        current_state = global_vars.state_client.get_state()

        semantic_map = {}
        if getattr(global_vars, "map", None) is not None:
            semantic_map = getattr(global_vars.map, "map", {}) or {}

        prompt_use = prompt.build_prompt(
            state=current_state,
            task=task,
            history=self.history,
            semantic_map=semantic_map,
        )

        response = global_vars.llm.generate(prompt_use)
        print(f"LLM response: {response}")

        action, params = self.parse_response(response)
        result = global_vars.skill_executor.execute(action, params)

        self.history.append({
            "state": current_state,
            "task": task,
            "action": action,
            "params": params,
            "result": result,
        })

        return result

    def parse_response(self, response):
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            print("LLM output is not valid JSON, fallback to stand_up")
            return "stand_up", {}

        action = response_json.get("action")
        params = response_json.get("params", {})
        if not isinstance(params, dict):
            params = {}

        return action, params

    def reset(self):
        self.history = []
