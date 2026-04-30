import json

from . import prompt


class ReActAgent:
    def __init__(self, llm, state_reader, skill_executor, semantic_map=None):
        self.history = []
        self.llm = llm
        self.state_reader = state_reader
        self.skill_executor = skill_executor
        self.semantic_map = semantic_map

    def step(self, task):
        if self.state_reader is None:
            raise RuntimeError("state_reader_not_initialized")
        if self.llm is None:
            raise RuntimeError("llm_not_initialized")
        if self.skill_executor is None:
            raise RuntimeError("skill_executor_not_initialized")

        current_state = self.state_reader.get_state()

        semantic_map = {}
        if self.semantic_map is not None:
            semantic_map = getattr(self.semantic_map, "map", {}) or {}

        prompt_use = prompt.build_prompt(
            state=current_state,
            task=task,
            history=self.history,
            semantic_map=semantic_map,
        )

        response = self.llm.generate(prompt_use)
        print(f"LLM response: {response}")

        action, params = self.parse_response(response, skill_executor=self.skill_executor)
        result = self.skill_executor.execute(action, params)

        self.history.append(
            {
                "state": current_state,
                "task": task,
                "action": action,
                "params": params,
                "result": result,
            }
        )

        return result

    def parse_response(self, response, skill_executor=None):
        fallback_action = "stand_up"
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            print("LLM output is not valid JSON, fallback to stand_up")
            return fallback_action, {}

        if not isinstance(response_json, dict):
            print("LLM output JSON is not an object, fallback to stand_up")
            return fallback_action, {}

        action = response_json.get("action")
        if not isinstance(action, str) or not action.strip():
            print("LLM output missing valid action, fallback to stand_up")
            return fallback_action, {}
        action = action.strip()

        if skill_executor is not None and action not in skill_executor.skill_registry:
            print(f"LLM action '{action}' not in registry, fallback to stand_up")
            return fallback_action, {}

        params = response_json.get("params", {})
        if not isinstance(params, dict):
            params = {}

        return action, params

    def reset(self):
        self.history = []
