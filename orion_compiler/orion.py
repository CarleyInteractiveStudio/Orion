from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult
from objects import OrionComponentInstance
from renderer import GraphicalRenderer

class Orion:
    """
    The main facade for the Orion language compiler/interpreter.
    This class ties together the different phases.
    """
    def __init__(self):
        self.vm = VM()
        self.had_error = False
        self.had_runtime_error = False

    def run(self, source: str, output_path: str = "output.png"):
        """
        Runs a piece of Orion source code. If a renderable 'App' component
        is found, it also renders it and saves it to the output_path.
        """
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()

        parser = Parser(tokens)
        statements = parser.parse()

        if not statements and len(tokens) > 1:
            return

        main_function = compile_source(statements)

        if main_function is None:
            self.had_error = True
            return

        result, last_value = self.vm.interpret(main_function)

        if result == InterpretResult.OK:
            app_instance = self.vm.globals.get("App")
            if isinstance(app_instance, OrionComponentInstance) and "render" in app_instance.definition.methods:
                self.vm.draw_commands = []
                self.vm.call_method_on_instance(app_instance, "render")

                renderer = GraphicalRenderer(400, 300)
                renderer.process_commands(self.vm.draw_commands)
                renderer.save_to_file(output_path)


    def run_file(self, path: str):
        """Runs an Orion script from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            self.run(source)
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
                self.had_error = False
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except EOFError:
                print("\nExiting.")
                break
