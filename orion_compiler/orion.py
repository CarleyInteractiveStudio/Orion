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
        # The compile function handles lexing and parsing internally.
        main_function = compile_source(source)

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
        Handles special layout components like 'Column' and 'Row'.
        """
        # Determine the component's absolute position.
        # This position is the base for its children's layout.
        base_abs_x = offset_x + component_instance.fields.get('x', 0)
        base_abs_y = offset_y + component_instance.fields.get('y', 0)

        node = {
            "instance": component_instance,
            "x": base_abs_x,
            "y": base_abs_y,
            "width": component_instance.fields.get('width', 0),
            "height": component_instance.fields.get('height', 0),
            "children": []
        }

        # Get the list of child instances to process
        children_to_process = []
        is_layout_component = component_instance.definition.name in ("Column", "Row")

        if is_layout_component:
            children_field = component_instance.fields.get("children")
            if isinstance(children_field, OrionList):
                children_to_process = children_field.elements
        elif "render" in component_instance.definition.methods:
            commands_before = len(self.vm.draw_commands)
            rendered_output = self.vm.call_method_on_instance(component_instance, "render")

            # Adjust the coordinates of any new draw commands by the component's absolute position.
            for i in range(commands_before, len(self.vm.draw_commands)):
                command = self.vm.draw_commands[i]
                command['x'] += base_abs_x
                command['y'] += base_abs_y

            if isinstance(rendered_output, OrionList):
                children_to_process = rendered_output.elements
        else:
            return node

        # Process the children, applying layout logic if necessary
        if is_layout_component and component_instance.definition.name == "Column":
            spacing = component_instance.fields.get('spacing', 0)
            padding = component_instance.fields.get('padding', 0)
            align = component_instance.fields.get('align', 'start')
            parent_width = component_instance.fields.get('width', 0)
            current_y_offset = padding
            for i, child_instance in enumerate(children_to_process):
                if isinstance(child_instance, OrionComponentInstance):
                    if i > 0:
                        current_y_offset += spacing

                    child_width = child_instance.fields.get('width', 0)
                    if child_width == 0 and child_instance.definition.name == 'Label':
                        child_width = len(child_instance.fields.get('text', '')) * (child_instance.fields.get('fontSize', 16) * 0.6)

                    x_offset = padding
                    if align == 'center':
                        x_offset = (parent_width - child_width) / 2
                    elif align == 'end':
                        x_offset = parent_width - child_width - padding

                    child_node = self._build_scene_graph(child_instance, base_abs_x + x_offset, base_abs_y + current_y_offset)
                    if child_node:
                        node["children"].append(child_node)
                        child_height = child_node["height"]
                        if child_height == 0 and child_node["instance"].definition.name == 'Label':
                            child_height = child_node["instance"].fields.get('fontSize', 16) * 1.5
                        current_y_offset += child_height

        elif is_layout_component and component_instance.definition.name == "Row":
            spacing = component_instance.fields.get('spacing', 0)
            padding = component_instance.fields.get('padding', 0)
            align = component_instance.fields.get('align', 'start')
            parent_height = component_instance.fields.get('height', 0)
            current_x_offset = padding
            for i, child_instance in enumerate(children_to_process):
                if isinstance(child_instance, OrionComponentInstance):
                    if i > 0:
                        current_x_offset += spacing

                    child_height = child_instance.fields.get('height', 0)
                    if child_height == 0 and child_instance.definition.name == 'Label':
                        child_height = child_instance.fields.get('fontSize', 16) * 1.5

                    y_offset = padding
                    if align == 'center':
                        y_offset = (parent_height - child_height) / 2
                    elif align == 'end':
                        y_offset = parent_height - child_height - padding

                    child_node = self._build_scene_graph(child_instance, base_abs_x + current_x_offset, base_abs_y + y_offset)
                    if child_node:
                        node["children"].append(child_node)
                        child_width = child_node["width"]
                        if child_width == 0 and child_node["instance"].definition.name == 'Label':
                            text = child_node["instance"].fields.get('text', '')
                            font_size = child_node["instance"].fields.get('fontSize', 16)
                            child_width = len(text) * (font_size * 0.6)
                        current_x_offset += child_width
        else:
            # Default behavior: children are positioned relative to the parent's origin.
            for child_instance in children_to_process:
                if isinstance(child_instance, OrionComponentInstance):
                    child_node = self._build_scene_graph(child_instance, base_abs_x, base_abs_y)
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

if __name__ == "__main__":
    import sys
    orion = Orion()
    if len(sys.argv) > 2:
        print("Usage: orion [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        orion.run_file(sys.argv[1])
    else:
        orion.run_prompt()
