"""The target adapter contract.

This module defines the abstract interface that every LLM adapter must
implement. Agents in Avouch interact only with this interface, never with
a specific provider's SDK. Adding support for a new provider means writing
one new adapter that fulfils this contract -- nothing else changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class AdapterError(Exception):
    """Raised when a target adapter fails to produce a response.

    Each concrete adapter catches its provider's SDK-specific exceptions
    and re-raises them as AdapterError, so that calling code handles a
    single, consistent error type.
    """


@dataclass
class LLMResponse:
    """A normalized response from any LLM target.

    Attributes:
        text: The text content the model generated.
        model: The identifier of the model that produced the response.
        provider: The provider name (e.g. "groq", "gemini").
        prompt_tokens: Tokens consumed by the prompt, if reported.
        completion_tokens: Tokens consumed by the completion, if reported.
        raw: The provider's original response object, kept for debugging.
    """

    text: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw: object = field(default=None, repr=False)


class TargetAdapter(ABC):
    """Abstract contract for any LLM that Avouch can send prompts to.

    A concrete adapter wraps one provider (Groq, Gemini, OpenRouter, or a
    custom endpoint) and translates between Avouch's standard interface and
    that provider's specific SDK.
    """

    @abstractmethod
    def __init__(self, model: str | None = None) -> None:
        """Initialize the adapter.

        Args:
            model: Optional model identifier. If None, the concrete adapter
                uses its own provider-specific default model.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """A human-readable identifier, e.g. 'groq:llama-3.3-70b-versatile'."""

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a single prompt to the target model and return its response.

        Args:
            prompt: The text prompt to send to the model.
            temperature: Sampling temperature; higher means more random output.

        Returns:
            An LLMResponse containing the generated text and metadata.

        Raises:
            AdapterError: If the provider call fails for any reason.
        """

    def generate_conversation(
        self, messages: list[dict[str, str]], temperature: float = 0.7
    ) -> LLMResponse:
        """Send a multi-message conversation and return the model's reply.

        Unlike generate(), which sends a single prompt, this sends a full
        message history (a list of {"role": ..., "content": ...} dicts) so the
        model responds in the context of an ongoing dialogue. This supports
        multi-turn red-teaming, where adversarial pressure builds across turns.

        Args:
            messages: Conversation history as a list of role/content dicts.
                Roles are "system", "user", or "assistant".
            temperature: Sampling temperature.

        Returns:
            An LLMResponse containing the model's reply and metadata.

        Raises:
            AdapterError: If the provider call fails for any reason.
        """
