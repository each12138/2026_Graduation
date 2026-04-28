import os

import requests
from requests import RequestException

DEFAULT_API_KEY = "sk-483e5a66ad1b46a89f78cf6c65c5d550"
DEFAULT_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT = 20


class LLMClient:
    def __init__(
        self,
        api_key=None,
        api_url=DEFAULT_API_URL,
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", DEFAULT_API_KEY)
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def generate(self, prompt):
        if not self.api_key:
            raise RuntimeError("missing_api_key")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}],
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
        except RequestException as err:
            raise RuntimeError(f"LLM request failed: {err}") from err
        except ValueError as err:
            raise RuntimeError(f"LLM response JSON invalid: {err}") from err

        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("LLM response missing choices")

        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("LLM response missing message content")
        return content
