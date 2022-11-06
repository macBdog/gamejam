from gamejam.widget import Widget
from gamejam.texture import SpriteTexture
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.settings import GameSettings
from gamejam.texture import SpriteTexture, Texture

from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1f,
    glUniform1iv,
    glUniform4fv
)

class Gui:
    """Manager style functionality for a collection of widget classes.
    Also convenience functions for window handling and display of position hierarchy."""
    NUM_DEBUG_WIDGETS = 128

    def __init__(self, name: str, graphics: Graphics):
        self.name = name
        self.active_draw = False
        self.active_input = False
        self.parent = None
        self.widgets = []
        self.children = {}
        self.display_ratio = graphics.display_ratio
        self.debug_dirty = False
        self.debug_size_offset = [0.0] * Gui.NUM_DEBUG_WIDGETS * 4
        self.debug_align = [0] * Gui.NUM_DEBUG_WIDGETS

        shader_substitutes = {
            "NUM_DEBUG_WIDGETS": str(Gui.NUM_DEBUG_WIDGETS)
        }
        debug_shader = Graphics.process_shader_source(graphics.builtin_shader(Shader.DEBUG, ShaderType.PIXEL), shader_substitutes)        
        self.shader = Graphics.create_program(graphics.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), debug_shader)
        
        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.debug_size_offset_id = glGetUniformLocation(self.shader, "WidgetSizeOffset")
        self.debug_align_id = glGetUniformLocation(self.shader, "WidgetAlign")


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

            if GameSettings.DEV_MODE:
                self.draw_debug(dt)


    def draw_debug(self, dt: float):
        def debug_widget_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform4fv(self.debug_size_offset_id, Gui.NUM_DEBUG_WIDGETS, self.debug_size_offset)
            glUniform1iv(self.debug_align_id, Gui.NUM_DEBUG_WIDGETS, self.debug_align)

        self.debug_dirty = True # remove, should be sent up the hierachy by widget mutators
        if self.debug_dirty:
            debug_widget_index = 0
            for i in self.widgets:
                so_index = debug_widget_index * 4
                self.debug_size_offset[so_index + 0] = i.size[0]
                self.debug_size_offset[so_index + 1] = i.size[1]
                self.debug_size_offset[so_index + 2] = i.offset[0]
                self.debug_size_offset[so_index + 3] = i.offset[1]
                self.debug_align[debug_widget_index] = (i.align_x.value * 10) + i.align_y.value
                debug_widget_index += 1
                if debug_widget_index >= Gui.NUM_DEBUG_WIDGETS:
                    break

            for _ in range(Gui.NUM_DEBUG_WIDGETS - debug_widget_index):
                self.debug_align[debug_widget_index] = 0
                debug_widget_index += 1

            self.sprite.draw(debug_widget_uniforms)
            self.debug_dirty = False

