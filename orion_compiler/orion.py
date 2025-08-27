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
    def __init__(self):
        self.vm = VM()
        self.scene_graph = None
        self.had_error = False
        self.had_runtime_error = False

    def _find_module_path(self, module_name: str, base_path: str) -> str | None:
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

    def run(self, source: str):
        main_function = compile_source(source)
        if main_function is None:
            self.had_error = True
            return
        result, _ = self.vm.interpret(main_function)
        if result != InterpretResult.OK:
            self.had_runtime_error = True

    def run_file_with_dependencies(self, entry_path: str, output_path: str = None, test_events: list = None):
        try:
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

            app_instance = self.vm.globals.get("App")
            if not isinstance(app_instance, OrionComponentInstance):
                print("INFO: Script finished. No 'App' component instance found to display.")
                return

            if test_events:
                output_prefix = output_path if output_path else "test_output"
                self._run_test_mode(app_instance, test_events, output_prefix)
            elif output_path:
                self._run_headless_mode(app_instance, output_path)
            else:
                self._run_gui(app_instance)

        except Exception as e:
            print(f"FATAL: An error occurred: {e}")
            import traceback
            traceback.print_exc()
            self.had_error = True

    def _build_scene_graph(self, component_instance, offset_x, offset_y, renderer):
        base_abs_x = offset_x + component_instance.fields.get('x', 0)
        base_abs_y = offset_y + component_instance.fields.get('y', 0)
        width = component_instance.fields.get('width', 0)
        height = component_instance.fields.get('height', 0)
        node = {"instance": component_instance, "x": base_abs_x, "y": base_abs_y, "width": width, "height": height, "children": []}

        is_scroll_view = component_instance.definition.name == "ScrollView"
        if is_scroll_view:
            renderer.save()
            clip_rect = skia.Rect.MakeXYWH(base_abs_x, base_abs_y, width, height)
            renderer.clipRect(clip_rect)

        children_to_process = []
        is_layout_component = component_instance.definition.name in ("Column", "Row")

        child_offset_y = base_abs_y
        if is_scroll_view:
            state = component_instance.fields.get("state", {})
            scroll_y = state.get("scroll_y", 0) if isinstance(state, dict) else 0
            child_offset_y -= scroll_y

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
            if is_scroll_view: renderer.restore()
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
                    child_node = self._build_scene_graph(child_instance, base_abs_x + x_offset, child_offset_y + current_y_offset, renderer)
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
                    child_node = self._build_scene_graph(child_instance, base_abs_x + current_x_offset, child_offset_y + y_offset, renderer)
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
                    child_node = self._build_scene_graph(child_instance, base_abs_x, child_offset_y, renderer)
                    if child_node: node["children"].append(child_node)

        if is_scroll_view:
            content_height = 0
            spacing = component_instance.fields.get('spacing', 0)
            padding = component_instance.fields.get('padding', 0) * 2
            for i, child_node in enumerate(node["children"]):
                if i > 0: content_height += spacing
                content_height += child_node["height"]
            component_instance.fields["content_height"] = content_height + padding
            renderer.restore()

        return node

    def _run_gui(self, app_instance: OrionComponentInstance):
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
            self.vm.draw_commands = []
            self.scene_graph = self._build_scene_graph(app_instance, 0, 0, renderer)
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT: running = False
                dispatcher.dispatch(event, self.vm, self.scene_graph)
            if app_instance.dirty:
                renderer.process_commands(self.vm.draw_commands)
                skia_pixels = renderer.surface.toarray().tobytes()
                ctypes.memmove(window_surface.pixels, skia_pixels, len(skia_pixels))
                window.refresh()
                app_instance.dirty = False
            sdl2.SDL_Delay(10)
        sdl2.ext.quit()

    def _run_headless_mode(self, app_instance: OrionComponentInstance, output_path: str):
        print(f"INFO: Running in headless mode. Output will be saved to {output_path}")
        width = app_instance.fields.get('width', 800)
        height = app_instance.fields.get('height', 600)
        renderer = GraphicalRenderer(width, height)
        self.vm.draw_commands = []
        self.scene_graph = self._build_scene_graph(app_instance, 0, 0, renderer)
        renderer.process_commands(self.vm.draw_commands)
        renderer.save_to_file(output_path)

    def _run_test_mode(self, app_instance: OrionComponentInstance, events: list, output_path_prefix: str):
        print(f"INFO: Running in automated test mode. Output prefix: {output_path_prefix}")
        width = app_instance.fields.get('width', 800)
        height = app_instance.fields.get('height', 600)
        renderer = GraphicalRenderer(width, height)
        dispatcher = EventDispatcher()
        self.vm.draw_commands = []
        self.scene_graph = self._build_scene_graph(app_instance, 0, 0, renderer)
        renderer.process_commands(self.vm.draw_commands)
        renderer.save_to_file(f"{output_path_prefix}_0_initial.png")
        for i, event_def in enumerate(events):
            event = sdl2.SDL_Event()
            if event_def["type"] == "move":
                event.type = sdl2.SDL_MOUSEMOTION
                event.motion.x = event_def["x"]
                event.motion.y = event_def["y"]
                print(f"INFO: Simulating mouse move to ({event_def['x']}, {event_def['y']})")
            elif event_def["type"] == "click":
                event.type = sdl2.SDL_MOUSEBUTTONDOWN
                event.button.button = sdl2.SDL_BUTTON_LEFT
                event.button.x = event_def["x"]
                event.button.y = event_def["y"]
                print(f"INFO: Simulating click at ({event_def['x']}, {event_def['y']})")
            elif event_def["type"] == "wheel":
                event.type = sdl2.SDL_MOUSEWHEEL
                event.wheel.x = event_def["x"]
                event.wheel.y = event_def["y"]
                print(f"INFO: Simulating mouse wheel scroll ({event_def['x']}, {event_def['y']})")
            dispatcher.dispatch(event, self.vm, self.scene_graph)
            app_instance.dirty = True
            if app_instance.dirty:
                self.vm.draw_commands = []
                self.scene_graph = self._build_scene_graph(app_instance, 0, 0, renderer)
                renderer.process_commands(self.vm.draw_commands)
                app_instance.dirty = False
            renderer.save_to_file(f"{output_path_prefix}_{i+1}_{event_def['type']}.png")

    def run_prompt(self):
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
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        script_path = args[0]
        output_path = None
        test_events = None
        try:
            if '--output' in args:
                output_path = args[args.index('--output') + 1]
            if '--test-events' in args:
                events_str = args[args.index('--test-events') + 1]
                test_events = []
                for event_part in events_str.split(';'):
                    type_part, coords_part = event_part.split(':')
                    x_str, y_str = coords_part.split(',')
                    test_events.append({"type": type_part, "x": int(x_str), "y": int(y_str)})
        except (ValueError, IndexError):
            print("Usage: python -m orion_compiler.orion <script> [--output prefix] [--test-events 'type:x,y;...']")
            sys.exit(64)
        orion.run_file_with_dependencies(
            script_path,
            output_path=output_path,
            test_events=test_events
        )
        if orion.had_error: sys.exit(65)
        if orion.had_runtime_error: sys.exit(70)
    else:
        orion.run_prompt()
