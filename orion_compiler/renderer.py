class TextRenderer:
    """
    A simple text-based renderer that draws shapes onto a character grid.
    """
    def __init__(self, width: int, height: int):
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive integers.")
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]

    def process_commands(self, commands: list[dict]):
        """Processes a list of draw command dictionaries."""
        for command in commands:
            cmd_type = command.get("command")
            if cmd_type == "box":
                self._draw_box(command)
            elif cmd_type == "text":
                self._draw_text(command)

    def _draw_box(self, command: dict):
        """Draws a box on the canvas."""
        x, y = command.get("x", 0), command.get("y", 0)
        width, height = command.get("width", 1), command.get("height", 1)

        # Draw corners
        self._set_char(x, y, '+')
        self._set_char(x + width - 1, y, '+')
        self._set_char(x, y + height - 1, '+')
        self._set_char(x + width - 1, y + height - 1, '+')

        # Draw horizontal lines
        for i in range(1, width - 1):
            self._set_char(x + i, y, '-')
            self._set_char(x + i, y + height - 1, '-')

        # Draw vertical lines
        for i in range(1, height - 1):
            self._set_char(x, y + i, '|')
            self._set_char(x + width - 1, y + i, '|')

    def _draw_text(self, command: dict):
        """Draws text on the canvas."""
        x, y = command.get("x", 0), command.get("y", 0)
        text = command.get("text", "")

        for i, char in enumerate(text):
            self._set_char(x + i, y, char)

    def _set_char(self, x: int, y: int, char: str):
        """Safely sets a character on the canvas, ignoring out-of-bounds writes."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.canvas[y][x] = char

    def render_to_console(self):
        """Prints the canvas to the console."""
        for row in self.canvas:
            print("".join(row))
