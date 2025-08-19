import sys
from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser
from orion.evaluator.evaluator import eval_node
from orion.evaluator.environment import new_environment

def main():
    """
    Reads a test Orion file, parses it, evaluates it, and prints the result.
    """
    print("--- Starting Orion Interpreter ---")

    test_file = "interpreter_test.orion"
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: {test_file} not found.")
        sys.exit(1)

    print("[1/3] Lexing...")
    lexer = Lexer(source_code)

    print("[2/3] Parsing...")
    parser = Parser(lexer)
    program = parser.parse_program()

    if parser.errors:
        print("--- Parser Errors ---")
        for msg in parser.errors:
            print(f"  - {msg}")
        print("--- End of Errors ---")
        sys.exit(1)

    print("[3/3] Evaluating...")
    env = new_environment()
    evaluated = eval_node(program, env)

    print("\n--- Evaluator Result ---")
    if evaluated is not None:
        print(evaluated.to_string())
    else:
        print("No result from evaluation (or result was NULL).")
    print("--- End of Result ---")


if __name__ == "__main__":
    main()
