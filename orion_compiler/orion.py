import time
import sdl2
import sdl2.ext
import skia
import ctypes

from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult
from objects import OrionComponentInstance
from renderer import GraphicalRenderer
from event_dispatcher import EventDispatcher


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
        is found, it opens a window and begins the event loop.
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

        # Run the script to define components, create instances, etc.
        result, _ = self.vm.interpret(main_function)

        # After the script runs, check for an 'App' component to render.
        app_instance = self.vm.globals.get("App")
        if result == InterpretResult.OK and isinstance(app_instance, OrionComponentInstance):
            self._run_gui(app_instance)
        else:
            print("INFO: No 'App' component instance found or script failed. Exiting.")


    def _run_gui(self, app_instance: OrionComponentInstance):
        """Initializes SDL2 and starts the main application loop."""
        print("INFO: Starting Orion GUI application...")

        sdl2.ext.init()

        WIDTH, HEIGHT = 800, 600
        window = sdl2.ext.Window("Orion Application", size=(WIDTH, HEIGHT))
        window.show()

        window_surface = window.get_surface()
        renderer = GraphicalRenderer(WIDTH, HEIGHT)
        dispatcher = EventDispatcher()

        running = True
        event = sdl2.SDL_Event()
        while running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    running = False

                dispatcher.dispatch(event, self.vm, [app_instance])

            # --- Efficient Render a frame ---
            if app_instance.dirty:
                print("DEBUG: Dirty flag was set, re-rendering.")
                self.vm.draw_commands = []
                self.vm.call_method_on_instance(app_instance, "render")

                renderer.process_commands(self.vm.draw_commands)
                skia_pixels = renderer.surface.tobytes()
                ctypes.memmove(window_surface.pixels, skia_pixels, len(skia_pixels))

                window.refresh()
                app_instance.dirty = False # Reset dirty flag after rendering

            sdl2.SDL_Delay(10)

        sdl2.ext.quit()


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
                self.vm = VM()
                self.run(line)
                self.had_error = False
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except EOFError:
                print("\nExiting.")
                break
