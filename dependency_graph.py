
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
print("-" * 40)

for function, dependencies in dependency_map.items():

    print(f"{function} -> {dependencies}")


# --------------------------------------------------
# 5. Recursive dependency tracing
# --------------------------------------------------

visited = set()


def trace_dependencies(function):

    # Stop if function was already visited
    if function in visited:
        return

    # Remember visited function
    visited.add(function)

    dependencies = dependency_map.get(function, [])

    for dependency in dependencies:

        print(dependency)

        trace_dependencies(dependency)


# --------------------------------------------------
# 6. Start tracing
# --------------------------------------------------

print("\nTRANSITIVE DEPENDENCIES")
print("-" * 40)

trace_dependencies("calculate_total")


# --------------------------------------------------
# 7. Count only internal dependencies
# --------------------------------------------------

internal_dependencies = visited.intersection(
    dependency_map.keys()
)

internal_dependencies.discard("calculate_total")

print("\nTOTAL INTERNAL DEPENDENCIES:", len(internal_dependencies))


# --------------------------------------------------
# 8. Display internal dependencies
# --------------------------------------------------

print("\nINTERNAL DEPENDENCY LIST")
print("-" * 40)

for dependency in sorted(internal_dependencies):

    print("-", dependency)
