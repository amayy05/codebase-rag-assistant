import ast

code = '''
def hello():
    print("Hi")

hello()
'''

tree = ast.parse(code)

print(ast.dump(tree, indent=2))