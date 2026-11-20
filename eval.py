"""eval.py - scores the task extractor on the test meetings in eval_data.json.

Run with:  python eval.py

How scoring works
- A predicted task "matches" an expected task if its text contains all the
  expected keywords (case-insensitive).
- Owner is correct if both are empty, or the expected owner appears in the
  predicted owner. Due is checked the same way.
- A task is "fully correct" if it was found and owner and due are both correct.
- Predicted tasks that match nothing are "extra" tasks (the AI invented them).
"""
import json
import time


def _same(expected, predicted):
    """True if both are empty, or the expected text appears in the predicted text."""
    if not expected:
        return not predicted
    return bool(predicted) and expected.lower() in predicted.lower()


def score_case(expected_tasks, predicted_tasks):
    """Compare one meeting. Returns a dict of counts plus per-task details."""
    unmatched = list(predicted_tasks)
    found = owner_ok = due_ok = fully_ok = 0
    details = []

    for exp in expected_tasks:
        match = None
        for pred in unmatched:
            text = pred["task"].lower()
            if all(k.lower() in text for k in exp["keywords"]):
                match = pred
                break
        if match is None:
            details.append(f"  MISSING: {exp['keywords']} (owner={exp['owner']}, due={exp['due']})")
            continue

        unmatched.remove(match)
        found += 1
        o = _same(exp["owner"], match.get("owner"))
        d = _same(exp["due"], match.get("due"))
        owner_ok += o
        due_ok += d
        fully_ok += o and d
        if not (o and d):
            details.append(
                f"  WRONG: {match['task']!r} -> owner={match.get('owner')} "
                f"(expected {exp['owner']}), due={match.get('due')} (expected {exp['due']})"
            )

    for extra in unmatched:
        details.append(f"  EXTRA: {extra['task']!r} was not expected")

    return {
        "expected": len(expected_tasks),
        "found": found,
        "owner_ok": owner_ok,
        "due_ok": due_ok,
        "fully_ok": fully_ok,
        "extra": len(unmatched),
        "predicted": len(predicted_tasks),
        "details": details,
    }


def pct(a, b):
    return "n/a" if b == 0 else f"{100 * a / b:.0f}%"


def run():
    import llm  # imported here so score_case can be tested without an API key

    with open("eval_data.json", encoding="utf-8") as f:
        cases = json.load(f)

    totals = {"expected": 0, "found": 0, "owner_ok": 0, "due_ok": 0,
              "fully_ok": 0, "extra": 0, "predicted": 0}

    for case in cases:
        try:
            result = llm.extract_tasks(case["notes"])
            predicted = [t.model_dump() for t in result.tasks]
        except Exception as e:  # keep going if one case fails
            print(f"Case {case['id']}: ERROR {e}")
            predicted = []

        s = score_case(case["expected"], predicted)
        for k in totals:
            totals[k] += s[k]

        ok = s["fully_ok"] == s["expected"] and s["extra"] == 0
        print(f"Case {case['id']:>2}: {'OK' if ok else 'CHECK'}")
        for line in s["details"]:
            print(line)
        time.sleep(1)  # be gentle with the free API

    print("\n===== RESULTS =====")
    print(f"Test meetings:        {len(cases)}")
    print(f"Expected tasks:       {totals['expected']}")
    print(f"Tasks found (recall): {totals['found']}/{totals['expected']} = {pct(totals['found'], totals['expected'])}")
    print(f"Owner correct:        {totals['owner_ok']}/{totals['found']} = {pct(totals['owner_ok'], totals['found'])}")
    print(f"Due date correct:     {totals['due_ok']}/{totals['found']} = {pct(totals['due_ok'], totals['found'])}")
    print(f"Fully correct tasks:  {totals['fully_ok']}/{totals['expected']} = {pct(totals['fully_ok'], totals['expected'])}")
    print(f"Extra (invented):     {totals['extra']} of {totals['predicted']} predicted tasks")


if __name__ == "__main__":
    run()
