from dataclasses import dataclass
from typing import Literal

Provider = Literal["groq", "gemini"]

@dataclass
class ModelResult:
    text: str
    provider: str
    model: str
    fallback_used: bool = False
    error: str | None = None
