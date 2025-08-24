import sys

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from tokens import Token, TokenType

def run_interpreter_test(name, source_code, expected_vars):
    """
    Runs a full lexer -> parser -> interpreter test and checks final variable states.
    """
    print(f"--- Running Interpreter Test: {name} ---")

    # 1. Lexer & Parser
    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    # Basic check to ensure parser produced an AST
    if not statements and len(tokens) > 1:
        print(f"FAIL: {name} - Parser returned no statements.")
        return False

    # 2. Interpreter
    interpreter = Interpreter()
    interpreter.interpret(statements)

    # 3. Verify final state
    for var_name, expected_value in expected_vars.items():
        # We need a dummy token for the environment's get method
        dummy_token = Token(TokenType.IDENTIFIER, var_name, None, 0)
        try:
            actual_value = interpreter.environment.get(dummy_token)
            if actual_value != expected_value:
                print(f"FAIL: {name}")
                print(f"Verification failed for variable '{var_name}'.")
                print(f"Expected: {expected_value} (type: {type(expected_value)})")
                print(f"Got:      {actual_value} (type: {type(actual_value)})")
                return False
        except Exception as e:
            print(f"FAIL: {name}")
            print(f"An exception occurred while getting variable '{var_name}': {e}")
            return False

    print(f"PASS: {name}")
    return True

def main():
    tests_passed = 0
    total_tests = 0

    # Test 1: Arithmetic and variable assignment
    source1 = """
    var x = 10;
    var y = x * 2 + 5; // Should be 25
    """
    expected1 = {"y": 25.0}
    total_tests += 1
    if run_interpreter_test("Arithmetic and Variables", source1, expected1):
        tests_passed += 1

    # Test 2: String concatenation
    source2 = """
    var a = "hello";
    var b = " world";
    var c = a + b;
    """
    expected2 = {"c": "hello world"}
    total_tests += 1
    if run_interpreter_test("String Concatenation", source2, expected2):
        tests_passed += 1

    # Test 3: Comparisons and truthiness
    source3 = """
    var t = 10 > 5;      // true
    var f = 10 == 11;    // false
    """
    expected3 = {"t": True, "f": False}
    total_tests += 1
    if run_interpreter_test("Comparisons and Booleans", source3, expected3):
        tests_passed += 1

    print(f"\n--- Interpreter Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
