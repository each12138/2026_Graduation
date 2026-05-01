import os

import requests
from requests import RequestException

API_KEY = os.getenv("GO2_LLM_API_KEY", "sk-483e5a66ad1b46a89f78cf6c65c5d550")
API_URL = os.getenv("GO2_LLM_API_URL", "https://api.deepseek.com/v1/chat/completions")
MODEL = os.getenv("GO2_LLM_MODEL", "deepseek-chat")

TEMPERATURE = 0.2
DEFAULT_TIMEOUT = 20


class LLM:
    def __init__(
        self,
        api_key=API_KEY,
        api_url=API_URL,
        model=MODEL,
        temperature=TEMPERATURE,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def generate(self, prompt):
        messages = [{"role": "system", "content": prompt}]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "options": {"format": "json"},
        }
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            response_data = response.json()
        except RequestException as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError(f"LLM response is not valid JSON: {exc}") from exc

        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("LLM response missing choices")

        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("LLM response missing message content")

        return content
