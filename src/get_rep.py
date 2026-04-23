"""临时脚本：用最少依赖复用正式 ReAct 流程并获取模型回复。"""

import global_vars
from agent import prompt as react_prompt
from utils.llm import LLM


class DummyStateClient:
	"""仅提供 ReAct 所需状态接口。"""

	def get_state(self):
		return {}


def get_rep(input_text="站起来"):
	# 只初始化与模型交互必需的对象。
	global_vars.state_client = DummyStateClient()
	global_vars.llm = LLM()

	# 非必要全局对象明确置空。
	global_vars.map = None
	global_vars.react_agent = None
	global_vars.skill_executor = None

	current_state = global_vars.state_client.get_state()
	prompt_use = react_prompt.build_prompt(current_state, input_text, [])
	llm_response = global_vars.llm.generate(prompt_use)

	print("识别文本:", input_text)
	print("模型原始返回:", llm_response)
	return llm_response


if __name__ == "__main__":
	get_rep("站起来")
