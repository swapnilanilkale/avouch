"""Groq target adapter.

Wraps the Groq SDK so that Groq-hosted models can be used through Avouch's
standard TargetAdapter interface.
"""

from groq import APIError, Groq, RateLimitError

from avouch.adapters.base import AdapterError, LLMResponse, TargetAdapter
from avouch.adapters.retry import with_backoff
from avouch.config import get_settings

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqAdapter(TargetAdapter):
    """A TargetAdapter backed by the Groq API."""

    def __init__(self, model: str = DEFAULT_GROQ_MODEL) -> None:
        """Create a Groq adapter.

        Args:
            model: The Groq model identifier to send prompts to.
        """
        self._model = model
        settings = get_settings()
        self._client = Groq(api_key=settings.groq_api_key)

    @property
    def name(self) -> str:
        """Return a human-readable identifier for this adapter."""
        return f"groq:{self._model}"

    def generate(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a prompt to the Groq model and return a normalized response.

        Args:
            prompt: The text prompt to send.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the generated text and metadata.

        Raises:
            AdapterError: If the Groq API call fails.
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
        except APIError as exc:
            raise AdapterError(f"Groq API call failed: {exc}") from exc

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="groq",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            raw=completion,
        )

    def generate_conversation(
        self, messages: list[dict[str, str]], temperature: float = 0.7
    ) -> LLMResponse:
        """Send a full message history to Groq as a native conversation.

        Overrides the base fallback: the messages are passed directly to the
        chat completions API, so the model responds with true multi-turn
        context rather than a flattened prompt.

        Args:
            messages: Conversation history as role/content dicts.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the model's reply and metadata.

        Raises:
            AdapterError: If the Groq API call fails.
        """

        @with_backoff((RateLimitError,))
        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
            )

        try:
            completion = _call()
        except APIError as exc:
            raise AdapterError(f"Groq API call failed: {exc}") from exc

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="groq",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            raw=completion,
        )
