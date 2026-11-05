
import ast

# --------------------------------------------------
# 1. Sample Python code
# --------------------------------------------------

code = """
def calculate_total():
    validate_price()
    calculate_tax()

def validate_price():
    check_discount()

def calculate_tax():
    get_tax_rate()

def check_discount():
    print("Checking discount")

def get_tax_rate():
    print("Getting tax rate")
"""


# --------------------------------------------------
# 2. Parse Python code using AST
# --------------------------------------------------

tree = ast.parse(code)


# --------------------------------------------------
# 3. Build the dependency map
# --------------------------------------------------

dependency_map = {}

for node in ast.walk(tree):

    if isinstance(node, ast.FunctionDef):

        function_name = node.name
        dependencies = []

        for child in ast.walk(node):

            if isinstance(child, ast.Call):

                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)

        dependency_map[function_name] = dependencies


# --------------------------------------------------
# 4. Display dependency map
# --------------------------------------------------

print("FUNCTION DEPENDENCY MAP")
print("-" * 45)

for function, dependencies in dependency_map.items():

    print(f"{function} -> {dependencies}")


# --------------------------------------------------
# 5. Recursive dependency tracing
# --------------------------------------------------

visited = set()


def trace_dependencies(function):

    if function in visited:
        return

    visited.add(function)

    dependencies = dependency_map.get(function, [])

    for dependency in dependencies:

        print(dependency)

        trace_dependencies(dependency)


print("\nTRANSITIVE DEPENDENCIES")
print("-" * 45)

trace_dependencies("calculate_total")


# --------------------------------------------------
# 6. Count internal dependencies
# --------------------------------------------------

internal_dependencies = visited.intersection(
    dependency_map.keys()
)

internal_dependencies.discard("calculate_total")

print("\nTOTAL INTERNAL DEPENDENCIES:", len(internal_dependencies))


# --------------------------------------------------
# 7. Display internal dependency list
# --------------------------------------------------

print("\nINTERNAL DEPENDENCY LIST")
print("-" * 45)

for dependency in sorted(internal_dependencies):

    print("-", dependency)


# --------------------------------------------------
# 8. Generate clean dependency tree
# --------------------------------------------------

def print_dependency_tree(function, visited=None, level=0):

    if visited is None:
        visited = set()

    if function in visited:
        return

    visited.add(function)

    print("  " * level + function)

    dependencies = dependency_map.get(function, [])

    for dependency in dependencies:

        # Include only functions defined in our code
        if dependency in dependency_map:

            print_dependency_tree(
                dependency,
                visited,
                level + 1
            )


print("\nCLEAN DEPENDENCY TREE")
print("-" * 45)

print_dependency_tree("calculate_total")
