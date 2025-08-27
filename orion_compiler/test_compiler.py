import sys
import io
from contextlib import redirect_stderr

from .lexer import Lexer
from .parser import Parser
from .compiler import compile as compile_source

def run_compiler_test(name, source_code, expected_error_fragment):
    """
    Runs the static analysis part of the compiler and checks for expected type errors.
    """
    print(f"--- Running Compiler Test: {name} ---")

    f = io.StringIO()
    with redirect_stderr(f):
        lexer = Lexer(source_code)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()

        main_function = compile_source(statements)

    output = f.getvalue()

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
        ("Assign wrong type", "var x: number = 'a';", "Initializer of type string cannot be assigned to variable of type number"),
        ("Re-assign wrong type", "var x: bool; x = 1;", "Cannot assign value of type number to variable of type bool"),
        ("Numeric operator error", "'a' - 'b';", "Operands for MINUS must be numbers"),
        ("Addition operator error", "1 + 'b';", "Operands for '+' must be two numbers or two strings"),
        ("Comparison operator error", "true > false;", "Operands for GREATER must be numbers"),
        ("Unary minus error", "-'hello';", "Operand for '-' must be a number"),
        ("Unary not error", "!123;", "Operand for '!' must be a boolean"),
        ("If condition error", "if (1) {}", "If condition must be a boolean"),
        ("While condition error", "while ('a') {}", "While condition must be a boolean"),
        ("Subscript non-subscriptable", "var x: number = 1; return x[0];", "is not subscriptable"),
        ("Subscript with non-number", "var l: list[any] = []; return l['a'];", "List index must be a number"),
        ("Undeclared variable", "return x + 1;", "Undeclared variable 'x'"),
        ("Wrong type in list literal", "var l: list[number] = [1, 'a'];", "of type list[any] cannot be assigned to variable of type list[number]"),
        ("Set list element with wrong type", "var l: list[number] = [1]; l[0] = 'a';", "of type string to a list of type list[number]"),
        ("Assign list element to wrong type", "var l: list[number] = [1]; var s: string = l[0];", "of type number cannot be assigned to variable of type string"),
        ("Assigning list[any] to list[number]", "var l: list[any] = [1]; var n: list[number] = l;", "of type list[any] cannot be assigned to variable of type list[number]"),
        ("Wrong value type in dict literal", 'var d: dict[string, number] = {"a": "b"};', "of type dict[string, string] cannot be assigned to variable of type dict[string, number]"),
        ("Set dict element with wrong value type", 'var d: dict[string, number] = {}; d["a"] = "b";', "of type string to a dict of type dict[string, number]"),
        ("Set dict element with wrong key type", 'var d: dict[string, number] = {}; d[1] = 1;', "Key of type number cannot be used to index a dict with key type string"),
        ("Assign dict element to wrong type", 'var d: dict[string, number] = {"a": 1}; var s: string = d["a"];', "of type number cannot be assigned to variable of type string"),
        ("Component get non-existent prop", "component C {} var c = C(); return c.foo;", "has no property named 'foo'"),
        ("Component set wrong type", 'component C { p: 1; } var c = C(); c.p = "a";', "Cannot assign value of type string to property 'p' of type number"),
        ("Use 'this' outside component", "function foo() { return this; }", "Cannot use 'this' outside of a component method"),
        ("Access non-existent prop on 'this'", "component C { function get() { return this.foo; } }", "has no property named 'foo'"),
    ]

    valid_tests = [
        ("Correct assignment", "var x: number = 1; x = 2;"),
        ("String concatenation", "var s: string = 'a' + 'b';"),
        ("Boolean logic", "var b: bool = true == false;"),
        ("Valid if", "if (true) {}"),
        ("Valid while", "var b: bool = false; while(b) {}"),
        ("List creation", "var l = [1, 'a', true];"),
        ("Valid get list subscript", "var l = [1]; var x = l[0];"),
        ("Valid set list subscript", "var l = [1]; l[0] = 2;"),
        ("Dict creation", 'var d = {"a": 1, "b": "two"};'),
        ("Valid get dict subscript", 'var d = {"a": 1}; var x = d["a"];'),
        ("Valid set dict subscript", 'var d = {"a": 1}; d["a"] = 2;'),
        ("Declare generic list", "var l: list[number];"),
        ("Assign correctly typed list", "var l: list[number] = [1, 2];"),
        ("Assign list[number] to list[any]", "var l: list[any] = [1, 2];"),
        ("Get element from typed list", "var l: list[string] = ['a']; var s: string = l[0];"),
        ("Declare generic dict", "var d: dict[string, number];"),
        ("Assign correctly typed dict", 'var d: dict[string, number] = {"a": 1};'),
        ("Get element from typed dict", 'var d: dict[string, number] = {"a": 1}; var n: number = d["a"];'),
        ("Set element in typed dict", 'var d: dict[string, number] = {}; d["a"] = 1;'),
        ("Component valid access", 'component C { p: 1; } var c = C(); c.p = 2; var x: number = c.p;'),
        ("Component valid 'this' access", 'component C { p: 1; function f() { this.p = 2; } }'),
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
