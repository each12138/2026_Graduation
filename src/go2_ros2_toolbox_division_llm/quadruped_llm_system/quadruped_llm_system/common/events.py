import json
import time
import uuid
from typing import Any

# 获取当前时间戳
def now_ts() -> float:
    return time.time()

# 生成一个新的请求ID，默认前缀为 "req"
def new_request_id(prefix: str = "req") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

# 创建一个事件字典，包含事件类型、时间戳、来源和可选的请求ID以及其他数据
def make_event(event_type: str, source: str, request_id: str = "", **data: Any) -> dict[str, Any]:
    payload = {
        "type": event_type,
        "timestamp": now_ts(),
        "source": source,
    }
    if request_id:
        payload["request_id"] = request_id
    payload.update(data)
    return payload


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def from_json(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
