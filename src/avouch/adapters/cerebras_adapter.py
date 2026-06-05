"""Cerebras target adapter.

Cerebras exposes an OpenAI-compatible API, so this adapter uses the standard
OpenAI SDK pointed at the Cerebras endpoint.
"""

from typing import TYPE_CHECKING, cast

from openai import OpenAI, OpenAIError, RateLimitError

from avouch.adapters.base import AdapterError, LLMResponse, TargetAdapter
from avouch.adapters.retry import with_backoff
from avouch.config import get_settings

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam


CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"


class CerebrasAdapter(TargetAdapter):
    """A TargetAdapter backed by the Cerebras inference API."""

    def __init__(self, model: str = DEFAULT_CEREBRAS_MODEL) -> None:
        """Create a Cerebras adapter.

        Args:
            model: The Cerebras model identifier to send prompts to.
        """
        self._model = model
        settings = get_settings()
        self._client = OpenAI(
            base_url=CEREBRAS_BASE_URL,
            api_key=settings.cerebras_api_key,
        )

    @property
    def name(self) -> str:
        """Return a human-readable identifier for this adapter."""
        return f"cerebras:{self._model}"

    def generate(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a prompt to the Cerebras model and return a response.

        Args:
            prompt: The text prompt to send.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the generated text and metadata.


        Raises:
            AdapterError: If the Cerebras API call fails.
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
            raise AdapterError(f"Cerebras API call failed: {exc}") from exc

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="cerebras",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            raw=completion,
        )

    def generate_conversation(
        self, messages: list[dict[str, str]], temperature: float = 0.7
    ) -> LLMResponse:
        """Send a full message history to Cerebras as a native conversation.

        Overrides the base fallback: the messages are passed directly to the
        chat completions API, so the model responds with true multi-turn
        context rather than a flattened prompt.

        Args:
            messages: Conversation history as role/content dicts.
            temperature: Sampling temperature.

        Returns:
            An LLMResponse with the model's reply and metadata.

        Raises:
            AdapterError: If the Cerebras API call fails.
        """

        typed_messages = cast("list[ChatCompletionMessageParam]", messages)

        @with_backoff((RateLimitError,))
        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                messages=typed_messages,
                temperature=temperature,
            )

        try:
            completion = _call()
        except OpenAIError as exc:
            raise AdapterError(f"Cerebras API call failed: {exc}") from exc

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            provider="cerebras",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            raw=completion,
        )
