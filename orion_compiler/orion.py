import time
import sdl2
import sdl2.ext
import skia
import ctypes
import os
import re

from .lexer import Lexer
from .parser import Parser
from .compiler import compile as compile_source
from .vm import VM, InterpretResult
from .objects import OrionComponentInstance, OrionList
from .renderer import GraphicalRenderer
from .event_dispatcher import EventDispatcher


class Orion:
    """
    The main facade for the Orion language compiler/interpreter.
    This class ties together the different phases.
    """
    def __init__(self):
        self.vm = VM()
        self.scene_graph = None
        self.had_error = False
        self.had_runtime_error = False

    def _find_module_path(self, module_name: str, base_path: str) -> str | None:
        """Finds a module file path."""
        base_dir = os.path.dirname(os.path.abspath(base_path))
        possible_paths = [
            os.path.join(base_dir, f"{module_name}.orion"),
            f"orion_compiler/stdlib/{module_name}.orion",
            f"{module_name}.orion",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def _resolve_dependencies(self, entry_path: str) -> list[str]:
        """Performs a topological sort of the dependency graph."""
        graph = {}
        entry_abspath = os.path.abspath(entry_path)

        nodes_to_process = [entry_abspath]
        processed_nodes = set()

        while nodes_to_process:
            current_path = nodes_to_process.pop(0)
            if current_path in processed_nodes:
                continue

            processed_nodes.add(current_path)

            try:
                with open(current_path, 'r', encoding='utf-8') as f:
                    source = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Module file not found: {current_path}")

            dependencies = []
            module_names = re.findall(r'^\s*use\s+([a-zA-Z_][a-zA-Z0-9_]*);', source, re.MULTILINE)
            for name in module_names:
                dep_path = self._find_module_path(name, current_path)
                if dep_path:
                    dependencies.append(dep_path)
                    nodes_to_process.append(dep_path)
            graph[current_path] = dependencies

        sorted_list = []
        visiting = set()
        visited = set()

        def visit(node):
            if node in visited: return
            if node in visiting: raise Exception(f"Circular dependency detected involving {node}")

            visiting.add(node)
            if node in graph:
                for dep in graph[node]:
                    visit(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_list.append(node)

        visit(entry_abspath)
        return sorted_list

    def run(self, source: str, output_path: str = "output.png"):
        """
        Runs a piece of Orion source code. This is a simple version for REPL or single strings
        without complex dependencies.
        """
        # This simple run method is now only for the REPL.
        main_function = compile_source(source)
        if main_function is None:
            self.had_error = True
            return
        result, _ = self.vm.interpret(main_function)
        if result != InterpretResult.OK:
            self.had_runtime_error = True

    def run_file_with_dependencies(self, entry_path: str, output_path: str = None, test_click_coords: tuple = None):
        """
        Resolves dependencies, then compiles and runs an Orion script from a file.
        This is the main entry point for running applications.
        """
        try:
            # Step 1: Resolve and load all modules
            ordered_files = self._resolve_dependencies(entry_path)
            for path in ordered_files:
                print(f"INFO: Loading module '{os.path.basename(path)}'...")
                with open(path, 'r', encoding='utf-8') as f:
                    source = f.read()
                compiled_function = compile_source(source)
                if compiled_function is None:
                    self.had_error = True
                    print(f"ERROR: Compilation failed for '{path}'.")
                    break
                result, _ = self.vm.interpret(compiled_function)
                if result != InterpretResult.OK:
                    self.had_runtime_error = True
                    print(f"ERROR: Runtime error while loading module '{path}'.")
                    break
            if self.had_error or self.had_runtime_error:
                return

            # Step 2: Get the main App instance
            app_instance = self.vm.globals.get("App")
            if not isinstance(app_instance, OrionComponentInstance):
                print("INFO: Script finished. No 'App' component instance found to display.")
                return

            # Step 3: Run in GUI, Headless, or Test mode
            if test_click_coords:
                output_file = output_path if output_path else "test_output.png"
                self._run_test_mode(app_instance, test_click_coords, output_file)
            elif output_path:
                self._run_headless_mode(app_instance, output_path)
            else:
                self._run_gui(app_instance)

        except Exception as e:
            print(f"FATAL: An error occurred: {e}")
            import traceback
            traceback.print_exc()
            self.had_error = True


    def _build_scene_graph(self, component_instance, offset_x, offset_y):
        # ... [omitted for brevity, same as before]
        base_abs_x = offset_x + component_instance.fields.get('x', 0)
        base_abs_y = offset_y + component_instance.fields.get('y', 0)
        node = {"instance": component_instance, "x": base_abs_x, "y": base_abs_y, "width": component_instance.fields.get('width', 0), "height": component_instance.fields.get('height', 0), "children": []}
        children_to_process = []
        is_layout_component = component_instance.definition.name in ("Column", "Row")
        if is_layout_component:
            children_field = component_instance.fields.get("children")
            if isinstance(children_field, OrionList):
                children_to_process = children_field.elements
        elif "render" in component_instance.definition.methods:
            commands_before = len(self.vm.draw_commands)
            rendered_output = self.vm.call_method_on_instance(component_instance, "render")
            for i in range(commands_before, len(self.vm.draw_commands)):
                command = self.vm.draw_commands[i]
                command['x'] += base_abs_x
                command['y'] += base_abs_y
            if isinstance(rendered_output, OrionList):
                children_to_process = rendered_output.elements
        else:
            return node
        if is_layout_component and component_instance.definition.name == "Column":
            spacing = component_instance.fields.get('spacing', 0)
            padding = component_instance.fields.get('padding', 0)
            align = component_instance.fields.get('align', 'start')
            parent_width = component_instance.fields.get('width', 0)
            current_y_offset = padding
            for i, child_instance in enumerate(children_to_process):
                if isinstance(child_instance, OrionComponentInstance):
                    if i > 0: current_y_offset += spacing
                    child_width = child_instance.fields.get('width', 0)
                    if child_width == 0 and child_instance.definition.name == 'Label': child_width = len(child_instance.fields.get('text', '')) * (child_instance.fields.get('fontSize', 16) * 0.6)
                    x_offset = padding
                    if align == 'center': x_offset = (parent_width - child_width) / 2
                    elif align == 'end': x_offset = parent_width - child_width - padding
                    child_node = self._build_scene_graph(child_instance, base_abs_x + x_offset, base_abs_y + current_y_offset)
                    if child_node:
                        node["children"].append(child_node)
                        child_height = child_node["height"]
                        if child_height == 0 and child_node["instance"].definition.name == 'Label': child_height = child_node["instance"].fields.get('fontSize', 16) * 1.5
                        current_y_offset += child_height
        elif is_layout_component and component_instance.definition.name == "Row":
            spacing = component_instance.fields.get('spacing', 0)
            padding = component_instance.fields.get('padding', 0)
            align = component_instance.fields.get('align', 'start')
            parent_height = component_instance.fields.get('height', 0)
            current_x_offset = padding
            for i, child_instance in enumerate(children_to_process):
                if isinstance(child_instance, OrionComponentInstance):
                    if i > 0: current_x_offset += spacing
                    child_height = child_instance.fields.get('height', 0)
                    if child_height == 0 and child_instance.definition.name == 'Label': child_height = child_instance.fields.get('fontSize', 16) * 1.5
                    y_offset = padding
                    if align == 'center': y_offset = (parent_height - child_height) / 2
                    elif align == 'end': y_offset = parent_height - child_height - padding
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
            for child_instance in children_to_process:
                if isinstance(child_instance, OrionComponentInstance):
                    child_node = self._build_scene_graph(child_instance, base_abs_x, base_abs_y)
                    if child_node: node["children"].append(child_node)
        return node


    def _run_gui(self, app_instance: OrionComponentInstance):
        # ... [omitted for brevity, same as before]
        print("INFO: Starting Orion GUI application...")
        sdl2.ext.init()
        WIDTH, HEIGHT = 800, 600
        window = sdl2.ext.Window("Orion Application", size=(WIDTH, HEIGHT))
        window.show()
        sdl2.SDL_StartTextInput()
        window_surface = window.get_surface()
        renderer = GraphicalRenderer(WIDTH, HEIGHT)
        dispatcher = EventDispatcher()
        running = True
        event = sdl2.SDL_Event()
        while running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT: running = False
                if self.scene_graph: dispatcher.dispatch(event, self.vm, self.scene_graph)
            if app_instance.dirty:
                print("DEBUG: Dirty flag was set, re-rendering.")
                self.vm.draw_commands = []
                self.scene_graph = self._build_scene_graph(app_instance, 0, 0)
                renderer.process_commands(self.vm.draw_commands)
                skia_pixels = renderer.surface.toarray().tobytes()
                ctypes.memmove(window_surface.pixels, skia_pixels, len(skia_pixels))
                window.refresh()
                app_instance.dirty = False
            sdl2.SDL_Delay(10)
        sdl2.ext.quit()

    def _run_headless_mode(self, app_instance: OrionComponentInstance, output_path: str):
        # ... [omitted for brevity, same as before]
        print(f"INFO: Running in headless mode. Output will be saved to {output_path}")
        width = app_instance.fields.get('width', 800)
        height = app_instance.fields.get('height', 600)
        renderer = GraphicalRenderer(width, height)
        self.vm.draw_commands = []
        self.scene_graph = self._build_scene_graph(app_instance, 0, 0)
        renderer.process_commands(self.vm.draw_commands)
        renderer.save_to_file(output_path)

    def _run_test_mode(self, app_instance: OrionComponentInstance, click_coords: tuple, output_path: str):
        # ... [omitted for brevity, same as before]
        print(f"INFO: Running in automated test mode. Output will be saved to {output_path}")
        width = app_instance.fields.get('width', 800)
        height = app_instance.fields.get('height', 600)
        renderer = GraphicalRenderer(width, height)
        dispatcher = EventDispatcher()
        self.vm.draw_commands = []
        self.scene_graph = self._build_scene_graph(app_instance, 0, 0)
        print(f"INFO: Simulating click at {click_coords}")
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        event.button.button = sdl2.SDL_BUTTON_LEFT
        event.button.x = click_coords[0]
        event.button.y = click_coords[1]
        dispatcher.dispatch(event, self.vm, self.scene_graph)
        app_instance.dirty = True
        if app_instance.dirty:
            self.vm.draw_commands = []
            self.scene_graph = self._build_scene_graph(app_instance, 0, 0)
            renderer.process_commands(self.vm.draw_commands)
            app_instance.dirty = False
        renderer.save_to_file(output_path)

    def run_prompt(self):
        # ... [omitted for brevity, same as before]
        print("Orion REPL (Ctrl+C to exit)")
        print("NOTE: 'use' statements for .orion files are not supported in REPL.")
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
    # This __main__ block assumes the script is run as a module from the project root
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        output_path = None
        test_click_coords = None

        # Basic command line parsing
        try:
            # Note: sys.argv for a module is ['orion_compiler/orion.py', arg1, arg2, ...]
            # So we need to adjust indexing if run with -m
            args = sys.argv[1:]

            script_path = args[0]

            if '--output' in args:
                output_path = args[args.index('--output') + 1]
            if '--test-click' in args:
                coords_str = args[args.index('--test-click') + 1]
                x_str, y_str = coords_str.split(',')
                test_click_coords = (int(x_str), int(y_str))
        except (ValueError, IndexError):
            print("Usage: python -m orion_compiler.orion <script> [--output path] [--test-click x,y]")
            sys.exit(64)

        orion.run_file_with_dependencies(
            script_path,
            output_path=output_path,
            test_click_coords=test_click_coords
        )
        if orion.had_error: sys.exit(65)
        if orion.had_runtime_error: sys.exit(70)
    else:
        orion.run_prompt()
