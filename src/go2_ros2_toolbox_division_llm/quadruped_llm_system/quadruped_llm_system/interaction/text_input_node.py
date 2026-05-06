import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TextInputNode(Node):
    def __init__(self) -> None:
        super().__init__("text_input_node")
        self.pub = self.create_publisher(String, "/from_human_text", 10)
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self.get_logger().info("Text input node ready. Type commands in terminal.")

    def _loop(self) -> None:
        while rclpy.ok():
            try:
                text = input("user> ").strip()
            except EOFError:
                break
            except KeyboardInterrupt:
                break

            if not text:
                continue

            msg = String()
            msg.data = text
            self.pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = TextInputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
