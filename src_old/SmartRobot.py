import time
import sys
import os
import global_vars

from utils.whisper_asr import record_audio, transcribe_audio, AUDIO_OUTPUT
from utils.state import GetState
from utils.llm import LLM
from skills.skill_manager import DEFAULT_DURATION
from skills.skill_executor import SkillExecutor
from agent.react_agent import ReActAgent
from skills.map import SemanticMap

from unitree_sdk2py.core.channel import ChannelFactoryInitialize


def main():
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    global_vars.map = SemanticMap()
    global_vars.state_client = GetState()
    global_vars.llm = LLM()
    global_vars.skill_executor = SkillExecutor(
        semantic_map=global_vars.map,
        state_client=global_vars.state_client,
    )
    global_vars.react_agent = ReActAgent(
        llm=global_vars.llm,
        state_client=global_vars.state_client,
        skill_executor=global_vars.skill_executor,
        semantic_map=global_vars.map,
    )

    try:
        while True:
            # record_audio(AUDIO_OUTPUT)
            # transcribed_text = transcribe_audio(AUDIO_OUTPUT)
            transcribed_text = input("请输入指令：")  # 替代语音输入，方便测试
            if transcribed_text:
                print(f"🎤 识别到指令：{transcribed_text}")
                # 调用AI进行响应
                try:
                    result = global_vars.react_agent.step(transcribed_text)
                    print(f"执行结果：{result}")
                    time.sleep(DEFAULT_DURATION)  # 每个技能执行后等待默认时长

                except Exception as e:
                    print(f"❌ 处理指令失败，错误：{e}")
    finally:
        if getattr(global_vars, "state_client", None) is not None:
            try:
                global_vars.state_client.close()
            except Exception as close_error:
                print(f"关闭状态客户端失败：{close_error}")

        if os.path.exists(AUDIO_OUTPUT):
            os.remove(AUDIO_OUTPUT)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 识别结束，程序已退出。")
        if os.path.exists(AUDIO_OUTPUT):
            os.remove(AUDIO_OUTPUT)
