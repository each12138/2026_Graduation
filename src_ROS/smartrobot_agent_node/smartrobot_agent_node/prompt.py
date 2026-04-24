import json

SYSTEM_PROMPT = """You are a robot action decision agent for Unitree Go2.

Rules:
1. Select exactly one action from the skill list.
2. Output must be a JSON object with fields: thought, action, params.
3. If user asks to go to a named place, prefer go_to.
4. Use memory_position only when user explicitly asks to save current position.
"""

TOOLS_DESC = """
Available skills:
- stand_up
- stand_down
- move_forward(vx)
- move_lateral(vy)
- move_rotate(vyaw)
- sit_down
- hello
- stretch
- wallow
- scrape
- front_jump
- hand_stand
- memory_position(name, pose)
- go_to(location)
- patrol(locations)
"""


def _safe_json(data):
    return json.dumps(data, ensure_ascii=False)


def build_prompt(state, task, history, place_memory):
    prompt = SYSTEM_PROMPT + "\n" + TOOLS_DESC + "\n"
    prompt += f"Current state: {_safe_json(state)}\n"
    prompt += f"User instruction: {_safe_json(task)}\n"
    prompt += f"Place memory: {_safe_json(place_memory)}\n"
    prompt += "History:\n"

    for record in history[-10:]:
        prompt += (
            f"- task={_safe_json(record.get('task'))}, "
            f"action={record.get('action')}, "
            f"params={_safe_json(record.get('params'))}, "
            f"result={_safe_json(record.get('result'))}\n"
        )

    prompt += (
        "Respond only JSON: "
        '{"thought":"...","action":"stand_up","params":{}}'
    )
    return prompt
