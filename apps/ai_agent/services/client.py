"""Thin wrapper around the Anthropic SDK.

The SDK is imported lazily so the rest of the project does not hard-require it
at import time. Install with: pip install anthropic
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

# Per-million-token pricing (USD). Update when Anthropic pricing changes.
PRICING = {
    "claude-opus-4-7":    {"in": Decimal("15"),   "out": Decimal("75"),  "cache_read": Decimal("1.5"),  "cache_write": Decimal("18.75")},
    "claude-sonnet-4-6":  {"in": Decimal("3"),    "out": Decimal("15"),  "cache_read": Decimal("0.3"),  "cache_write": Decimal("3.75")},
    "claude-haiku-4-5":   {"in": Decimal("1"),    "out": Decimal("5"),   "cache_read": Decimal("0.1"),  "cache_write": Decimal("1.25")},
}

DEFAULT_MODEL = "claude-sonnet-4-6"


def get_client():
    from anthropic import Anthropic  # lazy import
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Anthropic(api_key=api_key)


def estimate_cost(model: str, usage: dict[str, int]) -> Decimal:
    p = PRICING.get(model)
    if not p:
        return Decimal("0")
    return (
        p["in"]          * Decimal(usage.get("input_tokens", 0))
        + p["out"]         * Decimal(usage.get("output_tokens", 0))
        + p["cache_read"]  * Decimal(usage.get("cache_read_input_tokens", 0))
        + p["cache_write"] * Decimal(usage.get("cache_creation_input_tokens", 0))
    ) / Decimal("1000000")
