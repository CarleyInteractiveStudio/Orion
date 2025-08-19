import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser
from orion.evaluator import evaluator
from orion.evaluator.environment import new_environment

def main():
    """
    Runs the full Orion toolchain on the main test file.
    """
    print("--- Running Orion Final Test ---")

    try:
        with open("test.orion", "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print("Error: test.orion not found.")
        sys.exit(1)

    # 1. Parsing
    print("\n[1/2] Parsing...")
    parser = Parser(Lexer(source_code))
    program = parser.parse_program()

    if parser.errors:
        print("--- Parser Errors ---")
        for msg in parser.errors:
            print(f"  - {msg}")
        print("--- End of Errors ---")
        sys.exit(1) # Stop if there are parsing errors
    else:
        print("--- Parsing Successful ---")

    # 2. Evaluation
    print("\n[2/2] Evaluating...")
    env = new_environment()
    evaluated = evaluator.eval_node(program, env)

    print("\n--- Evaluator Result ---")
    if evaluated is not None:
        print(f"OK. Final evaluated object: {evaluated.to_string()}")
    else:
        print("OK. Evaluation finished without a final value.")
    print("--- End of Test ---")


if __name__ == "__main__":
    main()
