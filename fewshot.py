import sys
from dotenv import load_dotenv
import anthropic
from pricing import request_cost
from prompts import BASE, RULES, EXAMPLES
from checks import check, CHECKS

# Windows consoles default to cp1252, which cannot print Cyrillic or the ✓/✗ marks
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
client = anthropic.Anthropic(max_retries=3, timeout=60.0)
MODEL = "claude-haiku-5-5"
RUNS = 3


VARIANTS = {
    "A baseline": BASE,
    "B rules": BASE + RULES,
    "C rules+examples": BASE + RULES + EXAMPLES,
}

# New questions: none of them appear in the examples
QUESTIONS = [
    "Кои програми ги нуди AIESEC за студенти?",
    "I study computer science and want to work abroad next summer. What should I apply for?",
    "Колку чини да се оди на волонтирање преку AIESEC?",
]



results = {name: [] for name in VARIANTS}

with open("fewshot_results.md", "w", encoding="utf-8") as out:
    for name, system in VARIANTS.items():
        out.write(f"# {name}\n\n")
        for q in QUESTIONS:
            for run in range(1, RUNS + 1):
                r = client.messages.create(
                    model=MODEL, max_tokens=2000, system=system,
                    messages=[{"role": "user", "content": q}],
                )
                answer = "".join(b.text for b in r.content if b.type == "text")
                if r.stop_reason == "max_tokens":
                    print(f"⚠️ Truncated: {name} / {q[:30]}")
                passed, details = check(q, answer)
                failed = [c for c in CHECKS if not passed[c]]
                results[name].append({
                    "passed": passed, "in": r.usage.input_tokens,
                    "out": r.usage.output_tokens, "cost": request_cost(MODEL, r.usage),
                })
                out.write(f"## {q} (run {run})\n"
                          f"Failed: {', '.join(failed) or 'none'} {details}\n\n{answer}\n\n")
                print(f"{name:<17} run {run}  {q[:35]:<35}  "
                      f"{'✓' if not failed else '✗ ' + ', '.join(failed)}")

print(f"\n{'Variant':<18}" + "".join(f"{c:>12}" for c in CHECKS)
      + f"{'avg in':>8}{'avg out':>9}{'cost $':>10}")
for name, rows in results.items():
    n = len(rows)
    line = f"{name:<18}" + "".join(
        f"{sum(r['passed'][c] for r in rows)}/{n}".rjust(12) for c in CHECKS)
    line += (f"{sum(r['in'] for r in rows) / n:>8.0f}"
             f"{sum(r['out'] for r in rows) / n:>9.0f}"
             f"{sum(r['cost'] for r in rows):>10.5f}")
    print(line)