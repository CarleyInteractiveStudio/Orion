import sys
import io
from contextlib import redirect_stdout

from lexer import Lexer
from parser import Parser
from resolver import Resolver

def run_resolver_test(name, source_code, expected_error=None):
    """
    Runs the lexer, parser, and resolver, then checks for specific errors.
    """
    print(f"--- Running Resolver Test: {name} ---")

    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    # Capture stdout to check for resolver errors
    f = io.StringIO()
    with redirect_stdout(f):
        resolver = Resolver()
        resolver.resolve(statements)

    output = f.getvalue()

    if expected_error:
        if resolver.had_error and expected_error in output:
            print(f"PASS: {name} (Correctly caught error)")
            return True
        else:
            print(f"FAIL: {name}")
            print(f"Expected error containing: '{expected_error}'")
            print(f"Got output: '{output.strip()}'")
            return False
    else: # Should be valid code
        if not resolver.had_error:
            print(f"PASS: {name} (Correctly identified valid code)")
            return True
        else:
            print(f"FAIL: {name}")
            print("Expected no errors, but got:")
            print(output.strip())
            return False

def main():
    tests_passed = 0
    total_tests = 0

    # --- Tests that should FAIL ---

    # Test 1: Redeclaring a variable
    source1 = "var a = 1; var a = 2;"
    total_tests += 1
    if run_resolver_test("Redeclared Variable", source1, "Already a variable with this name"):
        tests_passed += 1

    # Test 2: Using variable in its own initializer
    source2 = "var a = a;"
    total_tests += 1
    if run_resolver_test("Variable in Initializer", source2, "Can't read local variable in its own initializer"):
        tests_passed += 1

    # Test 3: Assigning to a const variable
    source3 = "const a = 1; a = 2;"
    total_tests += 1
    if run_resolver_test("Assign to Const", source3, "Cannot assign to a constant variable"):
        tests_passed += 1

    # Test 4: Type mismatch
    source4 = 'var a: int = "hello";'
    total_tests += 1
    if run_resolver_test("Type Mismatch", source4, "Type mismatch: cannot assign value of type 'string' to variable of type 'int'"):
        tests_passed += 1

    # --- Tests that should PASS ---

    # Test 5: Valid code
    source5 = "var a = 1; var b = 2; a = a + b;"
    total_tests += 1
    if run_resolver_test("Valid Code", source5, expected_error=None):
        tests_passed += 1

    # --- New Function Type-Checking Tests ---

    # Test 6: Wrong argument type
    source6 = 'function foo(a: int) {} foo("bar");'
    total_tests += 1
    if run_resolver_test("Wrong Argument Type", source6, "expected 'int', got 'string'"):
        tests_passed += 1

    # Test 7: Wrong argument count
    source7 = "function foo(a: int, b: int) {} foo(1);"
    total_tests += 1
    if run_resolver_test("Wrong Argument Count", source7, "Expected 2 arguments but got 1"):
        tests_passed += 1

    # Test 8: Wrong return type
    source8 = 'function foo(): int { return "bar"; }'
    total_tests += 1
    if run_resolver_test("Wrong Return Type", source8, "function should return 'int' but returns 'string'"):
        tests_passed += 1

    # Test 9: Return value from void function
    source9 = "function foo() { return 1; }"
    total_tests += 1
    if run_resolver_test("Return from Void Function", source9, "Cannot return a value from a void function"):
        tests_passed += 1

    # Test 10: Valid typed function
    source10 = "function foo(a: float): float { return a; } var x = foo(1);"
    total_tests += 1
    if run_resolver_test("Valid Typed Function", source10, expected_error=None):
        tests_passed += 1

    print(f"\n--- Resolver Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
