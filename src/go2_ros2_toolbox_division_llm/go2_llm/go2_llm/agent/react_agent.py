import json
import time

from . import prompt


class ReActAgent:
    def __init__(self, llm, state_reader, skill_executor, semantic_map=None):
        self.history = []
        self.llm = llm
        self.state_reader = state_reader
        self.skill_executor = skill_executor
        self.semantic_map = semantic_map
        # 使用递增编号标识一次上层任务，便于把多条动作历史串起来。
        self._task_counter = 0

    def _next_task_id(self):
        self._task_counter += 1
        return f"task_{self._task_counter}"

    def _get_runtime_state(self):
        if self.state_reader is None:
            raise RuntimeError("state_reader_not_initialized")
        return self.state_reader.get_state()

    def _append_action_history(
        self,
        *,
        state,
        task,
        action,
        params,
        result,
        task_id,
        task_type,
        step_index,
    ):
        # history 继续按“动作”记录，但每条动作都保留任务归属，
        # 这样后续做多步任务、巡视任务时，仍能追踪动作属于哪个上层任务。
        self.history.append(
            {
                "state": state,
                "task": task,
                "task_id": task_id,
                "task_type": task_type,
                "step_index": step_index,
                "action": action,
                "params": params,
                "result": result,
            }
        )

    def _validate_skill_action(self, action, params, skill_executor=None):
        fallback_action = "stand_up"

        if not isinstance(action, str) or not action.strip():
            print("LLM output missing valid action, fallback to stand_up")
            return fallback_action, {}
        action = action.strip()

        if skill_executor is not None and action not in skill_executor.skill_registry:
            print(f"LLM action '{action}' not in registry, fallback to stand_up")
            return fallback_action, {}

        if not isinstance(params, dict):
            params = {}

        return action, params

    def _build_fallback_task_spec(self):
        return {
            "type": "single",
            "action": "stand_up",
            "params": {},
        }

    def _normalize_single_task(self, response_json, skill_executor=None):
        action, params = self._validate_skill_action(
            response_json.get("action"),
            response_json.get("params", {}),
            skill_executor=skill_executor,
        )
        return {
            "type": "single",
            "action": action,
            "params": params,
        }

    def _normalize_plan_task(self, response_json, skill_executor=None):
        steps = response_json.get("steps", [])
        if not isinstance(steps, list) or not steps:
            print("LLM plan output missing valid steps, fallback to stand_up")
            return self._build_fallback_task_spec()

        normalized_steps = []
        for step in steps:
            if not isinstance(step, dict):
                print("LLM plan step is not an object, fallback to stand_up")
                return self._build_fallback_task_spec()

            action, params = self._validate_skill_action(
                step.get("action"),
                step.get("params", {}),
                skill_executor=skill_executor,
            )
            normalized_steps.append(
                {
                    "action": action,
                    "params": params,
                }
            )

        return {
            "type": "plan",
            "steps": normalized_steps,
        }

    def _normalize_patrol_task(self, response_json, skill_executor=None):
        if skill_executor is not None and "navigate" not in skill_executor.skill_registry:
            print("LLM patrol requires navigate skill, fallback to stand_up")
            return self._build_fallback_task_spec()

        points = response_json.get("points", [])
        if not isinstance(points, list) or not points:
            print("LLM patrol output missing valid points, fallback to stand_up")
            return self._build_fallback_task_spec()

        normalized_points = []
        for point in points:
            if not isinstance(point, str) or not point.strip():
                print("LLM patrol point is invalid, fallback to stand_up")
                return self._build_fallback_task_spec()
            normalized_points.append(point.strip())

        loop = response_json.get("loop", False)
        loop = bool(loop)

        max_rounds = response_json.get("max_rounds", 1)
        if not isinstance(max_rounds, int) or max_rounds <= 0:
            max_rounds = 1

        wait_sec = response_json.get("wait_sec", 0)
        if not isinstance(wait_sec, (int, float)) or wait_sec < 0:
            wait_sec = 0

        return {
            "type": "patrol",
            "points": normalized_points,
            "loop": loop,
            "max_rounds": max_rounds,
            "wait_sec": float(wait_sec),
        }

    def _requires_origin_memory(self, task_spec):
        if task_spec.get("type") != "plan":
            return False

        for step in task_spec.get("steps", []):
            if (
                step.get("action") == "navigate"
                and isinstance(step.get("params"), dict)
                and step["params"].get("location") == "__origin__"
            ):
                return True
        return False

    def _ensure_origin_memory(self, *, current_state, task, task_id, task_type):
        # 当计划中要“返回原点”时，先自动记录一次当前位置，
        # 避免后续 navigate("__origin__") 找不到目标点。
        result = self.skill_executor.execute(
            "memory_current_position",
            {
                "name": "__origin__",
            },
        )
        self._append_action_history(
            state=current_state,
            task=task,
            action="memory_current_position",
            params={"name": "__origin__"},
            result=result,
            task_id=task_id,
            task_type=task_type,
            step_index=-1,
        )
        return result

    def _execute_single_task(self, *, task, task_id, task_spec):
        current_state = self._get_runtime_state()
        action = task_spec["action"]
        params = task_spec["params"]
        result = self.skill_executor.execute(action, params)

        self._append_action_history(
            state=current_state,
            task=task,
            action=action,
            params=params,
            result=result,
            task_id=task_id,
            task_type="single",
            step_index=0,
        )
        return result

    def _execute_plan_task(self, *, task, task_id, task_spec):
        results = []

        if self._requires_origin_memory(task_spec):
            current_state = self._get_runtime_state()
            origin_result = self._ensure_origin_memory(
                current_state=current_state,
                task=task,
                task_id=task_id,
                task_type="plan",
            )
            results.append(
                {
                    "step_index": -1,
                    "action": "memory_current_position",
                    "params": {"name": "__origin__"},
                    "result": origin_result,
                }
            )
            if not origin_result.get("success", False):
                return {
                    "success": False,
                    "task_type": "plan",
                    "task_id": task_id,
                    "failed_step": -1,
                    "results": results,
                }

        for step_index, step in enumerate(task_spec["steps"]):
            current_state = self._get_runtime_state()
            action = step["action"]
            params = step["params"]
            result = self.skill_executor.execute(action, params)
            
            time.sleep(2.0)

            self._append_action_history(
                state=current_state,
                task=task,
                action=action,
                params=params,
                result=result,
                task_id=task_id,
                task_type="plan",
                step_index=step_index,
            )

            results.append(
                {
                    "step_index": step_index,
                    "action": action,
                    "params": params,
                    "result": result,
                }
            )

            if not result.get("success", False):
                return {
                    "success": False,
                    "task_type": "plan",
                    "task_id": task_id,
                    "failed_step": step_index,
                    "results": results,
                }

        return {
            "success": True,
            "task_type": "plan",
            "task_id": task_id,
            "results": results,
        }

    def _execute_patrol_task(self, *, task, task_id, task_spec):
        points = task_spec["points"]
        loop = task_spec["loop"]
        max_rounds = task_spec["max_rounds"]
        wait_sec = task_spec["wait_sec"]

        total_rounds = max_rounds if loop else 1
        results = []
        step_index = 0

        for round_index in range(total_rounds):
            for point in points:
                current_state = self._get_runtime_state()
                action = "navigate"
                params = {"location": point}
                result = self.skill_executor.execute(action, params)

                self._append_action_history(
                    state=current_state,
                    task=task,
                    action=action,
                    params=params,
                    result=result,
                    task_id=task_id,
                    task_type="patrol",
                    step_index=step_index,
                )

                results.append(
                    {
                        "step_index": step_index,
                        "round_index": round_index,
                        "action": action,
                        "params": params,
                        "result": result,
                    }
                )

                if not result.get("success", False):
                    return {
                        "success": False,
                        "task_type": "patrol",
                        "task_id": task_id,
                        "failed_step": step_index,
                        "failed_point": point,
                        "failed_round": round_index,
                        "results": results,
                    }

                step_index += 1

                if wait_sec > 1.0:
                    time.sleep(wait_sec)
                else:
                    time.sleep(1.0)

        return {
            "success": True,
            "task_type": "patrol",
            "task_id": task_id,
            "completed_rounds": total_rounds,
            "results": results,
        }

    def step(self, task):
        if self.state_reader is None:
            raise RuntimeError("state_reader_not_initialized")
        if self.llm is None:
            raise RuntimeError("llm_not_initialized")
        if self.skill_executor is None:
            raise RuntimeError("skill_executor_not_initialized")

        semantic_map = {}
        if self.semantic_map is not None:
            semantic_map = getattr(self.semantic_map, "map", {}) or {}

        current_state = self._get_runtime_state()
        prompt_use = prompt.build_prompt(
            state=current_state,
            task=task,
            history=self.history,
            semantic_map=semantic_map,
        )

        response = self.llm.generate(prompt_use)
        print(f"LLM response: {response}")

        task_spec = self.parse_response(response, skill_executor=self.skill_executor)
        task_id = self._next_task_id()
        task_type = task_spec["type"]

        if task_type == "single":
            return self._execute_single_task(task=task, task_id=task_id, task_spec=task_spec)
        if task_type == "plan":
            return self._execute_plan_task(task=task, task_id=task_id, task_spec=task_spec)
        if task_type == "patrol":
            return self._execute_patrol_task(task=task, task_id=task_id, task_spec=task_spec)

        print(f"Unknown task type '{task_type}', fallback to stand_up")
        return self._execute_single_task(
            task=task,
            task_id=task_id,
            task_spec=self._build_fallback_task_spec(),
        )

    def parse_response(self, response, skill_executor=None):
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            print("LLM output is not valid JSON, fallback to stand_up")
            return self._build_fallback_task_spec()

        if not isinstance(response_json, dict):
            print("LLM output JSON is not an object, fallback to stand_up")
            return self._build_fallback_task_spec()

        task_type = response_json.get("type")
        if not isinstance(task_type, str) or not task_type.strip():
            # 现在统一要求模型显式输出三种任务类型之一，避免执行层猜测意图。
            print("LLM output missing valid type, fallback to stand_up")
            return self._build_fallback_task_spec()

        task_type = task_type.strip()
        if task_type == "single":
            return self._normalize_single_task(response_json, skill_executor=skill_executor)
        if task_type == "plan":
            return self._normalize_plan_task(response_json, skill_executor=skill_executor)
        if task_type == "patrol":
            return self._normalize_patrol_task(response_json, skill_executor=skill_executor)

        print(f"LLM output task type '{task_type}' is unsupported, fallback to stand_up")
        return self._build_fallback_task_spec()

    def reset(self):
        self.history = []
        self._task_counter = 0
