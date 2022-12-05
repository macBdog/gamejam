from enum import Enum

from gamejam.gui_widget import TouchState
from gamejam.texture import SpriteTexture
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.input import Input, InputActionKey, InputActionModifier
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.settings import GameSettings
from gamejam.texture import SpriteTexture, Texture
from gamejam.widget import Widget

from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1i,
    glUniform1f,
    glUniform1iv,
    glUniform4fv
)

class GuiEditMode(Enum):
    NONE = 0,
    OFFSET = 1,
    SIZE = 2,
    TEXT_OFFSET = 3,
    TEXT_SIZE = 4,

class Gui(Widget):
    """Manager style functionality for a collection of widget classes.
    Also convenience functions for window handling and display of position hierarchy."""
    NUM_DEBUG_WIDGETS = 128

    def __init__(self, name: str, graphics: Graphics, debug_font: Font):
        super().__init__()
        self.name = name
        self.active_draw = False
        self.active_input = False
        self.display_ratio = graphics.display_ratio
        self.debug_font = debug_font
        self.debug_edit_mode = GuiEditMode.NONE
        self.debug_edit_start_pos = [0.0, 0.0]
        self.debug_dirty = False
        self.debug_hover = None
        self.debug_selected = None
        self.debug_size_pos = [0.0] * Gui.NUM_DEBUG_WIDGETS * 4
        self.debug_align = [0] * Gui.NUM_DEBUG_WIDGETS
        self.cursor = None

        shader_substitutes = {
            "NUM_DEBUG_WIDGETS": str(Gui.NUM_DEBUG_WIDGETS)
        }
        debug_shader = Graphics.process_shader_source(graphics.builtin_shader(Shader.DEBUG, ShaderType.PIXEL), shader_substitutes)        
        self.shader = Graphics.create_program(graphics.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), debug_shader)
        
        self.texture = Texture("")
        self.debug_sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.debug_hover_id = glGetUniformLocation(self.shader, "WidgetHoverId")
        self.debug_selected_id = glGetUniformLocation(self.shader, "WidgetSelectedId")
        self.debug_size_pos_id = glGetUniformLocation(self.shader, "WidgetSizePosition")
        self.debug_align_id = glGetUniformLocation(self.shader, "WidgetAlign")

        self.set_size([2.0, 2.0])


    @staticmethod
    def toggle_gui_mode(**kwargs):
        gui = kwargs["gui"]
        GameSettings.GUI_MODE = not GameSettings.GUI_MODE
        if GameSettings.GUI_MODE == False:
            gui.dump()
    

    @staticmethod
    def add_new_widget(**kwargs):
        gui = kwargs["gui"]
        if GameSettings.GUI_MODE:
            gui.add_create_widget(None)


    @staticmethod
    def remove_widget(**kwargs):
        gui = kwargs["gui"]
        if GameSettings.GUI_MODE:
            if gui.debug_selected is not None:
                gui.debug_selected = None
                #TODO self.remove_widget(self.debug_selected)


    @staticmethod
    def toggle_edit_mode(**kwargs):
        gui = kwargs["gui"]
        mode = kwargs["mode"]
        if GameSettings.GUI_MODE:
            if gui.debug_edit_mode is GuiEditMode.NONE:
                gui.debug_edit_mode = mode
            else:
                gui.debug_edit_mode = GuiEditMode.NONE
                gui.debug_edit_start_pos = None


    @staticmethod
    def init_debug_bindings(gui, input: Input):
        """Bindings for the gui editor"""
        
        # Ctrl+N for add widget
        input.add_key_mapping(78, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, Gui.add_new_widget, {"gui": gui})

        # Ctrl+X to remove selected widget
        input.add_key_mapping(88, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, Gui.remove_widget, {"gui": gui})

        # O and S for modifying widget offset and size
        input.add_key_mapping(79, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, Gui.toggle_edit_mode, {"gui": gui, "mode": GuiEditMode.OFFSET})
        input.add_key_mapping(83, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, Gui.toggle_edit_mode, {"gui": gui, "mode": GuiEditMode.SIZE})

        # F and T for text offset and size
        input.add_key_mapping(70, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, Gui.toggle_edit_mode, {"gui": gui, "mode": GuiEditMode.TEXT_SIZE})
        input.add_key_mapping(84, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, Gui.toggle_edit_mode, {"gui": gui, "mode": GuiEditMode.TEXT_OFFSET})

        # Ctrl-G to enable gui editing mode, exiting dumps current widgets
        input.add_key_mapping(71, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, Gui.toggle_gui_mode, {"gui": gui})


    def is_active(self):
        return self.active_draw, self.active_input


    def set_active(self, do_draw: bool, do_input: bool):
        self.active_draw = do_draw
        self.active_input = do_input


    def add_create_widget(self, sprite: SpriteTexture, name:str="", font:Font=None) -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param sprite: The underlying sprite OpenGL object that is updated when the widget is drawn."""
        widget = Widget(name=name, font=font)
        widget.set_sprite(sprite)
        self.add_child(widget)
        return widget


    def delete_widget(self, widget: Widget):
        if widget in self._children:
            self._children.remove(widget)


    def touch(self, mouse: Cursor):
        if self.cursor is None:
            self.cursor = mouse

        if self.active_input:
            if GameSettings.GUI_MODE:
                self.touch_debug(mouse)
            else:
                for child in self._children:
                    child.touch(mouse)


    def touch_debug(self, mouse: Cursor):
        if self.debug_edit_mode is not GuiEditMode.NONE and self.debug_selected is not None:
            if self.debug_edit_start_pos is None:
                self.debug_edit_start_pos = self.cursor.pos
            else:
                edit_diff = [
                    mouse.pos[0] - self.debug_edit_start_pos[0],
                    mouse.pos[1] - self.debug_edit_start_pos[1],
                ]
                if self.debug_edit_mode is GuiEditMode.OFFSET:
                    self.debug_selected.set_offset(edit_diff)
                elif self.debug_edit_mode is GuiEditMode.SIZE:
                        self.debug_selected.set_size(edit_diff)
            
        touched_widget = False
        self.debug_hover = None
        for i, child in enumerate(self._children):
            touch_state = child.touch(mouse)
            if touch_state == TouchState.Hover:
                self.debug_hover = i

            if self.debug_selected is None:
                if touch_state == TouchState.Touched:
                    self.debug_selected = i
                    break
            else:
                if touch_state == TouchState.Touched:
                    touched_widget = True
        
        # Deselect any selected widget
        if mouse.buttons[0] and touched_widget == False:
            self.debug_selected = None
            self.debug_edit_mode = GuiEditMode.NONE


    def draw(self, dt: float):
        if self.active_draw:
            super().draw(dt)

            if self.active_draw:
                if GameSettings.GUI_MODE:
                    self.draw_debug(dt)


    def draw_debug(self, dt: float):
        self.debug_font.draw(self.name, 16, self._draw_pos, [1.0] * 4)
        
        hover_widget_id = -1
        selected_widget_id = -1
        def debug_widget_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1i(self.debug_selected_id, selected_widget_id)
            glUniform1i(self.debug_hover_id, hover_widget_id)
            glUniform4fv(self.debug_size_pos_id, Gui.NUM_DEBUG_WIDGETS, self.debug_size_pos)
            glUniform1iv(self.debug_align_id, Gui.NUM_DEBUG_WIDGETS, self.debug_align)

        child_widgets = self._children

        self.debug_dirty = True # remove, should be sent up the hierachy by widget mutators
        if self.debug_dirty:
            debug_widget_index = 0
            for i, widget in enumerate(child_widgets):
                if widget == self.debug_selected:
                    selected_widget_id = i
                if widget == self.debug_hover:
                    hover_widget_id = i
                sp_index = debug_widget_index * 4
                self.debug_size_pos[sp_index + 0] = widget._size[0]
                self.debug_size_pos[sp_index + 1] = widget._size[1]
                self.debug_size_pos[sp_index + 2] = widget._draw_pos[0]
                self.debug_size_pos[sp_index + 3] = widget._draw_pos[1]
                self.debug_align[debug_widget_index] = (widget._align.x.value * 10) + widget._align.y.value
                debug_widget_index += 1
                if debug_widget_index >= Gui.NUM_DEBUG_WIDGETS:
                    break

            for _ in range(Gui.NUM_DEBUG_WIDGETS - debug_widget_index):
                self.debug_align[debug_widget_index] = 0
                debug_widget_index += 1

            self.debug_sprite.draw(debug_widget_uniforms)
            self.debug_dirty = False

