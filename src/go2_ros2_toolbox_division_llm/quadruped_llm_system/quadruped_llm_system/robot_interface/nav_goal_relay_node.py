import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String

from quadruped_llm_system.common.events import from_json, make_event, to_json

# 收到目标点后，调用NavigateToPose action server进行导航，并将结果转换成事件发布出去
class NavGoalRelayNode(Node):
    def __init__(self) -> None:
        super().__init__("nav_goal_relay_node")

        self.sub_goal = self.create_subscription(PoseStamped, "/goal_pose", self._on_goal, 10)
        self.pub_events = self.create_publisher(String, "/agent_events", 20)
        self.sub_events = self.create_subscription(String, "/agent_events", self._on_event, 20)

        self._action_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        self.active_request_id = ""
        self.active_destination_id = ""
        self.active_destination_name = ""
        self._active_goal_handle = None

        self.server_timeout_s = 5.0

        self.get_logger().info("Nav goal relay ready. Using real NavigateToPose action.")

    def _on_event(self, msg: String) -> None:
        payload = from_json(msg.data)
        if not payload:
            return

        if str(payload.get("type", "")).strip() != "nav_start":
            return

        self.active_request_id = str(payload.get("request_id", "")).strip()
        self.active_destination_id = str(payload.get("destination_id", "")).strip()
        self.active_destination_name = str(payload.get("destination_name", "")).strip()

    def _publish_nav_result(self, event_type: str, reason: str = "") -> None:
        msg = String()
        msg.data = to_json(
            make_event(
                event_type,
                source="nav_goal_relay",
                request_id=self.active_request_id,
                destination_id=self.active_destination_id,
                destination_name=self.active_destination_name,
                reason=reason,
            )
        )
        self.pub_events.publish(msg)

    def _status_to_event(self, status: int) -> str:
        if status == GoalStatus.STATUS_SUCCEEDED:
            return "nav_goal_succeeded"
        if status == GoalStatus.STATUS_CANCELED:
            return "nav_goal_canceled"
        return "nav_goal_failed"

    # 收到目标点
    def _on_goal(self, msg: PoseStamped) -> None:
        self.get_logger().info(
            "goal received x={0:.2f} y={1:.2f} request_id={2}".format(
                msg.pose.position.x,
                msg.pose.position.y,
                self.active_request_id or "unknown",
            )
        )

        #action server不可用
        if not self._action_client.wait_for_server(timeout_sec=self.server_timeout_s):
            self.get_logger().error("navigate_to_pose action server not available")
            self._publish_nav_result("nav_goal_failed", "action_server_unavailable")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = msg

        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback,
        )
        send_goal_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:
            self.get_logger().error("Goal response exception: {0}".format(exc))
            self._publish_nav_result("nav_goal_failed", "goal_response_exception")
            return

        if goal_handle is None:
            self.get_logger().error("Goal response is None")
            self._publish_nav_result("nav_goal_failed", "goal_response_none")
            return

        if not goal_handle.accepted:
            self.get_logger().warning("Goal rejected by action server")
            self._publish_nav_result("nav_goal_failed", "goal_rejected")
            return

        self.get_logger().info("Goal accepted by NavigateToPose")
        self._active_goal_handle = goal_handle

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_nav_result)

    def _on_nav_result(self, future) -> None:
        try:
            result = future.result()
        except Exception as exc:
            self.get_logger().error("Navigation result exception: {0}".format(exc))
            self._publish_nav_result("nav_goal_failed", "result_exception")
            return

        if result is None:
            self.get_logger().error("Navigation result is None")
            self._publish_nav_result("nav_goal_failed", "result_none")
            return

        event_type = self._status_to_event(result.status)
        self.get_logger().info("Navigation finished with status={0}".format(result.status))
        self._publish_nav_result(event_type)

    # 打印导航过程中剩余距离的反馈信息
    def _feedback_callback(self, feedback_msg) -> None:
        try:
            remaining = feedback_msg.feedback.distance_remaining
            self.get_logger().info("Navigating, remaining={0:.2f}m".format(remaining))
        except Exception:
            pass

    def destroy_node(self):
        self._action_client.destroy()
        super().destroy_node()


def main() -> None:
    rclpy.init()
    node = NavGoalRelayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
