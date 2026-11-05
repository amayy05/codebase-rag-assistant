
import ast
from pathlib import Path

REPO_PATH = Path(
    r"C:\Users\amayn\OneDrive\Desktop\intillichargee\backend"
)

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__",
    ".pytest_cache", "node_modules", "build", "dist"
}


def scan_python_files(repo_path):

    files = []

    for path in repo_path.rglob("*.py"):

        relative = path.relative_to(repo_path)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        files.append(path)

    return files


def build_function_index(repo_path):

    index = {}

    for file_path in scan_python_files(repo_path):

        try:
            tree = ast.parse(
                file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            )
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                index.setdefault(node.name, []).append({
                    "file": str(file_path.relative_to(repo_path)),
                    "line": node.lineno
                })

    return index


def classify_calls(file_path, target_function, function_index):

    source = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    tree = ast.parse(source)

    for node in ast.walk(tree):

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if node.name != target_function:
            continue

        results = []

        for child in ast.walk(node):

            if not isinstance(child, ast.Call):
                continue

            # Direct function call, e.g. to_utc(...)
            if isinstance(child.func, ast.Name):

                name = child.func.id

                if name in function_index:
                    category = "INTERNAL_FUNCTION"
                else:
                    category = "EXTERNAL_OR_UNRESOLVED"

                results.append({
                    "name": name,
                    "category": category,
                    "line": child.lineno
                })

            # Method call, e.g. db.commit()
            elif isinstance(child.func, ast.Attribute):

                results.append({
                    "name": ast.unparse(child.func),
                    "category": "METHOD_OR_UNRESOLVED",
                    "line": child.lineno
                })

        return results

    return []


if __name__ == "__main__":

    index = build_function_index(REPO_PATH)

    target_file = (
        REPO_PATH / "app" / "services" / "queue_engine.py"
    )

    calls = classify_calls(
        target_file,
        "clean_expired_entries",
        index
    )

    print("CALL CLASSIFICATION")
    print("-" * 50)

    for call in calls:

        print(
            f"Line {call['line']} | "
            f"{call['name']} | "
            f"{call['category']}"
        )
