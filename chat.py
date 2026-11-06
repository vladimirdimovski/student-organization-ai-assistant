from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

MODEL = "claude-haiku-5-5"
SYSTEM = ("You are a helpful assistant for AIESEC in North Macedonia. "
          "Reply in the language the user writes in.")

history = []   # the API is stateless: this list IS the conversation

while True:
    user_input = input("\nYou: ").strip()
    if user_input.lower() in {"exit", "quit", "излез"}:
        break
    if not user_input:
        continue

    history.append({"role": "user", "content": user_input})

    print("Claude: ", end="", flush=True)
    with client.messages.stream(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=history,
    ) as stream:
        for text in stream.text_stream:      # yields only text, skips thinking
            print(text, end="", flush=True)
        final = stream.get_final_message()

    # send back the full content (including thinking blocks + signatures)
    history.append({"role": "assistant", "content": final.content})

    u = final.usage
    print(f"\n[stop={final.stop_reason} in={u.input_tokens} out={u.output_tokens}]")