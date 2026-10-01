from __future__ import annotations

from config.models import ModelResult


def _is_missing_model(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "404" in text or "not found" in text or "not_found" in text


class GeminiProvider:
    def __init__(self, api_key: str, models: tuple[str, ...]):
        self.api_key = api_key
        self.models = models
        self.client = None
        # Model names that the API said do not exist. They are skipped for the
        # rest of the process so a wrong name never slows every request down.
        self._dead: set[str] = set()
        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except Exception:
                self.client = None

    def _candidates(self) -> list[tuple[int, str]]:
        live = [(i, m) for i, m in enumerate(self.models) if m not in self._dead]
        return live or list(enumerate(self.models))

    def complete(self, prompt: str, system: str = "", temperature: float = 0.2) -> ModelResult:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        if not self.client:
            raise RuntimeError("Gemini SDK could not be initialized.")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        last_error = None
        for i, model in self._candidates():
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={"temperature": temperature},
                )
                text = getattr(response, "text", None) or ""
                if not text.strip():
                    raise RuntimeError("Gemini returned an empty response.")
                return ModelResult(text, "gemini", model, fallback_used=(i > 0))
            except Exception as exc:
                if _is_missing_model(exc):
                    self._dead.add(model)
                last_error = exc
                continue
        raise RuntimeError(f"All Gemini fallback models failed: {last_error}")

    def describe_image(self, data: bytes, mime_type: str, prompt: str) -> ModelResult:
        """Send an image + instruction to Gemini (used for screenshot analysis)."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        if not self.client:
            raise RuntimeError("Gemini SDK could not be initialized.")

        from google.genai import types

        part = types.Part.from_bytes(data=data, mime_type=mime_type)
        last_error = None
        for i, model in self._candidates():
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[part, prompt],
                    config={"temperature": 0.1},
                )
                text = getattr(response, "text", None) or ""
                if not text.strip():
                    raise RuntimeError("Gemini returned an empty response.")
                return ModelResult(text, "gemini", model, fallback_used=(i > 0))
            except Exception as exc:
                if _is_missing_model(exc):
                    self._dead.add(model)
                last_error = exc
                continue
        raise RuntimeError(f"Image analysis failed on all Gemini models: {last_error}")
