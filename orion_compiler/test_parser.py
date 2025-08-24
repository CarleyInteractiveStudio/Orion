import sys
from lexer import Lexer
from parser import Parser
from ast_printer import AstPrinter

def run_parser_test(name, source_code, expected_ast_str):
    """
    Runs a full lexer -> parser -> ast_printer test.
    """
    print(f"--- Running Parser Test: {name} ---")

    # 1. Lexer
    lexer = Lexer(source_code)
    tokens = lexer.scan_tokens()

    # 2. Parser
    parser = Parser(tokens)
    statements = parser.parse()

    # Check for parsing errors (parser prints them)
    # A more robust system would have the parser return errors instead of printing.
    # For now, we assume if statements are empty on non-empty code, something went wrong.
    if not statements and len(tokens) > 1:
        print(f"FAIL: {name} - Parser returned no statements.")
        return False

    # 3. AST Printer
    printer = AstPrinter()
    actual_ast_str = printer.print_program(statements)

    # 4. Compare
    # Normalize by stripping whitespace from each line and joining
    normalized_actual = "\n".join(line.strip() for line in actual_ast_str.strip().split('\n'))
    normalized_expected = "\n".join(line.strip() for line in expected_ast_str.strip().split('\n'))

    if normalized_actual == normalized_expected:
        print(f"PASS: {name}")
        return True
    else:
        print(f"FAIL: {name}")
        print("\n--- EXPECTED AST ---")
        print(normalized_expected)
        print("\n--- ACTUAL AST ---")
        print(normalized_actual)
        print("\n--------------------")
        return False

def main():
    tests_passed = 0
    total_tests = 0

    # Test 1: Simple variable declaration with a binary expression
    source1 = "var x = 10 * (2 + 3);"
    expected1 = """
    (var x (* 10 (group (+ 2 3))))
    """
    total_tests += 1
    if run_parser_test("Variable Declaration and Precedence", source1, expected1):
        tests_passed += 1

    # Test 2: Expression statement with comparisons
    source2 = "1 + 1 == 2;"
    expected2 = """
    (expr_stmt (== (+ 1 1) 2))
    """
    total_tests += 1
    if run_parser_test("Expression Statement with Equality", source2, expected2):
        tests_passed += 1

    # Test 3: Declaration without initializer
    source3 = "var y;"
    expected3 = """
    (var y)
    """
    total_tests += 1
    if run_parser_test("Declaration without Initializer", source3, expected3):
        tests_passed += 1

    # Test 4: Component parsing
    source4 = """
    component AlertBox {
        background: #ff3300;
        font: "Orbitron", 14;

        hover {
            background: #ff6600;
        }
    }
    """
    expected4 = """
(component AlertBox {
  (style background: # ff3300)
  (style font: "Orbitron" 14)
  (state hover {
    (style background: # ff6600)
  })
})
    """
    total_tests += 1
    if run_parser_test("Component Parsing", source4, expected4):
        tests_passed += 1

    # Test 5: Property set parsing
    source5 = "box.width = 100;"
    expected5 = """
    (expr_stmt (= width box 100))
    """
    total_tests += 1
    if run_parser_test("Property Set Parsing", source5, expected5):
        tests_passed += 1


    print(f"\n--- Parser Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1) # Exit with error code if any test fails

if __name__ == "__main__":
    main()
