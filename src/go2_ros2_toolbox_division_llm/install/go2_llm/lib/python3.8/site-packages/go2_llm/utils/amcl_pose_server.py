import json
import os
import socketserver

try:
    from .amcl_pose_provider import AmclPoseProvider
except ImportError:
    from amcl_pose_provider import AmclPoseProvider

DEFAULT_STATE_SERVER_HOST = os.environ.get("GO2_STATE_SERVER_HOST", "127.0.0.1")
DEFAULT_STATE_SERVER_PORT = int(os.environ.get("GO2_STATE_SERVER_PORT", "8765"))


class _ThreadedStateServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, request_handler_class, pose_provider):
        super().__init__(server_address, request_handler_class)
        self.pose_provider = pose_provider


class _StateRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        raw_line = self.rfile.readline()
        if not raw_line:
            return

        try:
            request = json.loads(raw_line.decode("utf-8").strip())
        except json.JSONDecodeError as exc:
            self._write_response(
                {"success": False, "error": "invalid_json", "detail": str(exc)}
            )
            return

        cmd = request.get("cmd")
        if cmd != "get_state":
            self._write_response({"success": False, "error": "unsupported_command"})
            return

        timeout_sec = request.get("timeout_sec")
        try:
            # 这里单独放在 ROS2 进程里读取位姿，避免与 Unitree SDK 在同进程冲突。
            state = self.server.pose_provider.get_pose_info(timeout_sec=timeout_sec)
        except TimeoutError as exc:
            self._write_response(
                {"success": False, "error": "pose_timeout", "detail": str(exc)}
            )
            return
        except Exception as exc:
            self._write_response(
                {"success": False, "error": "pose_lookup_failed", "detail": str(exc)}
            )
            return

        self._write_response({"success": True, "state": state})

    def _write_response(self, payload):
        message = json.dumps(payload, ensure_ascii=False) + "\n"
        self.wfile.write(message.encode("utf-8"))


def main():
    host = DEFAULT_STATE_SERVER_HOST
    port = DEFAULT_STATE_SERVER_PORT
    provider = AmclPoseProvider()
    server = _ThreadedStateServer((host, port), _StateRequestHandler, provider)

    print(f"AMCL pose server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAMCL pose server stopped.")
    finally:
        server.shutdown()
        server.server_close()
        provider.close()


if __name__ == "__main__":
    main()
