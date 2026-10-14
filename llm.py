"""Small Groq client with automatic fallback when a model has been retired."""

from __future__ import annotations

import json
import re

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.1-8b-instant"]


class ModelNotFound(Exception):
    pass


class LLM:
    """Remembers which model worked, so later calls go straight to it."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    def _post(self, model, messages, temperature, json_mode):
        body = {"model": model, "temperature": temperature, "messages": messages}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        return requests.post(GROQ_URL, json=body, timeout=90,
                             headers={"Authorization": f"Bearer {self.api_key}",
                                      "Content-Type": "application/json"})

    def _call(self, model, messages, temperature, json_mode) -> str:
        resp = self._post(model, messages, temperature, json_mode)
        if resp.status_code == 400 and json_mode:
            resp = self._post(model, messages, temperature, False)
        if resp.status_code == 404:
            raise ModelNotFound(model)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except ValueError:
                detail = resp.text
            raise RuntimeError(f"Groq API error {resp.status_code}: {detail}")
        return resp.json()["choices"][0]["message"]["content"]

    def chat(self, messages: list[dict], temperature: float = 0.7, json_mode: bool = False) -> str:
        for m in [self.model] + [f for f in FALLBACK_MODELS if f != self.model]:
            try:
                out = self._call(m, messages, temperature, json_mode)
                self.model = m
                return out
            except ModelNotFound:
                continue
        raise RuntimeError("None of the Groq models are available.")


def parse_json(text: str) -> dict:
    """Parse model output, tolerating code fences or extra text around the JSON."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return JSON.")
    return json.loads(text[start:end + 1])
