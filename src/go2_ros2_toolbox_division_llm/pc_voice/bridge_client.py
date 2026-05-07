import time
from dataclasses import dataclass
from typing import Any, Dict

import requests

# 把识别出的文字发给狗端
@dataclass
class BridgeState:
    ok: bool
    muted: bool
    accept_text: bool
    speech_active: bool
    nav_active: bool
    reason: str
    timestamp: float
    last_publish_ts: float
    last_text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BridgeState":
        return cls(
            ok=bool(data.get("ok", False)),
            muted=bool(data.get("muted", False)),
            accept_text=bool(data.get("accept_text", False)),
            speech_active=bool(data.get("speech_active", False)),
            nav_active=bool(data.get("nav_active", False)),
            reason=str(data.get("reason", "unknown")),
            timestamp=float(data.get("timestamp", 0.0)),
            last_publish_ts=float(data.get("last_publish_ts", 0.0)),
            last_text=str(data.get("last_text", "")),
        )


class DogBridgeClient:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.base_url = str(cfg["base_url"]).rstrip("/")
        self.token = str(cfg.get("token", "")).strip()
        self.timeout_s = float(cfg.get("timeout_s", 3.0))

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Bridge-Token"] = self.token
        return headers

    # 向狗端发出GET请求，获取状态
    def get_state(self) -> BridgeState:
        url = f"{self.base_url}/voice/state"
        resp = requests.get(url, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError("bridge state is not an object")
        return BridgeState.from_dict(data)

    # 向狗端发出POST请求，发送识别出的文字
    def post_text(self, text: str, session_id: str, utterance_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/speech/text"
        payload = {
            "text": text,
            "session_id": session_id,
            "utterance_id": utterance_id,
            "source": "pc_realtime",
            "timestamp": time.time(),
        }
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout_s)
        if resp.status_code == 409:
            return resp.json()
        resp.raise_for_status()
        return resp.json()
