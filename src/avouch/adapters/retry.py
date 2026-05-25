"""Shared retry policy for target adapters.

Provider APIs intermittently return rate-limit (429) or transient server
errors. This module defines a single reusable retry decorator that applies
exponential backoff, so every adapter handles these failures consistently.
"""

import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 4


def with_backoff(exception_types: tuple[type[Exception], ...]):
    """Build a retry decorator for the given provider exception types.

    The returned decorator retries a function call when it raises one of the
    listed exceptions, waiting 2s, then 4s, then 8s between attempts, up to
    MAX_ATTEMPTS total tries. If every attempt fails, the original exception
    propagates and the adapter converts it into an AdapterError.

    Args:
        exception_types: Provider exception classes that should trigger a retry.

    Returns:
        A configured tenacity retry decorator.
    """
    return retry(
        retry=retry_if_exception_type(exception_types),
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        before_sleep=lambda state: logger.warning(
            "Provider call failed (attempt %d/%d); retrying after backoff...",
            state.attempt_number,
            MAX_ATTEMPTS,
        ),
        reraise=True,
    )
