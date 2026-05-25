"""Gemini target adapter.

Wraps Google's google-genai SDK so that Gemini models can be used through
Avouch's standard TargetAdapter interface.
"""

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from avouch.adapters.base import AdapterError, LLMResponse, TargetAdapter
from avouch.adapters.retry import with_backoff
from avouch.config import get_settings

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"


class GeminiAdapter(TargetAdapter):
    """A TargetAdapter backed by the Google Gemini API."""

    def __init__(self, model: str = DEFAULT_GEMINI_MODEL) -> None:
        """Create a Gemini adapter.

        Args:
            model: The Gemini model identifier to send prompts to.
        """
        self._model = model
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)

    @property
    def name(self) -> str:
        """Return a human-readable identifier for this adapter."""
        return f"gemini:{self._model}"

    def generate(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a prompt to the Gemini model and return a response.

        Args:
            prompt: The text prompt to send.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the generated text and metadata.

        Raises:
            AdapterError: If the Gemini API call fails.
        """

        @with_backoff((genai_errors.ClientError, genai_errors.ServerError))
        def _call():
            return self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(temperature=temperature),
            )

        try:
            response = _call()
        except genai_errors.APIError as exc:
            raise AdapterError(f"Gemini API call failed: {exc}") from exc

        usage = response.usage_metadata

        return LLMResponse(
            text=response.text or "",
            model=self._model,
            provider="gemini",
            prompt_tokens=usage.prompt_token_count if usage else None,
            completion_tokens=usage.candidates_token_count if usage else None,
            raw=response,
        )
