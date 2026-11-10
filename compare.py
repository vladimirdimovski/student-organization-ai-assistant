import sys
import time
from dotenv import load_dotenv
import anthropic
from pricing import request_cost

# Windows consoles default to cp1252, which cannot print Cyrillic or the ✓ mark
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
client = anthropic.Anthropic(max_retries=3, timeout=120.0)

MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]

SYSTEM = ("You are a helpful assistant for AIESEC in North Macedonia. "
          "Reply in the language the user writes in.")

QUESTIONS = [
    # 1. Simple factual, Macedonian
    "Што е AIESEC?",
    # 2. Reasoning + following a length constraint
    "A student has 3 free months next summer and wants international experience "
    "in marketing. Which AIESEC programme fits best and why? Answer in 3 sentences.",
    # 3. Macedonian language quality
    "Преведи на македонски: 'Applications for Global Volunteer close on 15 December. "
    "Contact your local committee for details.'",
]

rows = []

with open("compare_results.md", "w", encoding="utf-8") as out:
    for q_num, question in enumerate(QUESTIONS, start=1):
        out.write(f"## Q{q_num}: {question}\n\n")
        for model in MODELS:
            start = time.perf_counter()
            first_text = None

            with client.messages.stream(
                model=model,
                max_tokens=4000,
                system=SYSTEM,
                messages=[{"role": "user", "content": question}],
            ) as stream:
                for _ in stream.text_stream:
                    if first_text is None:                 # time to first visible word
                        first_text = time.perf_counter() - start
                final = stream.get_final_message()

            total = time.perf_counter() - start
            u = final.usage
            details = getattr(u, "output_tokens_details", None)
            thinking = getattr(details, "thinking_tokens", 0) or 0
            answer = "".join(b.text for b in final.content if b.type == "text")

            rows.append({
                "q": q_num, "model": model, "ttft": first_text, "total": total,
                "in": u.input_tokens, "out": u.output_tokens, "thinking": thinking,
                "cost": request_cost(model, u), "stop": final.stop_reason,
            })
            out.write(f"### {model}\n\n{answer}\n\n")
            print(f"Q{q_num} {model} ✓")

print(f"\n{'Q':<3}{'Model':<19}{'TTFT':>7}{'Total':>8}{'In':>6}{'Out':>7}{'Think':>7}{'Cost $':>10}  Stop")
for r in rows:
    ttft = f"{r['ttft']:.1f}s" if r["ttft"] is not None else "—"
    print(f"{r['q']:<3}{r['model']:<19}{ttft:>7}{r['total']:>7.1f}s{r['in']:>6}"
          f"{r['out']:>7}{r['thinking']:>7}{r['cost']:>10.5f}  {r['stop']}")

print()
for m in MODELS:
    m_rows = [r for r in rows if r["model"] == m]
    print(f"{m:<19} total ${sum(r['cost'] for r in m_rows):.5f}  "
          f"avg time {sum(r['total'] for r in m_rows) / len(m_rows):.1f}s")