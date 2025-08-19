import sys
from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser
from orion.evaluator.evaluator import eval_node
from orion.evaluator.environment import new_environment

def main():
    """
    Reads the main Orion test file, parses it, and evaluates it.
    """
    print("--- Running Orion Toolchain ---")

    test_file = "test.orion"
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: {test_file} not found.")
        sys.exit(1)

    # 1. Lexing & Parsing
    print("\n[1/2] Parsing...")
    lexer = Lexer(source_code)
    parser = Parser(lexer)
    program = parser.parse_program()

    if parser.errors:
        print("--- Parser Errors Encountered (Known Limitations) ---")
        for msg in parser.errors:
            print(f"  - {msg}")
        print("--- End of Errors ---")
    else:
        print("--- Parsing Successful ---")

    # 2. Evaluation
    print("\n[2/2] Evaluating...")
    from orion.evaluator.builtins import builtins
    env = new_environment()
    for name, fn in builtins.items():
        env.set(name, fn)

    evaluated = eval_node(program, env)

    print("\n--- Evaluator Result ---")
    if evaluated is not None:
        print(evaluated.to_string())
    else:
        print("Evaluation did not produce a final result.")
    print("--- End of Result ---")


if __name__ == "__main__":
    main()
