"""OpenRouter target adapter.

OpenRouter exposes an OpenAI-compatible API, so this adapter uses the
standard OpenAI SDK pointed at OpenRouter's endpoint. Only models with a
':free' suffix are used, to stay within the free tier.
"""

from openai import OpenAI, OpenAIError, RateLimitError

from avouch.adapters.base import AdapterError, LLMResponse, TargetAdapter
from avouch.adapters.retry import with_backoff
from avouch.config import get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"


class OpenRouterAdapter(TargetAdapter):
    """A TargetAdapter backed by the OpenRouter API."""

    def __init__(self, model: str = DEFAULT_OPENROUTER_MODEL) -> None:
        """Create an OpenRouter adapter.

        Args:
            model: The OpenRouter model identifier. Should end in ':free'.
        """
        self._model = model
        settings = get_settings()
        self._client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=settings.openrouter_api_key,
        )

    @property
    def name(self) -> str:
        """Return a human-readable identifier for this adapter."""
        return f"openrouter:{self._model}"

    def generate(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a prompt to the OpenRouter model and return a response.

        Args:
            prompt: The text prompt to send.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the generated text and metadata.

        Raises:
            AdapterError: If the OpenRouter API call fails.
        """

        @with_backoff((RateLimitError,))
        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

        try:
            completion = _call()
        except OpenAIError as exc:
            raise AdapterError(f"OpenRouter API call failed: {exc}") from exc

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="openrouter",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            raw=completion,
        )
