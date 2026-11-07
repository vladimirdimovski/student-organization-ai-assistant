# USD per million tokens — verify against Anthropic's pricing page
PRICES = {
    "claude-haiku-5-5":  {"input": 0.10, "output": 0.50},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
    "claude-opus-5-5":   {"input": 4.00, "output": 20.00},
}
HAIKU_LONG_PROMPT = {"input": 0.50, "output": 2.50}   # Haiku prompts > 100K tokens


def request_cost(model: str, usage) -> float:
    prices = PRICES[model]
    if model == "claude-haiku-5-5" and usage.input_tokens > 100_000:
        prices = HAIKU_LONG_PROMPT
    return (usage.input_tokens * prices["input"]
            + usage.output_tokens * prices["output"]) / 1_000_000