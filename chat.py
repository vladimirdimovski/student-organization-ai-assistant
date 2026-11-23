import re
import sys
from dotenv import load_dotenv
from pricing import request_cost
from grounding import build_system
from checks import check
import anthropic

# Windows consoles default to cp1252, which cannot print Cyrillic (stdin matters for piped input)
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

load_dotenv()
client = anthropic.Anthropic(max_retries=3, timeout=60.0)

MODEL = "claude-haiku-5-5"
SYSTEM = build_system()   # rules + style guide + site pages, see grounding.py

history = []   # the API is stateless: this list IS the conversation

session = {"in": 0, "out": 0, "thinking":0, "cost": 0.0}

GATE = ["no_mixed", "no_latin"]   # a failed check in this list triggers one rewrite, see checks.py
# If the visitor asks for English or Latin-script text, Latin letters in the answer are what they asked for
WANTS_LATIN = re.compile(r"англиск|латиниц|превед|превод|english|latin|translat", re.I)

turn = {"in": 0, "out": 0, "thinking": 0, "cost": 0.0}   # totals for one visitor message, reset each time


def ask(messages):
    """One request, no streaming: the answer must be complete before we can check it.
    It is billed the moment it returns, so a failure later in the same turn cannot lose it."""
    r = client.messages.create(model=MODEL, max_tokens=2000, system=SYSTEM, messages=messages)
    u = r.usage
    thinking = getattr(getattr(u, "output_tokens_details", None), "thinking_tokens", 0) or 0
    cost = request_cost(MODEL, u)
    for totals in (turn, session):
        totals["in"] += u.input_tokens
        totals["out"] += u.output_tokens
        totals["thinking"] += thinking
        totals["cost"] += cost
    return r


def typed_so_far():
    """Latin words the visitor has typed in any message so far; the model may repeat them."""
    said = " ".join(m["content"] for m in history if m["role"] == "user")
    return " ".join(re.findall(r"[A-Za-z\u00C0-\u024F]+", said))


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")   # by block type, never by index


while True:
    try:
        user_input = input("\nYou: ").strip()
    except EOFError:  # piped input ran out, or Ctrl+Z in the terminal: end like "exit"
        break
    if user_input.lower() in {"exit", "quit", "излез"}:
        break
    if not user_input:
        continue

    history.append({"role": "user", "content": user_input})
    turn.update({"in": 0, "out": 0, "thinking": 0, "cost": 0.0})
    asked = user_input + " " + typed_so_far()   # the Latin words add to the allowed list, nothing else

    try:
        final = ask(history)
        gate = ["no_mixed"] if WANTS_LATIN.search(user_input) else GATE
        results, details = check(asked, text_of(final))
        retried = any(not results[c] for c in gate)
        if retried:
            broke = details
            hint = ""
            if re.search(r"[\u0400-\u04FF]", user_input) and not WANTS_LATIN.search(user_input):
                hint = " The visitor wrote in Macedonian, so the whole answer must be in Macedonian, in Cyrillic."
            # the bad answer goes into THIS request only, never into history
            final = ask(history + [
                {"role": "assistant", "content": final.content},
                {"role": "user", "content": f"Your answer broke a rule ({details[:150]}).{hint} Rewrite it with "
                                            "the same content and follow all the style rules, unless the "
                                            "visitor asked for English or Latin-script text: then keep that "
                                            "text. Reply with the rewritten answer only."},
            ])
            results, details = check(asked, text_of(final))
    except anthropic.AuthenticationError:
        print("\n[error] Invalid API key, check .env")
        break  # retrying won't help
    except anthropic.RateLimitError:
        history.pop()  # drop the unanswered user turn
        print("\n[error] Still rate-limited after retries, wait and try again")
        continue
    except anthropic.APIConnectionError:
        history.pop()
        print("\n[error] Can't reach the API, check your connection")
        continue
    except anthropic.APIStatusError as e:
        history.pop()
        print(f"\n[error] API returned {e.status_code}: {e.message}")
        continue

    # A rewritten answer keeps only its text: its thinking block was produced with the bad attempt
    # in context, which history does not contain, so the API rejects it on the next turn (400 "Invalid
    # signature in thinking block"). Normal answers keep their full content, thinking blocks included.
    history.append({"role": "assistant", "content": text_of(final) if retried else final.content})

    print("Claude:", text_of(final))

    note = ""
    if retried:
        note = (f" | rewritten ({broke[:100]})" if all(results[c] for c in gate)
                else f" | rewritten, still failing ({details[:100]})")
    print(f"[{final.stop_reason} | in={turn['in']} out={turn['out']} "
          f"(thinking={turn['thinking']}) | ${turn['cost']:.5f} | session ${session['cost']:.5f}{note}]")

print(f"\nSession: {session['in']} in, {session['out']} out "
      f"({session['thinking']} thinking) — ${session['cost']:.5f}")
