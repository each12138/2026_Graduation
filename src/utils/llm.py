import requests

# ------------------ AI 接口配置 -----------------
API_KEY = "sk-483e5a66ad1b46a89f78cf6c65c5d550"
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

temperature = 0.2

class LLM:
    def __init__(self, api_key=API_KEY, api_url=API_URL, model=MODEL, temperature=temperature):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.temperature = temperature

    def generate(self, prompt):
        messages = [
            {"role": "system", "content": prompt}
        ]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json" 
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "options": {"format": "json"}
        }
        response = requests.post(
                self.api_url, 
                headers=headers, 
                json=data
        )
        response_data = response.json()
        return response_data['choices'][0]['message']['content']