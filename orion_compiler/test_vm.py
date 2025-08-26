import sys
import io
import os
from contextlib import redirect_stdout
from unittest.mock import patch

from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult
from disassembler import disassemble_chunk

def _orion_to_python_test_helper(value):
    from objects import OrionList, OrionDict, OrionInstance
    if isinstance(value, OrionList):
        return [_orion_to_python_test_helper(v) for v in value.elements]
    if isinstance(value, OrionDict):
        return {k: _orion_to_python_test_helper(v) for k, v in value.pairs.items()}
    if isinstance(value, OrionInstance):
        return {k: _orion_to_python_test_helper(v) for k, v in value.fields.items()}
    # Coerce all numbers to float for consistent comparison
    if isinstance(value, int):
        return float(value)
    return value

def run_vm_test(name, source_code, expected_value):
    """
    Runs the full new pipeline and checks the final result from the VM stack.
    """
    print(f"--- Running VM Test: {name} ---")

    main_function = compile_source(source_code)

    if main_function is None:
        print(f"FAIL: {name} - Compiler returned None.")
        return False

    vm = VM()
    result, final_value_orion = vm.interpret(main_function)

    if result != InterpretResult.OK:
        print(f"FAIL: {name} - VM did not return OK.")
        return False

    final_value = _orion_to_python_test_helper(final_value_orion)

    if final_value != expected_value:
        print(f"FAIL: {name}")
        print(f"Expected: {expected_value} (type: {type(expected_value)})")
        print(f"Got:      {final_value} (type: {type(final_value)})")
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
        main_function = compile_source(source_code)

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

def test_http_module():
    print("--- Running HTTP Module Tests ---")

    # Test case 1: Successful GET
    @patch('requests.get')
    def test_get_success(mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Success!"
        source = 'use http; return http.get("http://example.com");'
        return run_vm_test("HTTP GET Success", source, "Success!")

    # Test case 2: Failed GET (404)
    @patch('requests.get')
    def test_get_fail_404(mock_get):
        mock_get.return_value.status_code = 404
        source = 'use http; return http.get("http://example.com/404");'
        return run_vm_test("HTTP GET Fail 404", source, None)

    # Test case 3: Request Exception
    @patch('requests.get')
    def test_get_exception(mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.RequestException
        source = 'use http; return http.get("http://badurl");'
        return run_vm_test("HTTP GET Exception", source, None)

    results = [
        test_get_success(),
        test_get_fail_404(),
        test_get_exception(),
    ]

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"--- HTTP Tests Summary: {passed}/{total} passed ---")
    return passed, total


def main():
    tests = [
        ("Simple Arithmetic", "return (5 - 2) * (3 + 1);", 12.0),
        ("Complex Arithmetic", "return -(10 / 2) + 1;", -4.0),
        ("Global Variables", "var a = 10; var b = a + 5; a = 20; return a + b;", 35.0),
        ("Local Variables and Scopes", 'var a = "global a"; var b = "global b"; { var a = "inner a"; b = a; } return a + b;', "global ainner a"),
        ("If-Else Statement", "var x = 10; if (x > 5) { x = 20; } else { x = 0; } return x;", 20.0),
        ("While Loop", "var i = 0; var total = 0; while (i < 5) { total = total + i; i = i + 1; } return total;", 10.0),
        ("Functions (Fibonacci)", "function fib(n) { if (n < 2) { return n; } return fib(n - 2) + fib(n - 1); } return fib(8);", 21.0),
        ("List Get", "var a = [10, 20, 30]; return a[1];", 20),
        ("List Set", "var a = [10, 20]; a[0] = 99; return a[0];", 99),
        ("List Index with Expression", "var a = [10, 20, 30]; var i = 1; return a[i+1];", 30),
        ("Dict Get", 'return {"a": 100, "b": 200}["a"];', 100),
        ("Dict Set", 'var d = {"a": 1}; d["a"] = 99; return d["a"];', 99),
        ("Dict Set New Key", 'var d = {}; d["new"] = "value"; return d["new"];', "value"),
        ("Dict Get Missing Key", 'return {"a": 1}["b"];', None),
        ("Component Full Lifecycle", 'component Button { text: "default"; width: 100; enabled: true;} var b1 = Button(); var b2 = Button(); b2.text = "new text"; return b1.text + " " + b2.text;', "default new text"),
        ("Component Method Call", 'component Counter { value: 0; function increment() { this.value = this.value + 1; } } var c = Counter(); c.increment(); c.increment(); return c.value;', 2),
    ]

    runtime_error_tests = [
        ("Index Out of Bounds (Get)", "return [1][10];", "List index 10 out of range"),
        ("Index Out of Bounds (Set)", "var a = [1]; a[10] = 2;", "List index 10 out of range"),
        ("Component with Arguments", 'component Button {} return Button(1);', "Component constructor argument must be a dictionary"),
    ]

    TEST_FILE = "orion_test_file.tmp"
    io_tests = [
        ("IO Write & Exists", f'use io; io.write("{TEST_FILE}", "hello"); return io.exists("{TEST_FILE}");', True),
        ("IO Read", f'use io; return io.read("{TEST_FILE}");', "hello"),
        ("IO Append", f'use io; io.append("{TEST_FILE}", " world"); return io.read("{TEST_FILE}");', "hello world"),
        ("IO Read Non-existent", 'use io; return io.read("non_existent_file.tmp");', None),
    ]

    string_tests = [
        ("String Length", 'use str; return str.length("hello");', 5),
        ("String To Upper", 'use str; return str.toUpperCase("world");', "WORLD"),
        ("String To Lower", 'use str; return str.toLowerCase("WORLD");', "world"),
        ("String Contains (True)", 'use str; return str.contains("hello world", "lo w");', True),
        ("String Contains (False)", 'use str; return str.contains("hello world", "abc");', False),
        ("String Split", 'use str; return str.split("a,b,c", ",");', ["a", "b", "c"]),
        ("String Join", 'use str; return str.join(["a", "b", "c"], "-");', "a-b-c"),
    ]

    math_tests = [
        ("Math PI", 'use math; return math.PI;', 3.141592653589793),
        ("Math Sqrt", 'use math; return math.sqrt(16);', 4.0),
        ("Math Pow", 'use math; return math.pow(2, 8);', 256.0),
        ("Math Sin", 'use math; return math.sin(0);', 0.0),
    ]

    json_tests = [
        ("JSON Parse", 'use json; return json.parse(\'{"a": 1, "b": [2, 3]}\');', {'a': 1.0, 'b': [2.0, 3.0]}),
        ("JSON Stringify Roundtrip", 'use json; var obj = {"a": 1}; var s = json.stringify(obj); return json.parse(s);', {'a': 1.0}),
        ("JSON Roundtrip Nested", 'use json; var obj = {"c": 3, "d": {"e": 4}}; var s = json.stringify(obj); return json.parse(s);', {'c': 3.0, 'd': {'e': 4.0}}),
    ]

    all_tests = tests + io_tests + string_tests + math_tests + json_tests
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

    # Run HTTP tests
    http_passed, http_total = test_http_module()
    tests_passed += http_passed
    total_tests += http_total

    print(f"--- Running VM Test: Native Print ---")
    total_tests += 1
    source_print = 'print("hello", 123, [1,2], {"a": 1});'
    f = io.StringIO()
    with redirect_stdout(f):
        main_function = compile_source(source_print)
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
