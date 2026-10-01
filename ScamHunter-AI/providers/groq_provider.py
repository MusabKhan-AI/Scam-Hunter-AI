from __future__ import annotations
from config.models import ModelResult

class GroqProvider:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = None
        if api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
            except Exception:
                self.client = None

    def complete(self, prompt: str, system: str = "", temperature: float = 0.2) -> ModelResult:
        if not self.client:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return ModelResult(r.choices[0].message.content or "", "groq", self.model)
