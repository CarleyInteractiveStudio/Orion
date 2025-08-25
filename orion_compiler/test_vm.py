import sys
import io
import os
from contextlib import redirect_stdout

from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult
from disassembler import disassemble_chunk

def run_vm_test(name, source_code, expected_value):
    """
    Runs the full new pipeline and checks the final result from the VM stack.
    """
    print(f"--- Running VM Test: {name} ---")

    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    if not statements and len(tokens) > 1:
        print(f"FAIL: {name} - Parser produced no statements.")
        return False

    main_function = compile_source(statements)

    if main_function is None:
        print(f"FAIL: {name} - Compiler returned None.")
        return False

    vm = VM()
    result, final_value = vm.interpret(main_function)

    if result != InterpretResult.OK:
        print(f"FAIL: {name} - VM did not return OK.")
        return False

    if isinstance(expected_value, list):
        if not isinstance(final_value, list) or final_value != expected_value:
            print(f"FAIL: {name}")
            print(f"Expected list: {expected_value}")
            print(f"Got:           {final_value}")
            return False
    elif final_value != expected_value:
        print(f"FAIL: {name}")
        print(f"Expected final value: {expected_value} (type: {type(expected_value)})")
        print(f"Got:                  {final_value} (type: {type(final_value)})")
        return False

    print(f"PASS: {name}")
    return True

def run_vm_runtime_error_test(name, source_code, expected_error_fragment):
    """
    Runs the VM and expects a runtime error to be caught.
    """
    print(f"--- Running VM Test (Runtime Error): {name} ---")

    f = io.StringIO()
    with redirect_stdout(f):
        lexer = Lexer(source_code)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        main_function = compile_source(statements)

        if main_function is None:
            print(f"FAIL: {name} - Code failed to compile.")
            return False

        vm = VM()
        result, _ = vm.interpret(main_function)

    output = f.getvalue()

    if result != InterpretResult.RUNTIME_ERROR:
        print(f"FAIL: {name} - VM did not return RUNTIME_ERROR.")
        return False

    if expected_error_fragment in output:
        print(f"PASS: {name}")
        return True
    else:
        print(f"FAIL: {name}")
        print(f"Expected error fragment: '{expected_error_fragment}'")
        print(f"Got stdout output: '{output.strip()}'")
        return False

def main():
    def get_list_elements(vm_list):
        return vm_list.elements

    tests = [
        ("Simple Arithmetic", "return (5 - 2) * (3 + 1);", 12.0),
        ("Complex Arithmetic", "return -(10 / 2) + 1;", -4.0),
        ("Global Variables", "var a = 10; var b = a + 5; a = 20; return a + b;", 35.0),
        ("Local Variables and Scopes", 'var a = "global a"; var b = "global b"; { var a = "inner a"; b = a; } return a + b;', "global ainner a"),
        ("If-Else Statement", "var x = 10; if (x > 5) { x = 20; } else { x = 0; } return x;", 20.0),
        ("While Loop", "var i = 0; var total = 0; while (i < 5) { total = total + i; i = i + 1; } return total;", 10.0),
        ("Functions (Fibonacci)", "function fib(n) { if (n < 2) { return n; } return fib(n - 2) + fib(n - 1); } return fib(8);", 21.0),
        ("Module System", "use math; return math.add(10, 5) + math.PI;", 15.0 + 3.14159),
        ("List Get", "var a = [10, 20, 30]; return a[1];", 20),
        ("List Set", "var a = [10, 20]; a[0] = 99; return a[0];", 99),
        ("List Index with Expression", "var a = [10, 20, 30]; var i = 1; return a[i+1];", 30),
        ("Dict Get", 'return {"a": 100, "b": 200}["a"];', 100),
        ("Dict Set", 'var d = {"a": 1}; d["a"] = 99; return d["a"];', 99),
        ("Dict Set New Key", 'var d = {}; d["new"] = "value"; return d["new"];', "value"),
        ("Dict Get Missing Key", 'return {"a": 1}["b"];', None),
        # C-style for loops
        ("For Loop", "var a = 0; for (var i = 0; i < 5; i = i + 1) { a = a + i; } return a;", 10),
        ("For Loop No Initializer", "var i = 0; var a = 0; for (; i < 5; i = i + 1) { a = a + i; } return a;", 10),
        ("For Loop No Increment", "var a = 0; for (var i = 0; i < 5;) { a = a + i; i = i + 1; } return a;", 10),
        ("For Loop Scope", "var a = 10; for (var a = 0; a < 2; a = a + 1) {} return a;", 10),
        ("Component Full Lifecycle", 'component Button { text: "default"; width: 100; enabled: true;} var b1 = Button(); var b2 = Button(); b2.text = "new text"; return b1.text + " " + b2.text;', "default new text"),
    ]

    runtime_error_tests = [
        ("Index Out of Bounds (Get)", "return [1][10];", "List index 10 out of range"),
        ("Index Out of Bounds (Set)", "var a = [1]; a[10] = 2;", "List index 10 out of range"),
        ("Component with Arguments", 'component Button {} return Button(1);', "constructor takes no arguments, but got 1"),
    ]

    TEST_FILE = "orion_test_file.tmp"
    io_tests = [
        ("IO Write & Exists", f'use io; io.write("{TEST_FILE}", "hello"); return io.exists("{TEST_FILE}");', True),
        ("IO Read", f'use io; return io.read("{TEST_FILE}");', "hello"),
        ("IO Append", f'use io; io.append("{TEST_FILE}", " world"); return io.read("{TEST_FILE}");', "hello world"),
        ("IO Read Non-existent", 'use io; return io.read("non_existent_file.tmp");', None),
    ]

    all_tests = tests + io_tests
    tests_passed = 0

    try:
        for name, source, expected in all_tests:
            if run_vm_test(name, source, expected):
                tests_passed += 1

        for name, source, expected in runtime_error_tests:
            if run_vm_runtime_error_test(name, source, expected):
                tests_passed += 1
    finally:
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)

    total_tests = len(all_tests) + len(runtime_error_tests)

    print(f"--- Running VM Test: Native Print ---")
    total_tests += 1
    source_print = 'print("hello", 123, [1,2], {"a": 1});'
    f = io.StringIO()
    with redirect_stdout(f):
        lexer = Lexer(source_print)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        main_function = compile_source(statements)
        vm = VM()
        vm.interpret(main_function)
    output = f.getvalue()
    if 'hello 123 [1, 2] {"a": 1}\n' in output:
        print("PASS: Native Print")
        tests_passed += 1
    else:
        print(f"FAIL: Native Print")

    print(f"\n--- VM Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
