
from pathlib import Path
import re

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    "dist",
    "build",
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css", ".json", ".md"
}


def exact_search(repo_path, symbol):
    repo = Path(repo_path)

    if not repo.exists() or not repo.is_dir():
        print("Repository path does not exist.")
        return

    # Match the complete symbol, not just a substring.
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])"
    )

    results = []

    for file_path in repo.rglob("*"):

        if not file_path.is_file():
            continue

        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue

        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).splitlines()

            for line_number, line in enumerate(lines, start=1):
                if pattern.search(line):
                    results.append({
                        "file": str(file_path.relative_to(repo)),
                        "line": line_number,
                        "code": line.strip()
                    })

        except OSError:
            continue

    return results


if __name__ == "__main__":
    repo_path = input("Enter repository path: ").strip()
    symbol = input("Enter function or variable name: ").strip()

    matches = exact_search(repo_path, symbol)

    if matches is None:
        raise SystemExit(1)

    print(f"\nTotal matches: {len(matches)}")

    for match in matches:
        print(f"\nFile: {match['file']}")
        print(f"Line: {match['line']}")
        print(f"Code: {match['code']}")
