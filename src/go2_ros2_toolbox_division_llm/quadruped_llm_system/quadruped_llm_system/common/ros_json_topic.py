from std_msgs.msg import String
from .events import to_json, from_json


def json_msg(payload: dict) -> String:
    msg = String()
    msg.data = to_json(payload)
    return msg


def parse_json_msg(msg: String) -> dict | None:
    return from_json(msg.data)
