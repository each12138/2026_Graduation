"""最小化大模型连通性测试脚本。"""

import requests

# 复用当前项目的接口配置
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-483e5a66ad1b46a89f78cf6c65c5d550"
MODEL = "deepseek-chat"


def test_llm_connection():
	headers = {
		"Authorization": f"Bearer {API_KEY}",
		"Content-Type": "application/json",
	}
	payload = {
		"model": MODEL,
		"messages": [{"role": "user", "content": "请只回复: ok"}],
		"temperature": 0,
	}

	response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
	response.raise_for_status()

	data = response.json()
	content = data["choices"][0]["message"]["content"]
	return content


if __name__ == "__main__":
	try:
		reply = test_llm_connection()
		print("LLM连接成功")
		print(f"模型回复: {reply}")
	except Exception as e:
		print("LLM连接失败")
		print(f"错误信息: {e}")
