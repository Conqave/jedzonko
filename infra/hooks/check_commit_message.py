import re
import sys
from pathlib import Path

MAX_SUBJECT_LENGTH = 50
MAX_BODY_LINE_LENGTH = 72
SUBJECT = re.compile(r"^(?P<first_word>[A-Z][a-z]*)(?: [^\n]*)?[^.\s]$")
PREFIX = re.compile(r"^[a-z]+(\([^)]*\))?!?: ")
NON_IMPERATIVE = re.compile(r"(ed|ing|[^s]s)$")
FORBIDDEN_TRAILER = re.compile(r"^(co-authored-by: .*(claude|anthropic)|claude-session:)", re.I)


def find_problems(message: str) -> list[str]:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    subject = lines[0] if lines else ""
    problems = []
    matched = SUBJECT.match(subject)
    if PREFIX.match(subject) is not None:
        problems.append("the subject carries no type prefix")
    elif matched is None:
        problems.append("the subject starts with a capital letter and ends without a period")
    elif NON_IMPERATIVE.search(matched.group("first_word").lower()) is not None:
        problems.append(f"the subject starts with an imperative verb, not {matched.group('first_word')!r}")
    if re.search(r"[.!?;] ", subject):
        problems.append("the subject is a single sentence")
    if len(subject) > MAX_SUBJECT_LENGTH:
        problems.append(f"the subject fits in {MAX_SUBJECT_LENGTH} characters")
    if len(lines) > 1 and lines[1] != "":
        problems.append("a blank line separates the subject from the body")
    if any(len(line) > MAX_BODY_LINE_LENGTH for line in lines[2:]):
        problems.append(f"body lines wrap at {MAX_BODY_LINE_LENGTH} characters")
    if any(FORBIDDEN_TRAILER.match(line) for line in lines):
        problems.append("the message carries no assistant attribution")
    return problems


def main() -> int:
    message_path = Path(sys.argv[1])
    message = message_path.read_text()
    problems = find_problems(message)
    for problem in problems:
        print(f"commit message: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
