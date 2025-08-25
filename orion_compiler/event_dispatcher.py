import sdl2
from objects import OrionComponentInstance
from vm import VM

class EventDispatcher:
    """
    Processes SDL2 events and dispatches them to the appropriate components.
    """
    def dispatch(self, event: sdl2.SDL_Event, vm: VM, component_tree: list):
        """
        Dispatches a single event to the component tree.
        For now, the tree is just a list of top-level components.
        """
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            self._handle_mouse_down(event, vm, component_tree)

    def _handle_mouse_down(self, event: sdl2.SDL_Event, vm: VM, component_tree: list):
        """
        Handles a mouse down event by performing hit testing and calling
        the 'onClick' method on the hit component.
        """
        mx, my = event.button.x, event.button.y

        # Iterate in reverse to hit the top-most component first
        for component in reversed(component_tree):
            if self._hit_test(component, mx, my):
                # If the component has an onClick method, call it.
                if "onClick" in component.definition.methods:
                    vm.call_method_on_instance(component, "onClick")
                break # Stop after the first hit

    def _hit_test(self, component: OrionComponentInstance, mx: int, my: int) -> bool:
        """
        Checks if a point (mx, my) is within the bounds of a component.
        A component's bounds are defined by its x, y, width, and height properties.
        """
        # Get bounds from the component's fields, with defaults
        x = component.fields.get("x", 0)
        y = component.fields.get("y", 0)
        width = component.fields.get("width", 0)
        height = component.fields.get("height", 0)

        # Basic rectangular hit test
        return (x <= mx < x + width) and (y <= my < y + height)
