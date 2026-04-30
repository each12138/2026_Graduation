import os
import time

from .tf_pose_provider import TfPoseProvider

DEFAULT_GLOBAL_FRAME = "map"
DEFAULT_BASE_FRAME = "base_link"
DEFAULT_LOOKUP_TIMEOUT = 0.3


class StateReader:
    def __init__(
        self,
        global_frame=DEFAULT_GLOBAL_FRAME,
        robot_frame=DEFAULT_BASE_FRAME,
        lookup_timeout=DEFAULT_LOOKUP_TIMEOUT,
        pose_provider=None,
    ):
        global_frame_env = os.getenv("GO2_GLOBAL_FRAME", global_frame)
        robot_frame_env = os.getenv("GO2_ROBOT_FRAME", robot_frame)
        lookup_timeout_env = os.getenv("GO2_STATE_LOOKUP_TIMEOUT", str(lookup_timeout))

        self.global_frame = str(global_frame_env).strip() or DEFAULT_GLOBAL_FRAME
        self.robot_frame = str(robot_frame_env).strip() or DEFAULT_BASE_FRAME
        try:
            self.lookup_timeout = float(lookup_timeout_env)
        except ValueError:
            self.lookup_timeout = DEFAULT_LOOKUP_TIMEOUT

        self._owns_pose_provider = pose_provider is None
        self.pose_provider = pose_provider or TfPoseProvider()

    def get_state(self):
        transform = self.pose_provider.lookup_transform(
            target_frame=self.global_frame,
            source_frame=self.robot_frame,
            timeout_sec=self.lookup_timeout,
        )

        translation = transform.transform.translation
        rotation = transform.transform.rotation

        return {
            "frame_id": self.global_frame,
            "position": {
                "x": float(translation.x),
                "y": float(translation.y),
                "z": float(translation.z),
            },
            "orientation": {
                "x": float(rotation.x),
                "y": float(rotation.y),
                "z": float(rotation.z),
                "w": float(rotation.w),
            },
        }

    def close(self):
        if self._owns_pose_provider and self.pose_provider is not None:
            self.pose_provider.close()


if __name__ == "__main__":
    getter = None
    try:
        getter = StateReader()
        print("state listener started...")
        while True:
            state = getter.get_state()
            print("\n==================== robot state ====================")
            print(f"frame_id:    {state['frame_id']}")
            print(f"position:    {state['position']}")
            print(f"orientation: {state['orientation']}")
            print("====================================================")
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        if getter is not None:
            getter.close()
