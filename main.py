import sys
from orion.lexer.lexer import Lexer
from orion.parser.parser import Parser
from orion.evaluator import evaluator
from orion.evaluator.environment import new_environment

def main():
    """
    Reads the main Orion test file, parses it, and evaluates it.
    """
    print("--- Running Orion Toolchain ---")

    # --- Load Modules into Cache (for main test file) ---
    evaluator.MODULE_CACHE["UI_source"] = "let createWindow = function(title, size) {};"
    evaluator.MODULE_CACHE["Hardware_source"] = """
let sensor = {"read": function(name) { return 76; }};
let fan = {"setSpeed": function(speed) {}};
"""

    # --- Load Main File ---
    main_file = "test.orion"
    try:
        with open(main_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: {main_file} not found.")
        sys.exit(1)

    # --- Run Toolchain ---
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

    print("\n[2/2] Evaluating...")
    env = new_environment()
    # injecting built-ins is now handled inside the evaluator for simplicity
    # in a real scenario, this would be more robust

    evaluated = evaluator.eval_node(program, env)

    print("\n--- Evaluator Result ---")
    if evaluated is not None:
        print(evaluated.to_string())
    else:
        print("Evaluation did not produce a final result.")
    print("--- End of Result ---")


if __name__ == "__main__":
    main()
