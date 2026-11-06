from dotenv import load_dotenv
import anthropic

load_dotenv()                      # loads ANTHROPIC_API_KEY from .env
client = anthropic.Anthropic()     # the SDK reads the key from the environment

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=2000,
    # system="You are a helpful assistant for AIESEC in North Macedonia. "
    #        "Reply in the language the user writes in.",
    messages=[
        {"role": "user", "content": "What is AIESEC?"}
    ],
)

print("block types:", [block.type for block in response.content])

answer = "".join(block.text for block in response.content if block.type == "text")
if response.stop_reason == "max_tokens":
    print(f"⚠️ Truncated: hit max_tokens ({response.usage.output_tokens} output tokens used)")
if not answer:
    print("⚠️ No text block in the response")
print(answer)
print("\n--- raw response ---")
print(response.model_dump_json(indent=2))