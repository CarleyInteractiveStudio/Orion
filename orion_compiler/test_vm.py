import sys

from lexer import Lexer
from parser import Parser
from compiler import Compiler
from vm import VM, InterpretResult

def run_vm_test(name, source_code, expected_value):
    """
    Runs the full new pipeline and checks the final result from the VM stack.
    """
    print(f"--- Running VM Test: {name} ---")

    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    # The compiler doesn't handle all statements yet, so this might be empty
    if not statements:
        # A simple expression is wrapped in an Expression statement
        print(f"FAIL: {name} - Parser produced no statements.")
        return False

    compiler = Compiler()
    chunk = compiler.compile(statements)

    if chunk is None:
        print(f"FAIL: {name} - Compiler returned no chunk.")
        return False

    vm = VM()
    result, final_value = vm.interpret(chunk)

    if result != InterpretResult.OK:
        print(f"FAIL: {name} - VM did not return OK.")
        return False

    if final_value == expected_value:
        print(f"PASS: {name}")
        return True
    else:
        print(f"FAIL: {name}")
        print(f"Expected final value: {expected_value} (type: {type(expected_value)})")
        print(f"Got:                  {final_value} (type: {type(final_value)})")
        return False

def main():
    tests_passed = 0
    total_tests = 0

    # Test 1: Simple arithmetic
    source1 = "return (5 - 2) * (3 + 1);"
    expected1 = 12.0
    total_tests += 1
    if run_vm_test("Simple Arithmetic", source1, expected1):
        tests_passed += 1

    # Test 2: More complex arithmetic with different operators
    source2 = "return -(10 / 2) + 1;"
    expected2 = -4.0
    total_tests += 1
    if run_vm_test("Complex Arithmetic", source2, expected2):
        tests_passed += 1

    print(f"\n--- VM Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
