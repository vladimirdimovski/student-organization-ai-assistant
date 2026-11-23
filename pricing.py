# USD per million tokens — verify against Anthropic's pricing page
# read = what a cache hit costs as a fraction of the input price (Haiku 0.1, Sonnet and Opus 5.5 0.05)
PRICES = {
    "claude-haiku-5-5":  {"input": 0.10, "output": 0.50, "read": 0.10},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "read": 0.05},
    "claude-opus-5-5":   {"input": 4.00, "output": 20.00, "read": 0.05},
}
CACHE_WRITE = 1.25  # writing a 5-minute cache entry costs 1.25x the input price
HAIKU_LONG_PROMPT = {"input": 0.50, "output": 2.50}   # Haiku prompts > 100K tokens


def request_cost(model: str, usage) -> float:
    prices = PRICES[model]
    # with caching, input_tokens is only the part AFTER the cache breakpoint; the rest is reported
    # separately (both are 0 when caching is off, so old callers get the same numbers as before)
    written = getattr(usage, "cache_creation_input_tokens", 0) or 0
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    if model == "claude-haiku-5-5" and usage.input_tokens + written + read > 100_000:
        prices = {**HAIKU_LONG_PROMPT, "read": prices["read"]}
    return (usage.input_tokens * prices["input"]
            + written * prices["input"] * CACHE_WRITE
            + read * prices["input"] * prices["read"]
            + usage.output_tokens * prices["output"]) / 1_000_000