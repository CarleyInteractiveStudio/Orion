import sys

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

    print("\n--- Disassembly ---")
    disassemble_chunk(main_function.chunk, f"{name} Chunk")
    print("-------------------\n")

    vm = VM()
    result, final_value = vm.interpret(main_function)

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
    tests = [
        ("Simple Arithmetic", "return (5 - 2) * (3 + 1);", 12.0),
        ("Complex Arithmetic", "return -(10 / 2) + 1;", -4.0),
        ("Global Variables", "var a = 10; var b = a + 5; a = 20; return a + b;", 35.0),
        ("Local Variables and Scopes", 'var a = "global a"; var b = "global b"; { var a = "inner a"; b = a; } return a + b;', "global ainner a"),
        ("If-Else Statement", "var x = 10; if (x > 5) { x = 20; } else { x = 0; } return x;", 20.0),
        ("While Loop", "var i = 0; var total = 0; while (i < 5) { total = total + i; i = i + 1; } return total;", 10.0),
        ("Functions (Fibonacci)", "function fib(n) { if (n < 2) { return n; } return fib(n - 2) + fib(n - 1); } return fib(8);", 21.0)
    ]

    tests_passed = 0
    for name, source, expected in tests:
        if run_vm_test(name, source, expected):
            tests_passed += 1

    total_tests = len(tests)
    print(f"\n--- VM Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
