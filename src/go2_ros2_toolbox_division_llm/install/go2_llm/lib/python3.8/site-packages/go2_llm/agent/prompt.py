import json

SYSTEM_PROMPT = """You are a robot action decision agent for Unitree Go2.

Rules:
1. Select exactly one action from the skill list.
2. Output must be a JSON object with fields: thought, action, params.
3. If user asks to return/go to a named place, prefer navigate instead of memory_position.
4. Use memory_position only when user explicitly asks to record/save current position.
"""

TOOLS_DESC = """
Available skills:
- stand_up
- stand_down: 趴下
- move_forward(vx)
- move_lateral(vy)
- move_rotate(vyaw)
- sit_down: 坐下
- hello
- stretch
- wallow
- scrape
- front_jump
- hand_stand
- memory_position(name, pose)
- navigate(location)
"""

OUTPUT_FORMAT = """
Output JSON only, for example:
{
  "thought": "...",
  "action": "navigate",
  "params": {"location": "place_1"}
}
"""


def _safe_json(data):
    return json.dumps(data, ensure_ascii=False)


def build_prompt(state, task, history, semantic_map=None):
    if semantic_map is None:
        semantic_map = {}

    prompt_text = SYSTEM_PROMPT + "\n" + TOOLS_DESC + "\n" + OUTPUT_FORMAT + "\n"
    prompt_text += f"Current state: {_safe_json(state)}\n"
    prompt_text += f"User instruction: {_safe_json(task)}\n"
    prompt_text += f"Semantic map (saved places): {_safe_json(semantic_map)}\n"
    prompt_text += "History:\n"

    for record in history[-10:]:
        prompt_text += (
            f"- task={_safe_json(record.get('task'))}, "
            f"action={record.get('action')}, "
            f"params={_safe_json(record.get('params'))}, "
            f"result={_safe_json(record.get('result'))}\n"
        )

    prompt_text += "Choose the single best next action based on state, semantic map, and history."
    return prompt_text
