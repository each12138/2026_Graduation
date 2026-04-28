import os
import sys
import time

from smartrobot_agent_controller.agent_controller import AgentController
from smartrobot_place_memory.place_memory import PlaceMemory
from smartrobot_skill_controller.skill_manager import DEFAULT_DURATION
from smartrobot_skill_controller.skill_controller import SkillController
from smartrobot_state_client.state_reader import StateReader
from smartrobot_voice_input.voice_input import VoiceInput
from smartrobot_voice_input.whisper_asr import AUDIO_OUTPUT, cleanup_audio_file
from unitree_sdk2py.core.channel import ChannelFactoryInitialize


class SmartRobotPipeline:
    """编排语音输入、智能体决策和技能执行的完整流程。"""

    def __init__(self, use_whisper=False):
        self.voice = VoiceInput(use_whisper=use_whisper)
        self.state_reader = StateReader()
        self.place_memory = PlaceMemory()
        self.skills = SkillController(
            place_memory=self.place_memory,
            state_reader=self.state_reader,
        )
        self.agent = AgentController()

    def step(self, user_text):
        state = self.state_reader.get_state()
        action_packet, raw_llm = self.agent.decide(
            user_text=user_text,
            state=state,
            place_memory=self.place_memory.all_places(),
            skill_registry=self.skills.skill_registry,
        )
        result = self.skills.run_action(action_packet)
        self.agent.remember_result(
            task=user_text,
            state=state,
            action_packet=action_packet,
            result=result,
        )
        return action_packet, result, raw_llm

    def close(self):
        self.state_reader.close()
        cleanup_audio_file(AUDIO_OUTPUT)


def main():
    use_whisper = os.getenv("SMARTROBOT_USE_WHISPER", "0").strip() == "1"
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    pipeline = SmartRobotPipeline(use_whisper=use_whisper)
    try:
        while True:
            user_text = pipeline.voice.read_user_text()
            if not user_text:
                continue
            print(f"Input: {user_text}")
            try:
                action_packet, result, raw_llm = pipeline.step(user_text)
                print(f"LLM raw: {raw_llm}")
                print(f"Action packet: {action_packet}")
                print(f"Skill result: {result}")
            except Exception as err:
                print(f"Pipeline error: {err}")
            time.sleep(DEFAULT_DURATION)
    finally:
        pipeline.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user.")
