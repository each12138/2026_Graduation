#!/usr/bin/env python3
import json
import os
import socket
import struct
import threading

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5432
DEFAULT_FRAME_ID = "map"
DEFAULT_RESULT_TIMEOUT = 60.0 # 等待导航结果的最长时间
DEFAULT_SERVER_TIMEOUT = 5.0  # 等待action server的最长时间
DEFAULT_GOAL_RESPONSE_TIMEOUT = 10.0  # Nav2有没有收到这个goal


class Nav2TcpBridge(Node):
    def __init__(self):
        super().__init__("nav2_tcp_bridge")

        self.host = os.getenv("GO2_NAV_TCP_HOST", DEFAULT_HOST)
        self.port = int(os.getenv("GO2_NAV_TCP_PORT", str(DEFAULT_PORT)))
        self.frame_id = os.getenv("GO2_NAV_FRAME_ID", DEFAULT_FRAME_ID)

        self.result_timeout = float(os.getenv("GO2_NAV_RESULT_TIMEOUT", str(DEFAULT_RESULT_TIMEOUT)))
        self.server_timeout = float(os.getenv("GO2_NAV_SERVER_TIMEOUT", str(DEFAULT_SERVER_TIMEOUT)))
        self.goal_response_timeout = float(os.getenv("GO2_NAV_GOAL_RESPONSE_TIMEOUT", str(DEFAULT_GOAL_RESPONSE_TIMEOUT)))

        self._action_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self._running = True
        self.tcp_thread = threading.Thread(target=self.tcp_server_loop, daemon=True)
        self.tcp_thread.start()

        self.get_logger().info(
            f"Nav2 TCP Bridge started: {self.host}:{self.port}, frame_id={self.frame_id}"
        )

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    @staticmethod
    def _send_json_response(sock: socket.socket, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        length_prefix = struct.pack("!I", len(data))
        sock.sendall(length_prefix + data)
        
    @staticmethod
    def _wait_for_future_result(future, timeout_sec: float):
        event = threading.Event()
        def _on_done(_future):
            event.set()
        future.add_done_callback(_on_done)
        if event.wait(timeout=timeout_sec):
            return future.result()
        else:
            return None
    
    def tcp_server_loop(self):
        while self._running and rclpy.ok():
            try:
                client_socket, addr = self.server_socket.accept()
            except OSError:
                break

            self.get_logger().info(f"Client connected: {addr}")
            with client_socket:
                try:
                    while self._running and rclpy.ok():
                        length_data = self._recv_exact(client_socket, 4)
                        if not length_data:
                            break

                        payload_len = struct.unpack("!I", length_data)[0]
                        payload = self._recv_exact(client_socket, payload_len)
                        if not payload:
                            break

                        goal_data = json.loads(payload.decode("utf-8"))
                        response = self._handle_navigation_request(goal_data)
                        self._send_json_response(client_socket, response)
                except Exception as e:
                    self.get_logger().error(f"TCP loop error: {e}")

            self.get_logger().info("Client disconnected")

    def _build_goal_message(self, goal_data: dict):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = goal_data.get("frame_id", self.frame_id)
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = float(goal_data["position"]["x"])
        goal_msg.pose.pose.position.y = float(goal_data["position"]["y"])
        goal_msg.pose.pose.position.z = float(goal_data["position"].get("z", 0.0))

        goal_msg.pose.pose.orientation.x = float(goal_data["orientation"]["x"])
        goal_msg.pose.pose.orientation.y = float(goal_data["orientation"]["y"])
        goal_msg.pose.pose.orientation.z = float(goal_data["orientation"]["z"])
        goal_msg.pose.pose.orientation.w = float(goal_data["orientation"]["w"])

        return goal_msg
    
    def _handle_navigation_request(self, goal_data: dict):
        try:
            goal_msg = self._build_goal_message(goal_data)
            
            self.get_logger().info(
                "Received goal: "
                f"frame={goal_msg.pose.header.frame_id}, "
                f"x={goal_msg.pose.pose.position.x:.3f}, "
                f"y={goal_msg.pose.pose.position.y:.3f}"
            )
            
            if not self._action_client.wait_for_server(timeout_sec=self.server_timeout):
                self.get_logger().error("navigate_to_pose action server not available")
                return {
                    "success": False,
                }
                
            timeout_sec = goal_data.get("timeout_sec", self.result_timeout)
            try:
                timeout_sec = float(timeout_sec)
            except (ValueError, TypeError):
                timeout_sec = self.result_timeout
                
            send_goal_future = self._action_client.send_goal_async(
                goal_msg,
                feedback_callback=self._feedback_callback,
            )
            
            goal_handle = self._wait_for_future_result(send_goal_future, self.goal_response_timeout)
            if goal_handle is None:
                self.get_logger().error("Goal response timed out")
                return {
                    "success": False,
                }
            
            if not goal_handle.accepted:
                self.get_logger().warning("Goal rejected by action server")
                return {
                    "success": False,
                }
            
            result_future = goal_handle.get_result_async()
            nav_result = self._wait_for_future_result(result_future, self.result_timeout)
            if nav_result is None:
                self.get_logger().error("Navigation result timed out")
                try:
                    goal_handle.cancel_goal_async()
                except Exception:
                    pass
                return {
                    "success": False,
                }
                
            success = nav_result.status == GoalStatus.STATUS_SUCCEEDED
            return {
                "success": success,
            }
            
        except Exception as exc:
            self.get_logger().error(f"Error handling navigation request: {exc}")
            return {
                "success": False,
            }

    def _feedback_callback(self, feedback_msg):
        try:
            remaining = feedback_msg.feedback.distance_remaining
            self.get_logger().info(f"Navigating, remaining={remaining:.2f}m")
        except Exception:
            pass

    def destroy_node(self):
        self._running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Nav2TcpBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
