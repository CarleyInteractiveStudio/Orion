from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser

def main():
    """
    Reads the test Orion file, parses it, and prints the AST or any errors.
    """
    try:
        with open("test.orion", "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print("Error: test.orion not found. Make sure it's in the same directory.")
        return

    lexer = Lexer(source_code)
    parser = Parser(lexer)
    program = parser.parse_program()

    if parser.errors:
        print("--- Parser Errors ---")
        for msg in parser.errors:
            print(f"  - {msg}")
        print("--- End of Errors ---")
    else:
        print("--- Abstract Syntax Tree (AST) ---")
        print(str(program))
        print("--- End of AST ---")

if __name__ == "__main__":
    main()
