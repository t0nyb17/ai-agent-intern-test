import json
from pathlib import Path

from agent import SupportAgent


ROOT = Path(__file__).resolve().parent
VISIBLE = ROOT / "evaluation" / "visible-cases.json"
CUSTOM = ROOT / "evaluation" / "custom-cases.json"


def run_case(case):
    agent = SupportAgent()
    answers = []
    result = None

    messages = case.get("messages")

    if messages:
        messages = [
            message["content"]
            for message in messages
        ]
    else:
        messages = [case["message"]]

    for message in messages:
        result = agent.ask(message)
        answers.append(result.answer)

    text = "\n".join(answers).lower()
    failures = []

    checks = case.get("expect", case)

    for value in checks.get("must_include", []):
        if value.lower() not in text:
            failures.append(f"missing: {value}")

    for value in checks.get("must_not_include", []):
        if value.lower() in text:
            failures.append(f"forbidden: {value}")

    if "handoff" in checks:
        if result.handoff != checks["handoff"]:
            failures.append("wrong handoff")

    tool = checks.get("tool")

    if tool == "order_lookup":
        if not result.tool_calls:
            failures.append("order lookup was not called")
        elif result.tool_calls[0].name != "order_lookup":
            failures.append("wrong tool")

    if tool == "not_called" and result.tool_calls:
        failures.append("tool was called")

    return len(failures) == 0, failures


def run_file(path):
    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    results = []

    for case in data["cases"]:
        passed, failures = run_case(case)

        results.append(
            (
                case["id"],
                case["category"],
                passed,
                failures,
            )
        )

    return results


def main():

    results = []

    if VISIBLE.exists():
        results += run_file(VISIBLE)

    if CUSTOM.exists():
        results += run_file(CUSTOM)

    print("\nCASE RESULTS")
    print("=" * 60)

    for case_id, category, passed, failures in results:

        status = "PASS" if passed else "FAIL"

        print(
            f"{status:5} {category:20} {case_id}"
        )

        for failure in failures:
            print(f"      - {failure}")

    print("\nCATEGORY RESULTS")
    print("=" * 60)

    categories = {}

    for _, category, passed, _ in results:
        if category not in categories:
            categories[category] = [0, 0]

        categories[category][1] += 1

        if passed:
            categories[category][0] += 1

    for category, values in categories.items():
        print(
            f"{category:20} {values[0]}/{values[1]}"
        )

    passed = sum(
        1 for _, _, ok, _ in results if ok
    )

    print("\nOVERALL")
    print("=" * 60)
    print(f"{passed}/{len(results)} cases passed")


if __name__ == "__main__":
    main()