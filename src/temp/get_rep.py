"""Temporary helper to inspect the raw LLM response for a prompt."""

from agent import prompt as react_prompt
from utils.llm import LLM


class DummyStateClient:
    """Minimal state client for prompt generation tests."""

    def get_state(self):
        return {}


def get_rep(input_text="站起来"):
    state_client = DummyStateClient()
    llm = LLM()

    current_state = state_client.get_state()
    prompt_use = react_prompt.build_prompt(current_state, input_text, [])
    llm_response = llm.generate(prompt_use)

    print("识别文本:", input_text)
    print("模型原始返回:", llm_response)
    return llm_response


if __name__ == "__main__":
    get_rep("站起来")
