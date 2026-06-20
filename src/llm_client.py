from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI


class LLMError(RuntimeError):
    """Raised when an OpenAI request or response cannot be processed."""


class LLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise LLMError("API Key가 비어 있습니다.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def request_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
            )
            text = response.output_text.strip()
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        if not text:
            raise LLMError("모델이 빈 응답을 반환했습니다.")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
            if fenced:
                try:
                    return json.loads(fenced.group(1))
                except json.JSONDecodeError:
                    pass

        return {
            "summary": "모델 응답을 구조화된 JSON으로 변환하지 못했습니다.",
            "markdown": text,
            "issues": [],
        }
