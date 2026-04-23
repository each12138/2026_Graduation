import time
import sys
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_._SportModeState_ import SportModeState_


class GetState:
    def __init__(self, topic="rt/sportmodestate"):
        self.topic = topic
        self.sub = ChannelSubscriber(self.topic, SportModeState_)
        self.sub.Init()

    def get_state(self):
        msg = self.sub.Read()
        if msg is None:
            return None

        position = list(msg.position)
        quaternion = list(msg.imu_state.quaternion)

        return {
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

    getter = GetState()

    print("state listener started...")

    try:
        while True:
            state = getter.get_state()

            if state is not None:
                print("\n==================== robot state ====================")
                print(f"position:    {state['position']}")
                print(f"orientation: {state['orientation']}")
                print("====================================================")

            time.sleep(2.0)
    finally:
        getter.close()
