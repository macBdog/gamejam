import os
from pathlib import Path

from gamejam.texture import SpriteTexture
from gamejam.coord import Coord2d
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.settings import GameSettings
from gamejam.texture import SpriteTexture
from gamejam.widget import Widget
from gamejam.gui_widget import GuiWidget


class Gui(Widget):
    """Manager style functionality for a collection of widget classes.
    Also convenience functions for window handling and display of position hierarchy."""

    def __init__(self, name: str, graphics: Graphics, debug_font: Font, restore_from_file: bool = True):
        super().__init__()
        self.name = name
        self.active_draw = False
        self.active_input = False
        self.display_ratio = graphics.display_ratio
        self.debug_font = debug_font
        self.debug_edit_start_pos = Coord2d()
        self.debug_dirty = False
        self.debug_hover = None
        self.cursor = None

        if restore_from_file:
            gui_path = Path(os.getcwd()) / "gui" / f"{name}.yml"
            if gui_path.exists():
                with open(gui_path, 'r') as stream:
                    GuiWidget.restore(self, stream)
      
        self.set_size(Coord2d(2.0, 2.0))


    def is_active(self):
        return self.active_draw, self.active_input


    def set_active(self, do_draw: bool, do_input: bool):
        self.active_draw = do_draw
        self.active_input = do_input


    def add_create_widget(self, sprite:SpriteTexture=None, font:Font=None, name:str="") -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param sprite: The underlying sprite OpenGL object that is updated when the widget is drawn."""
        widget = GuiWidget(name=name, font=font)
        if sprite is not None:
            widget.set_sprite(sprite)
            widget.set_size(sprite.size)
            widget.set_offset(sprite.pos)
        self.add_child(widget)
        return widget


    def add_create_text_widget(self, font:Font, text:str, size:int, offset:Coord2d=None, name:str="") -> GuiWidget:
        widget = GuiWidget(name=name, font=font)
        widget.set_size(Coord2d(0.25, font.get_line_display_height(size)))
        if offset is not None:
            widget.set_offset(offset)
        widget.set_text(text, size, Coord2d())
        self.add_child(widget)
        return widget


    def delete_widget(self, widget: Widget):
        if widget in self._children:
            self._children.remove(widget)


    def touch(self, mouse: Cursor):
        if self.cursor is None:
            self.cursor = mouse

        if self.active_input:
            for child in self._children:
                if hasattr(child, "touch"):
                    child.touch(mouse)


    def draw(self, dt: float):
        if self.active_draw:
            super().draw(dt)

