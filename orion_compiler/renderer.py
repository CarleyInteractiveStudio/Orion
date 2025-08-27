import skia

class GraphicalRenderer:
    """
    Renders draw commands to an image file using the Skia graphics library.
    """
    def __init__(self, width: int, height: int):
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive integers.")
        self.width = width
        self.height = height
        self.surface = skia.Surface(width, height)
        self.canvas = self.surface.getCanvas()
        # Set a default background color
        self.canvas.clear(skia.ColorWHITE)

    def save(self):
        self.canvas.save()

    def clipRect(self, rect):
        self.canvas.clipRect(rect)

    def restore(self):
        self.canvas.restore()

    def process_commands(self, commands: list[dict]):
        """Processes a list of draw command dictionaries."""
        for command in commands:
            cmd_type = command.get("command")
            if cmd_type == "box":
                self._draw_box(command)
            elif cmd_type == "text":
                self._draw_text(command)

    def _draw_box(self, command: dict):
        """Draws a filled rectangle on the canvas."""
        paint = skia.Paint(
            Color=self._parse_color(command.get("color", "#000000")),
            Style=skia.Paint.kFill_Style
        )
        rect = skia.Rect.MakeXYWH(
            command.get("x", 0),
            command.get("y", 0),
            command.get("width", 10),
            command.get("height", 10)
        )
        self.canvas.drawRect(rect, paint)

    def _draw_text(self, command: dict):
        """Draws text on the canvas."""
        paint = skia.Paint(
            Color=self._parse_color(command.get("color", "#000000"))
        )
        font = skia.Font(
            None, # Default typeface
            command.get("fontSize", 12)
        )
        self.canvas.drawString(
            command.get("text", ""),
            command.get("x", 0),
            command.get("y", 0),
            font,
            paint
        )

    def _parse_color(self, hex_color: str) -> skia.Color:
        """Parses a hex color string (e.g., #RRGGBB) into a skia.Color."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return skia.Color(r, g, b)
        # Return black for invalid formats
        return skia.ColorBLACK

    def save_to_file(self, filepath: str = "output.png"):
        """Saves the canvas to a PNG image file."""
        image = self.surface.makeImageSnapshot()
        image.save(filepath, skia.kPNG)
        print(f"INFO: Image saved to {filepath}")
