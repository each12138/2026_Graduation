import json
import os
import re
from typing import Any

import requests


class LLMClient:
    # 这里封装认知层对 LLM 的访问，当前主要用于导航意图辅助解析。
    def __init__(self, runtime_cfg: dict) -> None:
        llm_cfg = runtime_cfg.get("llm", {})
        self.enabled = bool(llm_cfg.get("enabled", False))
        self.api_url = str(llm_cfg.get("api_url", "")).strip()
        self.model = str(llm_cfg.get("model", "deepseek-chat")).strip()
        self.temperature = float(llm_cfg.get("temperature", 0.2))
        self.timeout_s = float(llm_cfg.get("timeout_s", 20))
        self.api_key = os.getenv(str(llm_cfg.get("api_key_env", "DEEPSEEK_API_KEY")))

    @staticmethod
    def _default_result(reason: str) -> dict[str, Any]:
        return {
            "intent": "unknown",
            "destination_id": None,
            "confidence": 0.0,
            "alternatives": [],
            "reason": reason,
        }

    @staticmethod
    def _extract_json_block(text: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if fenced:
            return fenced.group(1)

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text

    def _parse_response_content(self, content: str) -> dict[str, Any]:
        raw_json = self._extract_json_block(content)
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return self._default_result(f"unparsed_response:{content[:80]}")

        if not isinstance(payload, dict):
            return self._default_result("llm_response_not_dict")

        result = self._default_result("ok")
        intent = str(payload.get("intent", "unknown")).strip().lower() or "unknown"
        destination_id = payload.get("destination_id")
        confidence = payload.get("confidence", 0.0)
        alternatives = payload.get("alternatives", [])
        reason = str(payload.get("reason", "ok")).strip() or "ok"

        result["intent"] = intent
        result["destination_id"] = destination_id if isinstance(destination_id, str) else None
        try:
            result["confidence"] = float(confidence)
        except (TypeError, ValueError):
            result["confidence"] = 0.0
        result["alternatives"] = alternatives if isinstance(alternatives, list) else []
        result["reason"] = reason
        return result

    def parse_nav_intent(self, text: str, catalog: list[dict[str, Any]]) -> dict[str, Any]:
        # 如果没有启用 LLM，就明确回退给规则/候选排序链路处理。
        if not self.enabled or not self.api_key or not self.api_url:
            return self._default_result("llm_disabled")

        system_prompt = (
            "You are a navigation intent parser for a quadruped robot. "
            "You must return only JSON. "
            "Required keys: intent, destination_id, confidence, alternatives, reason. "
            "intent must be either 'navigate' or 'none'. "
            "destination_id must be one of the provided catalog IDs or null. "
            "confidence must be a number between 0 and 1. "
            "alternatives must be a list of destination IDs."
        )
        user_prompt = (
            f"Catalog: {json.dumps(catalog, ensure_ascii=False)}\n"
            f"User: {text}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=body, timeout=self.timeout_s)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return self._default_result("llm_request_failed")

        if not isinstance(data, dict):
            return self._default_result("llm_response_not_dict")

        try:
            content = str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError):
            return self._default_result(f"unexpected_response:{str(data)[:80]}")

        return self._parse_response_content(content)

    def generate_short_response(self, instruction: str) -> str:
        if not self.enabled:
            return instruction

        return instruction
