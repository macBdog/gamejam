from gamejam.widget import Widget
from gamejam.texture import SpriteTexture
from gamejam.cursor import Cursor
from gamejam.font import Font

class Gui:
    """Manager style functionality for a collection of widget classes.
    Also convenience functions for window handling."""
    def __init__(self, name: str):
        self.name = name
        self.active_draw = False
        self.active_input = False
        self.parent = None
        self.widgets = []
        self.children = {}


    def is_active(self):
        return self.active_draw, self.active_input


    def set_active(self, do_draw: bool, do_input: bool):
        self.active_draw = do_draw
        self.active_input = do_input


    def add_child(self, child):
        if child.name not in self.children and child.parent == None:
            child.parent = self
            self.children[child.name] = child
        else:
            print(f"Error when adding child gui {child.name} to {self.name}! Gui {child.name} already has a parent and it's name is {child.parent.name}.")


    def add_create_widget(self, sprite: SpriteTexture, font:Font=None) -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param sprite: The underlying sprite OpenGL object that is updated when the widget is drawn."""

        widget = Widget(sprite, font)
        self.widgets.append(widget)
        return widget


    def add_widget(self, widget: Widget) -> Widget:
        self.widgets.append(widget)
        return widget


    def delete_widget(self, widget: Widget):
        self.widgets.remove(widget)


    def touch(self, mouse: Cursor):
        for _, name in enumerate(self.children):
            self.children[name].touch(mouse)

        if self.active_input:
            for i in self.widgets:
                i.touch(mouse)


    def draw(self, dt: float):
        for _, name in enumerate(self.children):
            self.children[name].draw(dt)

        if self.active_draw:
            for i in self.widgets:
                i.draw(dt)
