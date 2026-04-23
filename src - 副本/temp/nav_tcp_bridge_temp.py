#!/usr/bin/env python3
import argparse
import json
import socket
import struct
import threading

import rclpy
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class TempNavTcpBridge(Node):
    def __init__(self, host: str, port: int, frame_id: str = "odom"):
        super().__init__("temp_nav_tcp_bridge")
        self.host = host
        self.port = port
        self.frame_id = frame_id
        self._action_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self._running = True
        self.tcp_thread = threading.Thread(target=self._tcp_server_loop, daemon=True)
        self.tcp_thread.start()

        self.get_logger().info(
            f"Temp bridge started, listening on {self.host}:{self.port}, frame_id={self.frame_id}"
        )

    def _recv_exact(self, sock: socket.socket, size: int):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _tcp_server_loop(self):
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

                        length = struct.unpack("!I", length_data)[0]
                        payload = self._recv_exact(client_socket, length)
                        if not payload:
                            break

                        goal_data = json.loads(payload.decode("utf-8"))
                        self._send_nav_goal(goal_data)
                except Exception as e:
                    self.get_logger().error(f"TCP loop error: {e}")

            self.get_logger().info("Client disconnected")

    def _send_nav_goal(self, goal_data: dict):
        try:
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose.header.frame_id = self.frame_id
            goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

            goal_msg.pose.pose.position.x = float(goal_data["position"]["x"])
            goal_msg.pose.pose.position.y = float(goal_data["position"]["y"])
            goal_msg.pose.pose.position.z = float(goal_data["position"]["z"])

            goal_msg.pose.pose.orientation.x = float(goal_data["orientation"]["x"])
            goal_msg.pose.pose.orientation.y = float(goal_data["orientation"]["y"])
            goal_msg.pose.pose.orientation.z = float(goal_data["orientation"]["z"])
            goal_msg.pose.pose.orientation.w = float(goal_data["orientation"]["w"])

            self.get_logger().info(
                "Received goal: "
                f"x={goal_msg.pose.pose.position.x:.3f}, "
                f"y={goal_msg.pose.pose.position.y:.3f}"
            )

            if not self._action_client.wait_for_server(timeout_sec=5.0):
                self.get_logger().error("navigate_to_pose action server not available")
                return

            send_goal_future = self._action_client.send_goal_async(
                goal_msg, feedback_callback=self._feedback_callback
            )
            send_goal_future.add_done_callback(self._goal_response_callback)
        except Exception as e:
            self.get_logger().error(f"Invalid goal payload: {e}")

    def _goal_response_callback(self, future):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warning("Goal rejected")
                return
            self.get_logger().info("Goal accepted")
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._result_callback)
        except Exception as e:
            self.get_logger().error(f"Goal response error: {e}")

    def _feedback_callback(self, feedback_msg):
        try:
            remaining = feedback_msg.feedback.distance_remaining
            self.get_logger().info(f"Navigating, remaining={remaining:.2f}m")
        except Exception:
            pass

    def _result_callback(self, future):
        try:
            result = future.result()
            self.get_logger().info(f"Nav finished with status={result.status}")
        except Exception as e:
            self.get_logger().error(f"Result callback error: {e}")

    def destroy_node(self):
        self._running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        super().destroy_node()


def main():
    parser = argparse.ArgumentParser(description="Temporary TCP bridge for Nav2")
    parser.add_argument("--host", default="127.0.0.1", help="TCP bind host")
    parser.add_argument("--port", type=int, default=5432, help="TCP bind port")
    parser.add_argument("--frame-id", default="odom", help="Target frame_id for NavigateToPose")
    args = parser.parse_args()

    rclpy.init()
    node = TempNavTcpBridge(args.host, args.port, args.frame_id)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
