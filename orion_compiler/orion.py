import time
import sdl2
import sdl2.ext
import skia
import ctypes

from lexer import Lexer
from parser import Parser
from compiler import compile as compile_source
from vm import VM, InterpretResult
from objects import OrionComponentInstance, OrionList
from renderer import GraphicalRenderer
from event_dispatcher import EventDispatcher


class Orion:
    """
    The main facade for the Orion language compiler/interpreter.
    This class ties together the different phases.
    """
    def __init__(self):
        self.vm = VM()
        self.scene_graph = None # Will hold the tree of rendered components
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

        app_instance = self.vm.globals.get("App")
        if result == InterpretResult.OK and isinstance(app_instance, OrionComponentInstance):
            self._run_gui(app_instance)
        else:
            print("INFO: No 'App' component instance found or script failed. Exiting.")


    def _build_scene_graph(self, component_instance, offset_x, offset_y):
        """
        Recursively traverses the component tree, calling render() on each,
        and builds a 'scene graph' - a tree of dictionaries containing the
        instance, its absolute coordinates, and its children.
        This also populates the vm.draw_commands list as a side effect.
        """
        if "render" not in component_instance.definition.methods:
            return None

        # The component's own position is relative to its parent's offset.
        abs_x = offset_x + component_instance.fields.get('x', 0)
        abs_y = offset_y + component_instance.fields.get('y', 0)

        commands_before = len(self.vm.draw_commands)
        children = self.vm.call_method_on_instance(component_instance, "render")

        # Adjust the coordinates of the new commands by the component's absolute position.
        for i in range(commands_before, len(self.vm.draw_commands)):
            command = self.vm.draw_commands[i]
            command['x'] += abs_x
            command['y'] += abs_y

        node = {
            "instance": component_instance,
            "x": abs_x,
            "y": abs_y,
            "width": component_instance.fields.get('width', 0),
            "height": component_instance.fields.get('height', 0),
            "children": []
        }

        if isinstance(children, OrionList):
            for child in children.elements:
                if isinstance(child, OrionComponentInstance):
                    child_node = self._build_scene_graph(child, abs_x, abs_y)
                    if child_node:
                        node["children"].append(child_node)

        return node


    def _run_gui(self, app_instance: OrionComponentInstance):
        """Initializes SDL2 and starts the main application loop."""
        print("INFO: Starting Orion GUI application...")

        sdl2.ext.init()

        WIDTH, HEIGHT = 800, 600
        window = sdl2.ext.Window("Orion Application", size=(WIDTH, HEIGHT))
        window.show()

        sdl2.SDL_StartTextInput() # Enable text input events

        window_surface = window.get_surface()
        renderer = GraphicalRenderer(WIDTH, HEIGHT)
        dispatcher = EventDispatcher()

        running = True
        event = sdl2.SDL_Event()
        while running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    running = False

                if self.scene_graph: # Only dispatch if we have a scene graph
                    dispatcher.dispatch(event, self.vm, self.scene_graph)

            if app_instance.dirty:
                print("DEBUG: Dirty flag was set, re-rendering.")
                self.vm.draw_commands = []

                # Rebuild the scene graph and populate draw commands
                self.scene_graph = self._build_scene_graph(app_instance, 0, 0)

                renderer.process_commands(self.vm.draw_commands)
                skia_pixels = renderer.surface.tobytes()
                ctypes.memmove(window_surface.pixels, skia_pixels, len(skia_pixels))

                window.refresh()
                app_instance.dirty = False

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
