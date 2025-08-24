from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult

class Orion:
    """
    The main facade for the Orion language compiler/interpreter.
    This class ties together the different phases.
    """
    def __init__(self):
        self.vm = VM()
        self.had_error = False
        self.had_runtime_error = False

    def run(self, source: str):
        """Runs a piece of Orion source code using the new Compiler -> VM pipeline."""
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()

        parser = Parser(tokens)
        statements = parser.parse()

        # In a real compiler, we would check for parser errors here and stop.

        main_function = compile_source(statements)

        if main_function is None:
            self.had_error = True
            return None

        result, last_value = self.vm.interpret(main_function)

        return result, last_value

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
