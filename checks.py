"""Deterministic checks on answers (from fewshot.py), reused by the evals."""
import re

CYR = r"[\u0400-\u04FF]"
LAT = r"[A-Za-z]"
LATW = r"[A-Za-z\u00C0-\u024F]+"   # a whole Latin-script word, accents included (slično, not "sli" + "no")
ALLOWED = {"Volunteer", "Talent", "Teacher"}
OK_LATIN = {"AIESEC", "Global", "Volunteer", "Talent", "Teacher", "YouthSpeak"}  # Latin words allowed in Macedonian
CHECKS = ["no_mixed", "programmes", "language", "plain", "short", "no_figures", "no_latin"]
# Names that are legitimately written in Latin letters (added in Week 2). They are removed
# before the name-based and language checks, because otherwise (a) "Youth for Global Goals"
# looks like an invented "Global X" programme and its words count as English words, and (b) a
# short Macedonian answer that names programmes has more Latin than Cyrillic letters and fails
# the language check. Longest name first.
NAMES = ["Association Internationale des Étudiants en Sciences Économiques et Commerciales", "Youth for Global Goals", "Global Volunteer", "Global Talent", "Global Teacher",
         "YouthSpeak", "AIESECers", "AIESEC"]


def check(question: str, answer: str):
    """Deterministic checks. True = passed. Returns (results, details)."""
    words = re.findall(r"\w+", answer)
    mixed = [w for w in words if re.search(CYR, w) and re.search(LAT, w)]
    scan = answer
    for name in NAMES:
        scan = scan.replace(name, "")
    # Email addresses and web addresses are Latin by nature, not English words
    scan = re.sub(r"\b[\w.-]+@[\w-]+(?:\.[\w-]+)+|\b(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?",
                  "", scan, flags=re.I)
    invented = set(re.findall(r"Global\s+([A-Z][a-z]+)", scan)) - ALLOWED
    want_mk = bool(re.search(CYR, question))
    is_mk = len(re.findall(CYR, scan)) > len(re.findall(LAT, scan))
    # Latin words the visitor typed themselves may be repeated in the answer
    typed = {w.lower() for w in re.findall(LATW, question)}
    latin_words = sorted({w for w in re.findall(LATW, scan)
                          if w not in OK_LATIN and w.lower() not in typed})
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
