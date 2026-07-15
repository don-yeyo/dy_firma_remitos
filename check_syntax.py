import ast
import traceback

with open("scanner.py", "rb") as f:
    source = f.read()

try:
    ast.parse(source)
    print("No syntax errors found.")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}, offset {e.offset}: {e.msg}")
    print(e.text)
