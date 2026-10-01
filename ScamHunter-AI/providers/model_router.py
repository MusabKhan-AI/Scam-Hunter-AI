from __future__ import annotations

from config.models import ModelResult
from config.settings import Settings
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider


class ModelRouter:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.groq = GroqProvider(
            settings.groq_api_key,
            settings.groq_model,
        )

        self.gemini = GeminiProvider(
            settings.gemini_api_key,
            settings.gemini_models,
        )

    def groq_complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
    ) -> ModelResult:
        return self.groq.complete(
            prompt,
            system,
            temperature,
        )

    def gemini_complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
    ) -> ModelResult:
        return self.gemini.complete(
            prompt,
            system,
            temperature,
        )

    @property
    def has_any_provider(self) -> bool:
        return bool(
            self.settings.groq_api_key
            or self.settings.gemini_api_key
        )

    def describe_image(
        self,
        data: bytes,
        mime_type: str,
        prompt: str,
    ) -> ModelResult:
        """Vision is only available through Gemini."""
        return self.gemini.describe_image(data, mime_type, prompt)

    def best_available(
        self,
        prompt: str,
        system: str = "",
        prefer_gemini: bool = False,
    ) -> ModelResult:

        errors = []

        # -----------------------------------------
        # 1. Try Gemini first when requested
        # -----------------------------------------
        if prefer_gemini and self.settings.gemini_api_key:
            try:
                return self.gemini_complete(
                    prompt,
                    system,
                )
            except Exception as exc:
                errors.append(
                    f"Gemini failed: {type(exc).__name__}: {exc}"
                )

        # -----------------------------------------
        # 2. Try Groq
        # -----------------------------------------
        if self.settings.groq_api_key:
            try:
                return self.groq_complete(
                    prompt,
                    system,
                )
            except Exception as exc:
                errors.append(
                    f"Groq failed: {type(exc).__name__}: {exc}"
                )

        # -----------------------------------------
        # 3. If Gemini was not preferred,
        #    try Gemini as final fallback
        # -----------------------------------------
        if (
            not prefer_gemini
            and self.settings.gemini_api_key
        ):
            try:
                return self.gemini_complete(
                    prompt,
                    system,
                )
            except Exception as exc:
                errors.append(
                    f"Gemini fallback failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # -----------------------------------------
        # 4. Nothing worked
        # -----------------------------------------
        if errors:
            raise RuntimeError(
                "All configured AI providers failed.\n\n"
                + "\n".join(errors)
            )

        raise RuntimeError(
            "No AI provider is configured. "
            "Please configure GEMINI_API_KEY or GROQ_API_KEY."
        )
