"""Adapter registry.

Maps provider names to adapter classes and provides a single factory
function for obtaining a ready-to-use TargetAdapter by name. Other modules
request adapters through this registry rather than importing adapter
classes directly.
"""

from avouch.adapters.base import TargetAdapter
from avouch.adapters.cerebras_adapter import CerebrasAdapter
from avouch.adapters.gemini_adapter import GeminiAdapter
from avouch.adapters.groq_adapter import GroqAdapter
from avouch.adapters.openrouter_adapter import OpenRouterAdapter

_ADAPTER_REGISTRY: dict[str, type[TargetAdapter]] = {
    "groq": GroqAdapter,
    "gemini": GeminiAdapter,
    "openrouter": OpenRouterAdapter,
    "cerebras": CerebrasAdapter,
}


def available_providers() -> list[str]:
    """Return the sorted list of registered provider names."""
    return sorted(_ADAPTER_REGISTRY)


def get_adapter(provider: str, model: str | None = None) -> TargetAdapter:
    """Return a ready-to-use adapter for the named provider.

    Args:
        provider: The provider name, e.g. "groq" or "cerebras".
        model: Optional model identifier. If omitted, the adapter's own
            default model is used.

    Returns:
        An instantiated TargetAdapter for the requested provider.

    Raises:
        ValueError: If the provider name is not registered.
    """
    key = provider.strip().lower()
    adapter_class = _ADAPTER_REGISTRY.get(key)

    if adapter_class is None:
        valid = ", ".join(available_providers())
        raise ValueError(
            f"Unknown provider '{provider}'. Valid providers are: {valid}."
        )

    if model is not None:
        return adapter_class(model=model)
    return adapter_class()