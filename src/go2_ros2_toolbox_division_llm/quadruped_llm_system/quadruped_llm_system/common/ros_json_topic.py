from typing import Any, Dict, Optional

from std_msgs.msg import String

from .events import from_json, to_json


def json_msg(payload: Dict[str, Any]) -> String:
    msg = String()
    msg.data = to_json(payload)
    return msg


def parse_json_msg(msg: String) -> Optional[Dict[str, Any]]:
    return from_json(msg.data)
