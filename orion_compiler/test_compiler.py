import sys
import io
from contextlib import redirect_stderr

from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source

def run_compiler_test(name, source_code, expected_error_fragment):
    """
    Runs the static analysis part of the compiler and checks for expected type errors.
    """
    print(f"--- Running Compiler Test: {name} ---")

    # Setup to capture stderr
    f = io.StringIO()
    with redirect_stderr(f):
        lexer = Lexer(source_code)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()

        # The compile function now includes the type analysis pass
        main_function = compile_source(statements)

    output = f.getvalue()

    # We expect the compiler to fail
    if main_function is not None:
        print(f"FAIL: {name} - Compiler returned a function, but an error was expected.")
        return False

    if expected_error_fragment in output:
        print(f"PASS: {name}")
        return True
    else:
        print(f"FAIL: {name}")
        print(f"Expected error fragment: '{expected_error_fragment}'")
        print(f"Got stderr output: '{output.strip()}'")
        return False

def run_compiler_valid_test(name, source_code):
    """
    Runs the static analysis on valid code and expects no errors.
    """
    print(f"--- Running Compiler Test (Valid): {name} ---")

    f = io.StringIO()
    with redirect_stderr(f):
        lexer = Lexer(source_code)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        main_function = compile_source(statements)

    output = f.getvalue()

    if main_function is not None and not output:
        print(f"PASS: {name}")
        return True
    else:
        print(f"FAIL: {name}")
        print(f"Expected no errors, but got stderr: '{output.strip()}'")
        if main_function is None:
            print("And compiler returned None.")
        return False

def main():
    error_tests = [
        ("Assign wrong type", "var x: number = 'a';", "Initializer of type STRING cannot be assigned to variable of type NUMBER"),
        ("Re-assign wrong type", "var x: bool; x = 1;", "Cannot assign value of type NUMBER to variable of type BOOL"),
        ("Numeric operator error", "'a' - 'b';", "Operands for MINUS must be numbers"),
        ("Addition operator error", "1 + 'b';", "Operands for '+' must be two numbers or two strings"),
        ("Comparison operator error", "true > false;", "Operands for GREATER must be numbers"),
        ("Unary minus error", "-'hello';", "Operand for '-' must be a number"),
        ("Unary not error", "!123;", "Operand for '!' must be a boolean"),
        ("If condition error", "if (1) {}", "If condition must be a boolean"),
        ("While condition error", "while ('a') {}", "While condition must be a boolean"),
        ("Subscript non-list", "var x: number = 1; return x[0];", "Can only use subscript on lists"),
        ("Subscript with non-number", "var l = [1]; return l['a'];", "List index must be a number"),
    ]

    valid_tests = [
        ("Correct assignment", "var x: number = 1; x = 2;"),
        ("String concatenation", "var s: string = 'a' + 'b';"),
        ("Boolean logic", "var b: bool = true == false;"),
        ("Valid if", "if (true) {}"),
        ("Valid while", "var b: bool = false; while(b) {}"),
        ("List creation", "var l = [1, 'a', true];"),
        ("Valid get subscript", "var l = [1]; var x = l[0];"),
        ("Valid set subscript", "var l = [1]; l[0] = 2;"),
    ]

    tests_passed = 0
    total_tests = len(error_tests) + len(valid_tests)

    for name, source, expected in error_tests:
        if run_compiler_test(name, source, expected):
            tests_passed += 1

    for name, source in valid_tests:
        if run_compiler_valid_test(name, source):
            tests_passed += 1

    print(f"\n--- Compiler Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
