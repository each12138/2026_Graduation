import os
import sys
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_go.msg.dds_._SportModeState_ import SportModeState_


class StateReader:
    """Read required fields from rt/sportmodestate.

    This is intentionally a library-style module, not a separate runtime node.
    """

    def __init__(self, topic="rt/sportmodestate"):
        self.topic = topic
        state_frame = os.getenv("GO2_STATE_FRAME", "odom")
        self.frame_id = str(state_frame).strip() if state_frame is not None else "odom"
        if not self.frame_id:
            self.frame_id = "odom"
        self.sub = ChannelSubscriber(self.topic, SportModeState_)
        self.sub.Init()

    def get_state(self):
        msg = self.sub.Read()
        if msg is None:
            return None

        position = list(msg.position)
        quaternion = list(msg.imu_state.quaternion)
        return {
            "frame_id": self.frame_id,
            "position": {
                "x": float(position[0]),
                "y": float(position[1]),
                "z": float(position[2]),
            },
            "orientation": {
                "w": float(quaternion[0]),
                "x": float(quaternion[1]),
                "y": float(quaternion[2]),
                "z": float(quaternion[3]),
            },
        }

    def close(self):
        self.sub.Close()


if __name__ == "__main__":
    network_interface = sys.argv[1] if len(sys.argv) > 1 else None
    if network_interface:
        ChannelFactoryInitialize(0, network_interface)
    else:
        ChannelFactoryInitialize(0)

    reader = StateReader()
    print("state reader started...")
    try:
        while True:
            state = reader.get_state()
            if state is not None:
                print(state)
            time.sleep(1.0)
    finally:
        reader.close()
