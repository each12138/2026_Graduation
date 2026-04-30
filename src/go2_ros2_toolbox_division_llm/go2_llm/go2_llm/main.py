#!/usr/bin/env python3

import os
import sys
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

if __package__ is None or __package__ == "":
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)

    from go2_llm.agent.react_agent import ReActAgent
    from go2_llm.skills.map import SemanticMap
    from go2_llm.skills.skill_executor import SkillExecutor
    from go2_llm.skills.skill_manager import DEFAULT_DURATION
    from go2_llm.utils.llm import LLM
    from go2_llm.utils.state import StateReader
    from go2_llm.utils.whisper_asr import AUDIO_OUTPUT
else:
    from .agent.react_agent import ReActAgent
    from .skills.map import SemanticMap
    from .skills.skill_executor import SkillExecutor
    from .skills.skill_manager import DEFAULT_DURATION
    from .utils.llm import LLM
    from .utils.state import StateReader
    from .utils.whisper_asr import AUDIO_OUTPUT


def build_sport_client():
    sport_client = SportClient()
    sport_client.SetTimeout(10.0)
    sport_client.Init()
    return sport_client


def build_runtime():
    semantic_map = SemanticMap()
    state_reader = StateReader()
    llm = LLM()
    sport_client = build_sport_client()
    skill_executor = SkillExecutor(
        sport_client=sport_client,
        semantic_map=semantic_map,
        state_reader=state_reader,
    )
    react_agent = ReActAgent(
        llm=llm,
        state_reader=state_reader,
        skill_executor=skill_executor,
        semantic_map=semantic_map,
    )
    return react_agent, state_reader


def cleanup_audio_file():
    if os.path.exists(AUDIO_OUTPUT):
        os.remove(AUDIO_OUTPUT)


def main():
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    react_agent, state_reader = build_runtime()

    try:
        while True:
            transcribed_text = input("请输入指令：")
            if not transcribed_text:
                continue

            print(f"识别到指令：{transcribed_text}")
            try:
                result = react_agent.step(transcribed_text)
                print(f"执行结果：{result}")
                time.sleep(DEFAULT_DURATION)
            except Exception as exc:
                print(f"处理指令失败，错误：{exc}")
    finally:
        if state_reader is not None:
            try:
                state_reader.close()
            except Exception as close_error:
                print(f"关闭状态读取器失败：{close_error}")

        cleanup_audio_file()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n识别结束，程序已退出。")
        cleanup_audio_file()
