import sdl2
from objects import OrionComponentInstance
from vm import VM

class EventDispatcher:
    """
    Processes SDL2 events and dispatches them to the appropriate components
    by traversing a pre-built scene graph.
    """
    def dispatch(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """
        Dispatches a single event to the component tree represented by the scene graph.
        """
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            self._handle_mouse_down(event, vm, scene_graph)

    def _handle_mouse_down(self, event: sdl2.SDL_Event, vm: VM, scene_graph: dict):
        """
        Handles a mouse down event by performing a recursive hit test on the scene graph
        and calling the 'onClick' method on the hit component.
        """
        mx, my = event.button.x, event.button.y

        hit_component = self._find_hit_component_recursive(scene_graph, mx, my)

        if hit_component:
            print(f"INFO: Click hit on component {hit_component.definition.name} at ({mx}, {my})")
            if "onClick" in hit_component.definition.methods:
                vm.call_method_on_instance(hit_component, "onClick")

    def _find_hit_component_recursive(self, node: dict, mx: int, my: int):
        """
        Recursively traverses the scene graph to find the top-most component
        at the given mouse coordinates.
        """
        # Search children first (in reverse for top-down order)
        for child_node in reversed(node["children"]):
            hit_component = self._find_hit_component_recursive(child_node, mx, my)
            if hit_component:
                return hit_component # Found a hit in a child, so we're done.

        # If no child was hit, check the current node itself.
        x = node["x"]
        y = node["y"]
        width = node["width"]
        height = node["height"]

        is_hit = (x <= mx < x + width) and (y <= my < y + height)

        if is_hit:
            return node["instance"]

        return None
