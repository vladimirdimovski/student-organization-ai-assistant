import re
import sys
from dotenv import load_dotenv
import anthropic
from pricing import request_cost

# Windows consoles default to cp1252, which cannot print Cyrillic or the ✓/✗ marks
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
client = anthropic.Anthropic(max_retries=3, timeout=60.0)
MODEL = "claude-haiku-5-5"
RUNS = 3

BASE = ("You are a helpful assistant for AIESEC in North Macedonia. "
        "Reply in the language the user writes in.")

RULES = """

Answer in 2-4 sentences of plain text, without headings, lists or bold.
Only name these AIESEC exchange programmes: Global Volunteer, Global Talent, Global Teacher.
Do not state dates, fees, durations or other figures you have not been given. Refer the visitor
to the AIESEC in North Macedonia team for those.

Macedonian style (use only when answering in Macedonian):
- "претприемништво" (not "предприемништво"), "траење/времетраење" (not "трајање"),
  "најажурирани информации", "директно". Never use English words in Macedonian answers,
  except AIESEC and the programme names.
- Refer to "AIESEC во Северна Македонија"; in English, "AIESEC in North Macedonia"."""

EXAMPLES = """

Here are examples of good answers:

<examples>
<example>
<question>Што е Global Volunteer?</question>
<answer>Global Volunteer е програма на AIESEC за волонтирање на општествени проекти во странство. Проектите се поврзани со Целите за одржлив развој на ОН, на пример образование или заштита на животната средина. За актуелните проекти, траењето и роковите, обратете се до тимот на AIESEC во Северна Македонија.</answer>
</example>
<example>
<question>Can I get paid for an internship through AIESEC?</question>
<answer>Global Talent is AIESEC's programme for professional internships abroad. Whether an internship is paid depends on the specific opportunity and host company, so I can't promise that. The AIESEC in North Macedonia team can tell you which current opportunities include a salary.</answer>
</example>
<example>
<question>Дали AIESEC има програма за претприемачи?</question>
<answer>Тековните програми за размена на AIESEC се Global Volunteer, Global Talent и Global Teacher. Немам потврдени информации за посебна програма за претприемачи. Ако ве интересираат стартапи, прашајте го тимот на AIESEC во Северна Македонија дали има соодветни можности преку Global Talent.</answer>
</example>
</examples>"""

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

CYR = r"[\u0400-\u04FF]"
LAT = r"[A-Za-z]"
ALLOWED = {"Volunteer", "Talent", "Teacher"}
OK_LATIN = {"AIESEC", "Global", "Volunteer", "Talent", "Teacher"}  # Latin words allowed in Macedonian
CHECKS = ["no_mixed", "programmes", "language", "plain", "short", "no_figures", "no_latin"]


def check(question: str, answer: str):
    """Deterministic checks. True = passed. Returns (results, details)."""
    words = re.findall(r"\w+", answer)
    mixed = [w for w in words if re.search(CYR, w) and re.search(LAT, w)]
    invented = set(re.findall(r"Global\s+([A-Z][a-z]+)", answer)) - ALLOWED
    want_mk = bool(re.search(CYR, question))
    is_mk = len(re.findall(CYR, answer)) > len(re.findall(LAT, answer))
    latin_words = sorted({w for w in re.findall(r"[A-Za-z]+", answer) if w not in OK_LATIN})
    results = {
        "no_mixed": not mixed,                              # e.g. "студentski"
        "programmes": not invented,                         # e.g. "Global Internship"
        "language": want_mk == is_mk,
        "plain": not re.search(r"\*\*|^#|^\s*[-*•] |^\s*\d+\.", answer, re.M),
        "short": len(words) <= 90,
        "no_figures": not re.search(r"\d", answer),         # rough: any digit = a claimed figure
        "no_latin": not (want_mk and latin_words),          # English words in a Macedonian answer
    }
    details = []
    if mixed:
        details.append(f"mixed script: {mixed}")
    if invented:
        details.append(f"invented: {['Global ' + p for p in invented]}")
    if want_mk and latin_words:
        details.append(f"latin words: {latin_words}")
    return results, "; ".join(details)


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