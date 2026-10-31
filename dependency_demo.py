import ast

code = """
def calculate_total():
    validate_price()
    calculate_tax()
    save_result()

def validate_price():
    print("Validating")

def calculate_tax():
    print("Calculating tax")

def save_result():
    print("Saving")
"""

tree = ast.parse(code)

target_function = "calculate_total"

for node in ast.walk(tree):

    if isinstance(node, ast.FunctionDef):

        if node.name == target_function:

            print("Function:", node.name)
            print("\nDirect dependencies:")

            dependencies = []

            for child in ast.walk(node):

                if isinstance(child, ast.Call):

                    if isinstance(child.func, ast.Name):
                        dependencies.append(child.func.id)

            for dependency in dependencies:
                print("-", dependency)

            print("\nTotal:", len(dependencies))