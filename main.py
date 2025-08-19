import sys
from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser
from orion.evaluator.evaluator import eval_node
from orion.evaluator.environment import new_environment

def main():
    """
    Reads the main Orion test file, parses it, and (in the future) evaluates it.
    """
    print("--- Running Orion Toolchain ---")

    test_file = "test.orion"
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: {test_file} not found.")
        sys.exit(1)

    print("\n[1/2] Lexing and Parsing...")
    lexer = Lexer(source_code)
    parser = Parser(lexer)
    program = parser.parse_program()

    if parser.errors:
        print("--- Parser Errors Encountered (Known Limitations) ---")
        for msg in parser.errors:
            print(f"  - {msg}")
        print("--- End of Errors ---")
        # We don't exit here, to show that parsing can continue.
    else:
        print("--- Parsing Successful ---")


    print("\n[2/2] Evaluating (Partial Implementation)...")
    env = new_environment()
    evaluated = eval_node(program, env)

    print("\n--- Evaluator Result ---")
    if evaluated is not None:
        print(evaluated.to_string())
    else:
        print("Evaluation did not produce a final result.")
    print("--- End of Result ---")


if __name__ == "__main__":
    main()
