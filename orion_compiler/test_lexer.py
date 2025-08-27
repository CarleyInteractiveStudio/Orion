import sys
from . lexer import Lexer
from . tokens import TokenType, Token

def run_test(name, source, expected_tokens):
    """Helper function to run a single lexer test case."""
    print(f"--- Running Test: {name} ---")
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Extracting token types for comparison
    actual_types = [token.token_type for token in tokens]
    expected_types = [token.token_type for token in expected_tokens]

    if actual_types != expected_types:
        print(f"FAIL: {name}")
        print(f"Expected: {expected_types}")
        print(f"Got:      {actual_types}")
        # Also print full tokens for easier debugging
        print("\nExpected Tokens:")
        for t in expected_tokens: print(t)
        print("\nActual Tokens:")
        for t in tokens: print(t)
        return False

    # Optional: Check lexemes and literals for more thorough testing
    for i, token in enumerate(tokens):
        expected_token = expected_tokens[i]
        if token.lexeme != expected_token.lexeme or token.literal != expected_token.literal:
            print(f"FAIL: {name} (Mismatch at token {i})")
            print(f"Expected: {expected_token}")
            print(f"Got:      {token}")
            return False

    print(f"PASS: {name}")
    return True


def main():
    tests_passed = 0
    total_tests = 0

    # Test 1: Simple variable declaration
    source1 = "var x = 10;"
    expected1 = [
        Token(TokenType.VAR, 'var', None, 1),
        Token(TokenType.IDENTIFIER, 'x', None, 1),
        Token(TokenType.EQUAL, '=', None, 1),
        Token(TokenType.NUMBER, '10', 10, 1),
        Token(TokenType.SEMICOLON, ';', None, 1),
        Token(TokenType.EOF, '', None, 1)
    ]
    total_tests += 1
    if run_test("Simple Variable Declaration", source1, expected1):
        tests_passed += 1

    # Test 2: Code with comments and different spacing
    source2 = """
    // Simple function
    function main() {
        let y = "hello"; /* block comment */
    }
    """
    expected2 = [
        Token(TokenType.FUNCTION, 'function', None, 3),
        Token(TokenType.IDENTIFIER, 'main', None, 3),
        Token(TokenType.LEFT_PAREN, '(', None, 3),
        Token(TokenType.RIGHT_PAREN, ')', None, 3),
        Token(TokenType.LEFT_BRACE, '{', None, 3),
        Token(TokenType.LET, 'let', None, 4),
        Token(TokenType.IDENTIFIER, 'y', None, 4),
        Token(TokenType.EQUAL, '=', None, 4),
        Token(TokenType.STRING, '"hello"', 'hello', 4),
        Token(TokenType.SEMICOLON, ';', None, 4),
        Token(TokenType.RIGHT_BRACE, '}', None, 5),
        Token(TokenType.EOF, '', None, 6)
    ]
    total_tests += 1
    if run_test("Function with Comments", source2, expected2):
        tests_passed += 1

    # Test 3: Style properties from the spec
    source3 = """
    component Box {
        color: #ff00ff;
        hover { scale: 1.05; }
    }
    """
    expected3 = [
        Token(TokenType.COMPONENT, 'component', None, 2),
        Token(TokenType.IDENTIFIER, 'Box', None, 2),
        Token(TokenType.LEFT_BRACE, '{', None, 2),
        Token(TokenType.IDENTIFIER, 'color', None, 3),
        Token(TokenType.COLON, ':', None, 3),
        Token(TokenType.HASH, '#', None, 3),
        Token(TokenType.IDENTIFIER, 'ff00ff', None, 3),
        Token(TokenType.SEMICOLON, ';', None, 3),
        Token(TokenType.HOVER, 'hover', None, 4),
        Token(TokenType.LEFT_BRACE, '{', None, 4),
        Token(TokenType.IDENTIFIER, 'scale', None, 4),
        Token(TokenType.COLON, ':', None, 4),
        Token(TokenType.NUMBER, '1.05', 1.05, 4),
        Token(TokenType.SEMICOLON, ';', None, 4),
        Token(TokenType.RIGHT_BRACE, '}', None, 4),
        Token(TokenType.RIGHT_BRACE, '}', None, 5),
        Token(TokenType.EOF, '', None, 6)
    ]
    total_tests += 1
    if run_test("Component with Styles", source3, expected3):
        tests_passed += 1

    print(f"\n--- Test Summary ---")
    print(f"{tests_passed} / {total_tests} tests passed.")

    if tests_passed != total_tests:
        sys.exit(1) # Exit with error code if any test fails


if __name__ == "__main__":
    main()
