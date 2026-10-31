
import ast
from pathlib import Path


# Directories that should be ignored
IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}


# --------------------------------------------------
# 1. Analyze a Python file using AST
# --------------------------------------------------

def analyze_python_file(file_path, symbol):

    try:
        source = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except OSError:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    results = []

    for node in ast.walk(tree):

        # Regular imports
        if isinstance(node, ast.Import):

            for alias in node.names:

                if alias.name == symbol:
                    results.append({
                        "type": "IMPORT",
                        "line": node.lineno,
                        "name": alias.name
                    })

        # From imports
        elif isinstance(node, ast.ImportFrom):

            for alias in node.names:

                if alias.name == symbol:
                    results.append({
                        "type": "IMPORT_FROM",
                        "line": node.lineno,
                        "name": alias.name
                    })

        # Function definitions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            if node.name == symbol:
                results.append({
                    "type": "DEFINITION",
                    "line": node.lineno,
                    "name": node.name
                })

        # Class definitions
        elif isinstance(node, ast.ClassDef):

            if node.name == symbol:
                results.append({
                    "type": "CLASS_DEFINITION",
                    "line": node.lineno,
                    "name": node.name
                })

        # Function and method calls
        elif isinstance(node, ast.Call):

            # Direct function call: clean_expired_entries()
            if isinstance(node.func, ast.Name):

                if node.func.id == symbol:
                    results.append({
                        "type": "FUNCTION_CALL",
                        "line": node.lineno,
                        "name": symbol
                    })

            # Method call: db.commit()
            elif isinstance(node.func, ast.Attribute):

                if node.func.attr == symbol:
                    results.append({
                        "type": "METHOD_CALL",
                        "line": node.lineno,
                        "name": symbol,
                        "object": ast.unparse(node.func.value)
                    })

    return results


# --------------------------------------------------
# 2. Extract a function from a single Python file
# --------------------------------------------------

def extract_function(file_path, symbol):

    try:
        source = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except OSError:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()

    functions = []

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            if node.name == symbol:

                function_code = "\n".join(
                    lines[node.lineno - 1:node.end_lineno]
                )

                functions.append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "code": function_code
                })

    return functions


# --------------------------------------------------
# 3. Search for a symbol across the entire repository
# --------------------------------------------------

def search_repository(repo_path, symbol):

    repo = Path(repo_path)

    if not repo.exists():
        raise FileNotFoundError(
            "Repository path does not exist."
        )

    if not repo.is_dir():
        raise NotADirectoryError(
            "Please provide a repository folder."
        )

    all_results = []

    for file_path in repo.rglob("*.py"):

        relative_path = file_path.relative_to(repo)

        # Ignore unnecessary directories
        if any(part in IGNORED_DIRS for part in relative_path.parts):
            continue

        matches = analyze_python_file(file_path, symbol)

        for match in matches:
            match["file"] = str(relative_path)
            all_results.append(match)

    # Sort by file and line number
    all_results.sort(
        key=lambda item: (
            item["file"].lower(),
            item["line"]
        )
    )

    return all_results


# --------------------------------------------------
# 4. Extract a function from anywhere in the repository
# --------------------------------------------------

def extract_function_from_repository(repo_path, symbol):

    repo = Path(repo_path)

    if not repo.exists():
        raise FileNotFoundError(
            "Repository path does not exist."
        )

    if not repo.is_dir():
        raise NotADirectoryError(
            "Please provide a repository folder."
        )

    all_functions = []

    for file_path in repo.rglob("*.py"):

        relative_path = file_path.relative_to(repo)

        # Ignore unnecessary directories
        if any(part in IGNORED_DIRS for part in relative_path.parts):
            continue

        functions = extract_function(file_path, symbol)

        for function in functions:
            function["file"] = str(relative_path)
            all_functions.append(function)

    # Sort by file and starting line
    all_functions.sort(
        key=lambda item: (
            item["file"].lower(),
            item["start_line"]
        )
    )

    return all_functions


# --------------------------------------------------
# 5. Main program
# --------------------------------------------------

if __name__ == "__main__":

    repo_path = input(
        "Enter repository folder path: "
    ).strip()

    symbol = input(
        "Enter function, class or module name: "
    ).strip()

    if not repo_path or not symbol:
        print("Repository path and symbol name are required.")

    else:

        try:

            # AST symbol search
            results = search_repository(
                repo_path,
                symbol
            )

            print("\nTotal matches:", len(results))
            print("-" * 70)

            for result in results:

                print(
                    f"File: {result['file']} | "
                    f"Type: {result['type']} | "
                    f"Line: {result['line']} | "
                    f"Name: {result['name']}"
                    + (
                        f" | Object: {result['object']}"
                        if "object" in result else ""
                    )
                )

            # Repository-wide function extraction
            functions = extract_function_from_repository(
                repo_path,
                symbol
            )

            print("\n" + "=" * 70)
            print("FUNCTION EXTRACTION")
            print("=" * 70)

            print(
                "\nFunction definitions found:",
                len(functions)
            )

            if functions:

                for function in functions:

                    print("\n" + "=" * 70)
                    print("File:", function["file"])
                    print("Function:", function["name"])

                    print(
                        "Lines:",
                        function["start_line"],
                        "-",
                        function["end_line"]
                    )

                    print("\nComplete function code:")
                    print("-" * 70)
                    print(function["code"])

            else:
                print(
                    "No matching function definition found."
                )

        except (FileNotFoundError, NotADirectoryError) as error:

            print("\nError:", error)

        except OSError as error:

            print("\nFile system error:", error)
