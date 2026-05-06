import json
import time
import uuid
from typing import Any, Dict, Optional


def now_ts() -> float:
    return time.time()


def new_request_id(prefix: str = "req") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def make_event(event_type: str, source: str, request_id: str = "", **data: Any) -> Dict[str, Any]:
    payload = {
        "type": event_type,
        "timestamp": now_ts(),
        "source": source,
    }
    if request_id:
        payload["request_id"] = request_id
    payload.update(data)
    return payload


def to_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def from_json(raw: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
