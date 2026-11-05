
import ast
from pathlib import Path
from collections import defaultdict


# ============================================================
# CONFIGURATION
# ============================================================

REPO_PATH = Path(
    r"C:\Users\amayn\OneDrive\Desktop\intillichargee\backend"
)

TARGET_MODULE = "app.api.queue"
TARGET_FUNCTION = "join_queue"

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_module_name(file_path):
    """
    Convert a Python file path into its module name.

    Example:
    app/services/queue_engine.py
    becomes:
    app.services.queue_engine
    """

    relative_path = file_path.relative_to(REPO_PATH)

    parts = list(relative_path.with_suffix("").parts)

    if parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts)


def get_attribute_chain(node):
    """
    Convert AST attribute expressions into a list.

    Example:
    qe.recalculate_queue

    becomes:
    ['qe', 'recalculate_queue']
    """

    parts = []

    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value

    if isinstance(node, ast.Name):
        parts.append(node.id)

    return list(reversed(parts))


def resolve_relative_import(module_name, level, imported_module):
    """
    Resolve Python relative imports.

    Example:
    from .queue_engine import recalculate_queue
    """

    current_parts = module_name.split(".")

    if current_parts:
        current_parts.pop()

    for _ in range(max(level - 1, 0)):
        if current_parts:
            current_parts.pop()

    if imported_module:
        current_parts.extend(imported_module.split("."))

    return ".".join(current_parts)


# ============================================================
# FUNCTION CALL EXTRACTION
# ============================================================

def get_function_calls(function_node):
    """
    Extract calls belonging directly to this function.

    Does NOT enter:
    - nested functions
    - nested async functions
    - nested classes
    - lambdas
    """

    calls = []

    def visit(node):

        for child in ast.iter_child_nodes(node):

            # Do not enter nested scopes
            if isinstance(
                child,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                continue

            if isinstance(child, ast.Call):
                calls.append(child)

            visit(child)

    visit(function_node)

    return calls


# ============================================================
# BUILD FUNCTION INDEX
# ============================================================

def build_function_index():

    function_index = {}
    module_functions = defaultdict(list)

    import_map = defaultdict(dict)
    module_import_map = defaultdict(dict)

    python_files = []

    print("Scanning IntelliCharge backend...")

    for file_path in REPO_PATH.rglob("*.py"):

        if any(
            ignored in file_path.parts
            for ignored in IGNORED_DIRS
        ):
            continue

        python_files.append(file_path)

    # --------------------------------------------------------
    # First pass: parse files and register imports/functions
    # --------------------------------------------------------

    parsed_files = {}

    for file_path in python_files:

        try:
            source = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            tree = ast.parse(source)

        except (SyntaxError, OSError):
            continue

        module_name = get_module_name(file_path)

        parsed_files[module_name] = {
            "tree": tree,
            "file": file_path,
        }

        # ----------------------------------------------------
        # Imports
        # ----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:

                    imported_module = alias.name

                    if alias.asname:
                        local_name = alias.asname
                        module_import_map[module_name][local_name] = (
                            imported_module
                        )

                    else:
                        local_name = imported_module.split(".")[0]

                        module_import_map[module_name][local_name] = (
                            local_name
                        )

            elif isinstance(node, ast.ImportFrom):

                imported_module = resolve_relative_import(
                    module_name,
                    node.level,
                    node.module,
                )

                for alias in node.names:

                    if alias.name == "*":
                        continue

                    local_name = alias.asname or alias.name

                    # Imported module
                    module_import_map[module_name][local_name] = (
                        f"{imported_module}.{alias.name}"
                    )

                    # Imported symbol
                    import_map[module_name][local_name] = (
                        f"{imported_module}.{alias.name}"
                    )

        # ----------------------------------------------------
        # Functions and methods
        # ----------------------------------------------------

        def register_functions(node, parent_name=""):

            for child in node.body:

                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):

                    function_name = child.name

                    if parent_name:
                        qualified_name = (
                            f"{module_name}.{parent_name}.{function_name}"
                        )
                    else:
                        qualified_name = (
                            f"{module_name}.{function_name}"
                        )

                    function_index[qualified_name] = {
                        "name": function_name,
                        "qualified_name": qualified_name,
                        "module": module_name,
                        "class_name": parent_name or None,
                        "node": child,
                        "file": file_path,
                        "line": child.lineno,
                    }

                    module_functions[module_name].append(
                        qualified_name
                    )

                elif isinstance(child, ast.ClassDef):

                    class_name = (
                        f"{parent_name}.{child.name}"
                        if parent_name
                        else child.name
                    )

                    register_functions(
                        child,
                        class_name,
                    )

        register_functions(tree)

    print(f"Indexed functions: {len(function_index)}")

    return (
        function_index,
        module_functions,
        import_map,
        module_import_map,
    )


# ============================================================
# RESOLVE FUNCTION CALLS
# ============================================================

def resolve_call(
    call_node,
    current_function,
    function_index,
    import_map,
    module_import_map,
):

    module_name = current_function["module"]
    class_name = current_function["class_name"]

    # --------------------------------------------------------
    # Example: function_name()
    # --------------------------------------------------------

    if isinstance(call_node.func, ast.Name):

        called_name = call_node.func.id

        # Imported function
        imported_name = import_map[module_name].get(
            called_name
        )

        if imported_name in function_index:
            return imported_name

        # Same-module function
        same_module_name = (
            f"{module_name}.{called_name}"
        )

        if same_module_name in function_index:
            return same_module_name

        # Same-class method
        if class_name:

            class_method_name = (
                f"{module_name}.{class_name}.{called_name}"
            )

            if class_method_name in function_index:
                return class_method_name

        # Unique global function name fallback
        matches = [
            qualified_name
            for qualified_name, info in function_index.items()
            if info["name"] == called_name
        ]

        if len(matches) == 1:
            return matches[0]

        return None

    # --------------------------------------------------------
    # Example: self.method(), cls.method()
    # --------------------------------------------------------

    if isinstance(call_node.func, ast.Attribute):

        chain = get_attribute_chain(call_node.func)

        if not chain:
            return None

        # self.method() or cls.method()
        if (
            chain[0] in {"self", "cls"}
            and class_name
        ):

            method_name = chain[-1]

            candidate = (
                f"{module_name}.{class_name}.{method_name}"
            )

            if candidate in function_index:
                return candidate

        # ----------------------------------------------------
        # Imported module alias
        # Example: qe.recalculate_queue()
        # ----------------------------------------------------

        if len(chain) >= 2:

            local_module_name = chain[0]

            imported_module = (
                module_import_map[module_name].get(
                    local_module_name
                )
            )

            if imported_module:

                candidate = (
                    f"{imported_module}.{chain[-1]}"
                )

                if candidate in function_index:
                    return candidate

        # ----------------------------------------------------
        # Imported function alias
        # ----------------------------------------------------

        if len(chain) >= 2:

            imported_function = (
                import_map[module_name].get(chain[0])
            )

            if imported_function:

                candidate = (
                    f"{imported_function}.{chain[-1]}"
                )

                if candidate in function_index:
                    return candidate

        # ----------------------------------------------------
        # Same-module method/function attribute
        # ----------------------------------------------------

        candidate = (
            f"{module_name}.{chain[-1]}"
        )

        if candidate in function_index:
            return candidate

    return None


# ============================================================
# TRACE DEPENDENCIES
# ============================================================


def trace_dependencies(
    qualified_name,
    function_index,
    import_map,
    module_import_map,
    active_path=None,
    level=0,
):

    if active_path is None:
        active_path = set()

    if qualified_name not in function_index:
        return

    function_info = function_index[qualified_name]
    indent = "    " * level

    print(
        f"{indent}{function_info['qualified_name']} "
        f"({function_info['file'].relative_to(REPO_PATH)}:"
        f"{function_info['line']})"
    )

    # Detect recursion/cycles
    if qualified_name in active_path:
        print(f"{indent}    [Cycle detected]")
        return

    active_path = active_path.copy()
    active_path.add(qualified_name)

    # --------------------------------------------------------
    # Group calls by dependency
    # --------------------------------------------------------

    dependency_calls = defaultdict(list)

    for call_node in get_function_calls(function_info["node"]):

        dependency = resolve_call(
            call_node,
            function_info,
            function_index,
            import_map,
            module_import_map,
        )

        if dependency:
            dependency_calls[dependency].append(
                call_node.lineno
            )

    # --------------------------------------------------------
    # Print grouped dependencies
    # --------------------------------------------------------

    for dependency, line_numbers in dependency_calls.items():

        dependency_info = function_index[dependency]

        # Remove duplicate line numbers, preserve order
        line_numbers = list(dict.fromkeys(line_numbers))

        if len(line_numbers) == 1:
            locations = f"line {line_numbers[0]}"
        else:
            locations = (
                "lines "
                + ", ".join(map(str, line_numbers))
            )

        print(
            f"{indent}  └── calls "
            f"{dependency_info['name']} "
            f"({locations})"
        )

        trace_dependencies(
            dependency,
            function_index,
            import_map,
            module_import_map,
            active_path,
            level + 1,
        )



# ============================================================
# BUILD DEPENDENCY GRAPH
# ============================================================

def build_dependency_graph(
    qualified_name,
    function_index,
    import_map,
    module_import_map,
    graph=None,
    visited=None,
):
    """
    Build a dependency graph using an adjacency list.

    Each function is a node.
    Each function call is a directed edge.
    """

    if graph is None:
        graph = {}

    if visited is None:
        visited = set()

    # Stop if function doesn't exist
    if qualified_name not in function_index:
        return graph

    # Avoid processing the same function repeatedly
    if qualified_name in visited:
        return graph

    visited.add(qualified_name)

    # Create an empty list for this function
    graph.setdefault(qualified_name, [])

    function_info = function_index[qualified_name]

    # Find calls inside this function
    calls = get_function_calls(function_info["node"])

    for call_node in calls:

        dependency = resolve_call(
            call_node,
            function_info,
            function_index,
            import_map,
            module_import_map,
        )

        if not dependency:
            continue

        # Store the dependency as an outgoing edge
        if dependency not in graph[qualified_name]:
            graph[qualified_name].append(dependency)

        # Ensure the dependency also exists as a node
        graph.setdefault(dependency, [])

        # Recursively explore the dependency
        build_dependency_graph(
            dependency,
            function_index,
            import_map,
            module_import_map,
            graph,
            visited,
        )

    return graph



# ============================================================
# MAIN
# ============================================================


def main():

    (
        function_index,
        module_functions,
        import_map,
        module_import_map,
    ) = build_function_index()

    print("\nFunctions in target module:")
    print("=" * 60)

    for qualified_name in module_functions.get(
        TARGET_MODULE,
        [],
    ):
        print(qualified_name)

    target_name = f"{TARGET_MODULE}.{TARGET_FUNCTION}"

    if target_name not in function_index:
        print("\nTarget function not found:")
        print(target_name)
        print("\nCheck TARGET_MODULE and TARGET_FUNCTION.")
        return

    # Part 1: Print the dependency tree
    print("\nCROSS-FILE DEPENDENCY TRACE")
    print("=" * 60)

    trace_dependencies(
        target_name,
        function_index,
        import_map,
        module_import_map,
    )

    # Part 2: Build the dependency graph
    print("\nDEPENDENCY GRAPH (ADJACENCY LIST)")
    print("=" * 60)

    graph = build_dependency_graph(
        target_name,
        function_index,
        import_map,
        module_import_map,
    )

    # Part 3: Print the graph
    for function, dependencies in graph.items():

        print(f"\n{function}")

        for dependency in dependencies:
            print(f"    -> {dependency}")


if __name__ == "__main__":
    main()
