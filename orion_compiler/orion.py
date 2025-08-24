from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

class Orion:
    """
    The main facade for the Orion language compiler/interpreter.
    This class ties together the different phases.
    """
    def __init__(self):
        # In the future, we could have flags for different modes (e.g., REPL, file).
        self.had_error = False
        self.had_runtime_error = False

    def run(self, source: str):
        """Runs a piece of Orion source code."""
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()

        # In a real compiler, we would check for lexer errors here.

        parser = Parser(tokens)
        statements = parser.parse()

        # Check for parser errors (indicated by the parser printing errors).
        # A better system would have the parser return an error object.
        # For now, we'll assume no errors if statements are produced.

        interpreter = Interpreter()
        # We can pass the interpreter to the parser if needed for error reporting.

        # The interpret method will execute the code.
        # We'll modify it to return the final environment for module exports.
        final_environment = interpreter.interpret(statements)
        return final_environment

    def run_file(self, path: str):
        """Runs an Orion script from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            self.run(source)
            # Exit with an error code if there was a problem.
            if self.had_error: exit(65)
            if self.had_runtime_error: exit(70)
        except FileNotFoundError:
            print(f"Error: File not found at '{path}'")
            exit(1)

    def run_prompt(self):
        """Runs an interactive REPL session."""
        print("Orion REPL (Ctrl+C to exit)")
        while True:
            try:
                line = input("> ")
                if not line: continue
                self.run(line)
                self.had_error = False # Reset error for REPL
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except EOFError:
                print("\nExiting.")
                break
