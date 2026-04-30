import threading

try:
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from tf2_ros import Buffer, TransformException, TransformListener
except ImportError:  # pragma: no cover - depends on robot ROS2 environment
    rclpy = None
    SingleThreadedExecutor = None
    Node = None
    Buffer = None
    TransformException = Exception
    TransformListener = None


class _TfPoseNode(Node):
    def __init__(self):
        super().__init__("go2_tf_pose_provider")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=False)


class TfPoseProvider:
    def __init__(self):
        if rclpy is None or Node is None or Buffer is None or TransformListener is None:
            raise RuntimeError(
                "ros2_tf_unavailable: install/source ROS2 with rclpy and tf2_ros "
                "to read TF pose"
            )

        self._owns_rclpy = not rclpy.ok()
        if self._owns_rclpy:
            rclpy.init(args=None)

        self.node = _TfPoseNode()
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)

        self._running = True
        self._spin_thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._spin_thread.start()

    def _spin_loop(self):
        while self._running and rclpy.ok():
            self.executor.spin_once(timeout_sec=0.1)

    def lookup_transform(self, target_frame, source_frame, timeout_sec):
        try:
            return self.node.tf_buffer.lookup_transform(
                target_frame,
                source_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=timeout_sec),
            )
        except TransformException as exc:
            raise RuntimeError(
                f"state_transform_unavailable: cannot resolve "
                f"{target_frame}->{source_frame}: {exc}"
            ) from exc

    def close(self):
        self._running = False
        if hasattr(self, "_spin_thread") and self._spin_thread.is_alive():
            self._spin_thread.join(timeout=1.0)
        if hasattr(self, "executor"):
            self.executor.remove_node(self.node)
            self.executor.shutdown()
        if hasattr(self, "node"):
            self.node.destroy_node()
        if self._owns_rclpy and rclpy.ok():
            rclpy.shutdown()
