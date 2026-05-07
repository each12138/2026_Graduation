import json
import os
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.config import load_yaml
from quadruped_llm_system.common.events import from_json, make_event, to_json

# 文本桥接，接收电脑发来的文本并根据状态判断是否发布到"/from_human_text"话题
class TextBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("text_bridge_node")

        runtime_cfg = load_yaml("runtime.yaml")
        bridge_cfg = runtime_cfg.get("voice_bridge", {})

        self.bind_host = str(bridge_cfg.get("bind_host", "0.0.0.0"))
        self.bind_port = int(bridge_cfg.get("bind_port", 8765))
        self.max_text_len = int(bridge_cfg.get("max_text_len", 120))
        self.allowed_sources = set(bridge_cfg.get("allow_sources", ["pc_realtime"]))
        self.token_env = str(bridge_cfg.get("token_env", "VOICE_BRIDGE_TOKEN")).strip()
        self.shared_token = os.getenv(self.token_env, "").strip()

        self.pub_text = self.create_publisher(String, "/from_human_text", 10)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)

        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)
        self.sub_audio = self.create_subscription(String, "/to_human_audio", self._on_audio, 20)

        self._lock = threading.Lock()
        self._speech_active = False
        self._nav_active = False
        self._last_reason = "idle"
        self._last_publish_ts = 0.0
        self._last_text = ""
        self._http_server: Optional[ThreadingHTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None

        self._start_http_server()
        self.get_logger().info(
            f"Text bridge ready at http://{self.bind_host}:{self.bind_port}, "
            f"token_enabled={bool(self.shared_token)}"
        )

    # 启动HTTP服务器，处理文本输入请求
    def _start_http_server(self) -> None:
        node = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "Go2TextBridge/1.0"

            def log_message(self, format: str, *args: Any) -> None:
                node.get_logger().info("HTTP " + (format % args))

            # 辅助函数：发送JSON响应
            def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
                raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            # 辅助函数：读取并解析JSON请求体
            def _read_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    return None, "invalid_content_length"

                body = self.rfile.read(content_length)
                try:
                    payload = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    return None, "invalid_json"

                if not isinstance(payload, dict):
                    return None, "json_root_must_be_object"
                return payload, None

            def do_GET(self) -> None:
                if self.path == "/healthz":
                    self._send_json(
                        HTTPStatus.OK,
                        {"ok": True, "node": "text_bridge_node", "timestamp": time.time()},
                    )
                    return

                if self.path == "/voice/state":
                    self._send_json(HTTPStatus.OK, node.get_voice_state())
                    return

                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"ok": False, "error": "not_found", "path": self.path},
                )

            # 接收文本并决定是否转发到ROS话题
            def do_POST(self) -> None:
                if self.path != "/speech/text":
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {"ok": False, "error": "not_found", "path": self.path},
                    )
                    return

                if node.shared_token:
                    token = self.headers.get("X-Bridge-Token", "").strip()
                    if token != node.shared_token:
                        self._send_json(
                            HTTPStatus.UNAUTHORIZED,
                            {"ok": False, "error": "unauthorized"},
                        )
                        return

                payload, err = self._read_json()
                if err:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": err})
                    return

                source = str(payload.get("source", "pc_realtime")).strip() or "pc_realtime"
                text = str(payload.get("text", "")).strip()
                session_id = str(payload.get("session_id", "")).strip()
                utterance_id = str(payload.get("utterance_id", "")).strip()

                if source not in node.allowed_sources:
                    self._send_json(
                        HTTPStatus.FORBIDDEN,
                        {"ok": False, "error": "source_not_allowed", "source": source},
                    )
                    return

                if not text:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"ok": False, "error": "empty_text"},
                    )
                    return

                if len(text) > node.max_text_len:
                    self._send_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "ok": False,
                            "error": "text_too_long",
                            "max_text_len": node.max_text_len,
                        },
                    )
                    return

                # 判断是否拒绝文本输入
                state = node.get_voice_state()
                if state["muted"]:
                    self._send_json(
                        HTTPStatus.CONFLICT,
                        {"ok": False, "error": "voice_input_muted", "state": state},
                    )
                    return

                request_id = node.publish_text(text, source, session_id, utterance_id)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "accepted": True,
                        "request_id": request_id,
                        "published_topic": "/from_human_text",
                    },
                )

        self._http_server = ThreadingHTTPServer((self.bind_host, self.bind_port), Handler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()

    def _set_state(self, speech_active: Optional[bool] = None, nav_active: Optional[bool] = None) -> None:
        with self._lock:
            if speech_active is not None:
                self._speech_active = speech_active
            if nav_active is not None:
                self._nav_active = nav_active
            self._last_reason = self._compute_reason_locked()

    def _compute_reason_locked(self) -> str:
        if self._speech_active and self._nav_active:
            return "navigation_and_speech_active"
        if self._speech_active:
            return "speech_active"
        if self._nav_active:
            return "navigation_active"
        return "idle"

    # 获取当前语音状态，供HTTP接口使用，当在播报或导航时会拒绝文本输入
    def get_voice_state(self) -> Dict[str, Any]:
        with self._lock:
            muted = self._speech_active or self._nav_active
            return {
                "ok": True,
                "muted": muted,
                "accept_text": not muted,
                "speech_active": self._speech_active,
                "nav_active": self._nav_active,
                "reason": self._last_reason,
                "timestamp": time.time(),
                "last_publish_ts": self._last_publish_ts,
                "last_text": self._last_text,
            }

    def publish_text(self, text: str, source: str, session_id: str, utterance_id: str) -> str:
        msg = String()
        msg.data = text
        self.pub_text.publish(msg)

        request_id = f"bridge_{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._last_publish_ts = time.time()
            self._last_text = text

        event_msg = String()
        event_msg.data = to_json(
            make_event(
                "voice_text_received",
                source="text_bridge",
                request_id=request_id,
                text=text,
                transport="http",
                external_source=source,
                session_id=session_id,
                utterance_id=utterance_id,
            )
        )
        self.pub_events.publish(event_msg)
        self.get_logger().info(f"Published bridged text: {text}")
        return request_id

    # “/to_human_audio”的回调函数，收到音频事件时更新状态以拒绝文本输入
    def _on_audio(self, msg: String) -> None:
        payload = from_json(msg.data)
        if not payload:
            return
        text = str(payload.get("text", "")).strip()
        if text:
            self._set_state(speech_active=True)

    # “/agent_events”的回调函数，收到导航相关事件时更新状态，接受或拒绝文本输入
    def _on_event(self, msg: String) -> None:
        payload = from_json(msg.data)
        if not payload:
            return

        ev_type = str(payload.get("type", "")).strip()

        if ev_type == "speech_done":
            self._set_state(speech_active=False)
            return

        if ev_type == "nav_start":
            self._set_state(nav_active=True)
            return

        if ev_type in {"nav_succeeded", "nav_failed", "nav_canceled"}:
            self._set_state(nav_active=False)
            return

    def destroy_node(self) -> bool:
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = TextBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
