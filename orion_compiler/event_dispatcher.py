import sdl2
from . objects import OrionComponentInstance
from . vm import VM

class EventDispatcher:
    """
    Processes SDL2 events and dispatches them to the appropriate components
    by traversing a pre-built scene graph.
    """
    def __init__(self):
        self.focused_component = None
        self.hovered_component = None

    def dispatch(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """
        Dispatches a single event to the component tree represented by the scene graph.
        """
        if event.type == sdl2.SDL_MOUSEMOTION:
            self._handle_mouse_motion(event, vm, scene_graph)
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            self._handle_mouse_down(event, vm, scene_graph)
        elif event.type == sdl2.SDL_MOUSEWHEEL:
            self._handle_mouse_wheel(event, vm, scene_graph)
        elif self.focused_component:
            # If a component is focused, send it keyboard events.
            if event.type == sdl2.SDL_TEXTINPUT:
                if "onTextInput" in self.focused_component.definition.methods:
                    # Pass the input text as a prop
                    event_props = { "text": event.text.text }
                    vm.call_method_on_instance(self.focused_component, "onTextInput", event_props)

            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_BACKSPACE:
                    if "onKeyDown" in self.focused_component.definition.methods:
                        # Pass the key name as a prop
                        event_props = { "key": "backspace" }
                        vm.call_method_on_instance(self.focused_component, "onKeyDown", event_props)


    def _handle_mouse_down(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """
        Handles a mouse down event by performing a recursive hit test and calling
        the 'onClick' method on the hit component, also setting focus.
        """
        mx, my = event.button.x, event.button.y
        hit_component = self._find_hit_component_recursive(scene_graph, mx, my)

        # Set focus
        if self.focused_component and self.focused_component is not hit_component:
            # Tell the old component it lost focus
            if "onBlur" in self.focused_component.definition.methods:
                 vm.call_method_on_instance(self.focused_component, "onBlur")

        self.focused_component = hit_component

        if hit_component:
            print(f"INFO: Click hit on component {hit_component.definition.name} at ({mx}, {my})")
            if "onClick" in hit_component.definition.methods:
                vm.call_method_on_instance(hit_component, "onClick")

    def _handle_mouse_wheel(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """Handles a mouse wheel event, calling onMouseWheel on the hovered component."""
        if self.hovered_component:
            if "onMouseWheel" in self.hovered_component.definition.methods:
                # We flip the y value because SDL2's "natural" scrolling is often the reverse of what UIs expect.
                event_props = {"x": event.wheel.x, "y": -event.wheel.y}
                vm.call_method_on_instance(self.hovered_component, "onMouseWheel", event_props)

    def _handle_mouse_motion(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """
        Handles mouse motion to track entering and leaving components for hover effects.
        """
        mx, my = event.motion.x, event.motion.y
        newly_hovered = self._find_hit_component_recursive(scene_graph, mx, my)

        if self.hovered_component is not newly_hovered:
            # The hover state has changed.
            if self.hovered_component:
                if "onMouseLeave" in self.hovered_component.definition.methods:
                    vm.call_method_on_instance(self.hovered_component, "onMouseLeave")

            if newly_hovered:
                if "onMouseEnter" in newly_hovered.definition.methods:
                    vm.call_method_on_instance(newly_hovered, "onMouseEnter")

            self.hovered_component = newly_hovered

    def _find_hit_component_recursive(self, node: dict, mx: int, my: int):
        """
        Recursively traverses the scene graph to find the top-most component
        at the given mouse coordinates.
        """
        # Search children first (in reverse for top-down order)
        for child_node in reversed(node["children"]):
            hit_component = self._find_hit_component_recursive(child_node, mx, my)
            if hit_component:
                return hit_component

        # If no child was hit, check the current node itself.
        x = node["x"]
        y = node["y"]
        width = node["width"]
        height = node["height"]

        is_hit = (x <= mx < x + width) and (y <= my < y + height)

        if is_hit:
            return node["instance"]

        return None
