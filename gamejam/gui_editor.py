import os
from enum import Enum
from pathlib import Path

from gamejam.widget import Alignment, AlignX, AlignY
from gamejam.gui_widget import TouchState
from gamejam.texture import SpriteTexture
from gamejam.coord import Coord2d
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.input import Input, InputActionKey, InputActionModifier
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.texture import SpriteTexture, Texture
from gamejam.gui import Gui

from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1i,
    glUniform1f,
    glUniform1iv,
    glUniform4fv,
    glUniform2fv,
)


class GuiEditMode(Enum):
    NONE = 0,
    INSPECT = 1,
    OFFSET = 2,
    SIZE = 3,
    TEXT_OFFSET = 4,
    TEXT_SIZE = 5,
    PARENT = 6,
    ALIGN = 7,
    ALIGN_TO = 8,


class GuiEditor():
    """Editor for a GUI to show properties of child widgets and add remove."""
    NUM_DEBUG_WIDGETS = 128

    def __init__(self, main_gui: Gui, graphics: Graphics, input: Input, font: Font):
        super().__init__()
        self.main_gui = main_gui
        self.mode = GuiEditMode.NONE
        self.display_ratio = graphics.display_ratio
        self.font = font
        self.edit_start_pos = Coord2d()
        self.debug_dirty = False
        self.gui_to_edit = None
        self.widget_to_edit = None
        self.widget_to_hover = None
        self.widget_to_set_parent = None
        self.align_hover = -1
        self.debug_size_pos = [0.0] * GuiEditor.NUM_DEBUG_WIDGETS * 4
        self.debug_parent_pos = [0.0] * GuiEditor.NUM_DEBUG_WIDGETS * 2
        self.debug_align = [0] * GuiEditor.NUM_DEBUG_WIDGETS

        shader_substitutes = {
            "NUM_DEBUG_WIDGETS": str(GuiEditor.NUM_DEBUG_WIDGETS)
        }
        debug_shader = Graphics.process_shader_source(graphics.builtin_shader(Shader.DEBUG, ShaderType.PIXEL), shader_substitutes)        
        self.shader = Graphics.create_program(graphics.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), debug_shader)
        
        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 0.5], Coord2d(), Coord2d(2.0, 2.0), self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.debug_hover_id = glGetUniformLocation(self.shader, "WidgetHoverId")
        self.debug_align_hover_id = glGetUniformLocation(self.shader, "AlignHoverId")
        self.debug_selected_id = glGetUniformLocation(self.shader, "WidgetSelectedId")
        self.debug_size_pos_id = glGetUniformLocation(self.shader, "WidgetSizePosition")
        self.debug_parent_pos_id = glGetUniformLocation(self.shader, "WidgetParentPosition")
        self.debug_align_id = glGetUniformLocation(self.shader, "WidgetAlign")

        self._init_debug_bindings(input)


    def _init_debug_bindings(self, input: Input):
        # Ctrl+N for add widget
        input.add_key_mapping(78, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.add_new_widget, {"editor": self})

        # Ctrl+X to remove selected widget
        input.add_key_mapping(88, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.remove_widget, {"editor": self})

        # O and S for modifying widget offset and size
        input.add_key_mapping(79, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.OFFSET})
        input.add_key_mapping(83, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.SIZE})

        # F and T for text offset and size
        input.add_key_mapping(70, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.TEXT_SIZE})
        input.add_key_mapping(84, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.TEXT_OFFSET})

        # P, A and Ctrl-A for alignment
        input.add_key_mapping(80, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.PARENT})
        input.add_key_mapping(64, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.ALIGN})
        input.add_key_mapping(64, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.toggle_edit_mode, {"editor": self, "mode": GuiEditMode.ALIGN})

        # Ctrl-G to enable gui editing mode
        input.add_key_mapping(71, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.toggle_gui_mode, {"editor": self})

        # Ctrl-S to serialize gui to yaml file
        input.add_key_mapping(83, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.to_file, {"editor": self})

        # Direction keys to move around the widget hierachy
        input.add_key_mapping(264, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "down"})
        input.add_key_mapping(265, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "up"})
        input.add_key_mapping(262, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "right"})
        input.add_key_mapping(263, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "left"})


    @staticmethod
    def change_gui_edit(**kwargs):
        editor = kwargs["editor"]
        dir = kwargs["dir"]
        if editor.mode is not GuiEditMode.NONE and editor.gui_to_edit is not None:
            if dir == "up":
                if editor.gui_to_edit._parent is not None:
                    editor.gui_to_edit = editor.gui_to_edit._parent
            elif dir == "down":
                gui_children = [g for g in editor.gui_to_edit._children if type(g) is Gui]
                if len(gui_children) > 0:
                    editor.gui_to_edit = gui_children[0]
            elif dir == "left" or dir == "right":
                parent = editor.gui_to_edit._parent
                if parent is not None:
                    gui_children = [g for g in parent._children if type(g) is Gui]
                    num_siblings = len(gui_children)
                    if parent is not None and num_siblings > 0:
                        i = gui_children.index(editor.gui_to_edit)
                        if dir == "left":
                            if i == 0:
                                i = num_siblings - 1
                            else:
                                i = max(i - 1, 0)
                        elif dir == "right":
                            if i == num_siblings - 1:
                                i = 0
                            elif i == 0:
                                i = min(i + 1, num_siblings - 1)
                        index_in_parent = parent._children.index(gui_children[i])
                        editor.gui_to_edit = parent._children[index_in_parent]


    @staticmethod
    def toggle_gui_mode(**kwargs):
        editor = kwargs["editor"]        
        editor.mode = GuiEditMode.NONE if editor.mode != GuiEditMode.NONE else GuiEditMode.INSPECT
        if editor.mode and editor.gui_to_edit is None:
            editor.gui_to_edit = editor.main_gui
    

    @staticmethod
    def to_file(**kwargs):
        editor = kwargs["editor"]
        if editor.mode and editor.gui_to_edit is not None:
            gui = editor.gui_to_edit
            gui_path = Path(os.getcwd()) / "gui"

            if not gui_path.exists():
                os.mkdir(gui_path)

            with open(gui_path / f"{gui.name}.yml", 'w') as stream:
                gui.dump(stream)

    
    @staticmethod
    def from_file(**kwargs):
        editor = kwargs["editor"]
        gui = editor.gui_to_edit
        gui_path = Path(os.getcwd()) / "gui" / f"{gui.name}.yml"
        if gui_path.exists():
            with open(gui_path, 'r') as stream:
                gui.restore(stream)


    @staticmethod
    def add_new_widget(**kwargs):
        editor = kwargs["editor"]
        gui = editor.gui_to_edit
        if editor.mode is not GuiEditMode.NONE:
            editor.deselect()
            gui.add_create_widget()


    @staticmethod
    def remove_widget(**kwargs):
        editor = kwargs["editor"]
        if editor.mode is not GuiEditMode.NONE:
            if editor.widget_to_edit is not None:
                editor.gui.remove_widget(editor.widget_to_edit)
                editor.widget_to_edit = None
                

    @staticmethod
    def toggle_edit_mode(**kwargs):
        editor = kwargs["editor"]
        mode = kwargs["mode"]
        if editor.mode is not GuiEditMode.NONE:
            if editor.mode is GuiEditMode.INSPECT:
                editor.mode = mode
                if editor.mode == GuiEditMode.PARENT:
                    editor.widget_to_set_parent = editor.widget_to_edit
            else:
                editor.mode = GuiEditMode.INSPECT
                editor.edit_start_pos = None


    def deselect(self):
        self.widget_to_edit = None
        self.mode = GuiEditMode.INSPECT


    def _align_hover(self, mouse_pos: Coord2d, widget: any) -> int:
        self.align_hover = -1
        a_half = Coord2d(0.02, 0.04 * self.display_ratio)
        w_half = widget._size * 0.5
        w_half.x = abs(w_half.x)
        w_half.y = abs(w_half.y)
        if (mouse_pos.x >= widget._draw_pos.x - w_half.x - a_half.x and 
            mouse_pos.x <= widget._draw_pos.x - w_half.x + a_half.x):
            self.align_hover = 10
        elif (mouse_pos.x <= widget._draw_pos.x + a_half.x and 
            mouse_pos.x >= widget._draw_pos.x - a_half.x):
            self.align_hover = 20
        elif (mouse_pos.x <= widget._draw_pos.x + w_half.x + a_half.x and 
            mouse_pos.x >= widget._draw_pos.x + w_half.x - a_half.x):
            self.align_hover = 30
        if self.align_hover > 0:
            if (mouse_pos.y <= widget._draw_pos.y + w_half.y + a_half.y and 
                mouse_pos.y >= widget._draw_pos.y + w_half.y - a_half.y):
                self.align_hover += 3
            elif (mouse_pos.y <= widget._draw_pos.y + a_half.y and 
                mouse_pos.y >= widget._draw_pos.y - a_half.y):
                self.align_hover += 2
            elif (mouse_pos.y >= widget._draw_pos.y - w_half.y - a_half.y and 
                mouse_pos.y <= widget._draw_pos.y - w_half.y + a_half.y):
                self.align_hover += 1
            else:
                self.align_hover = -1

    def touch(self, mouse: Cursor):
        if self.mode is GuiEditMode.NONE or self.gui_to_edit is None:
            return

        if self.widget_to_edit is not None:
            self._align_hover(mouse.pos, self.widget_to_edit)

            if self.edit_start_pos is None:
                self.edit_start_pos = mouse.pos
            else:
                edit_diff = mouse.pos - self.edit_start_pos
                if self.mode is GuiEditMode.OFFSET:
                    self.widget_to_edit.set_offset(edit_diff)
                elif self.mode is GuiEditMode.SIZE:
                        self.widget_to_edit.set_size(edit_diff)
            
        touched_widget = False
        self.widget_to_hover = None
        for _, child in enumerate(self.gui_to_edit._children):
            if type(child) is Gui:
                pass
            else:
                if hasattr(child, "touch"):
                    touch_state = child.touch(mouse)
                    if touch_state == TouchState.Hover:
                        self.widget_to_hover = child

                    if self.widget_to_edit is None:
                        if touch_state == TouchState.Touched:
                            self.widget_to_edit = child

                            # Changing the alignment
                            if self.align_hover > 0:
                                new_align = Alignment(
                                    x=AlignX(self.align_hover // 10), 
                                    y=AlignY(self.align_hover - ((self.align_hover // 10) * 10))
                                )
                                self.widget_to_edit.set_offset(Coord2d())
                                self.widget_to_edit.set_align(new_align)
                                self.align_hover = -1

                            # Changing the parent
                            if self.widget_to_set_parent is not None and self.widget_to_set_parent != child:
                                self.widget_to_set_parent.set_parent(child)
                                self.widget_to_set_parent.set_offset(Coord2d())
                            self.widget_to_set_parent = None
                    else:
                        if touch_state == TouchState.Touched:
                            touched_widget = True
        
        # Deselect any selected widget
        if mouse.buttons[0] and touched_widget == False:
            self.deselect()


    def _draw_gui_selection(self, gui: Gui, selection_draw_pos: Coord2d):
        title_draw_colour = [0.7] * 4
        selected_draw_colour = title_draw_colour[:]
        selected_draw_colour[1] = 1.0

        # Draw siblings at this level
        start_draw_pos = selection_draw_pos
        if gui._parent is None:
            self.font.draw(gui.name, 12, selection_draw_pos, selected_draw_colour if gui == self.gui_to_edit else title_draw_colour)
        else:
            for sibling in gui._parent._children:
                if type(sibling) is Gui:
                    self.font.draw(sibling.name, 12, selection_draw_pos, selected_draw_colour if sibling == self.gui_to_edit else title_draw_colour)
                    selection_draw_pos += Coord2d(0.2)

        # Draw children underneath
        num_children = len(gui._children)
        if num_children > 0:
            selection_draw_pos.x = start_draw_pos.x
            selection_draw_pos.y -= 0.1
            for child in gui._children:
                if type(child) is Gui:
                    self.font.draw(child.name, 12, selection_draw_pos, selected_draw_colour if child == self.gui_to_edit else title_draw_colour)
                    selection_draw_pos += Coord2d(0.2)
                

    def draw(self, dt: float):
        if self.mode is GuiEditMode.NONE:
            return

        if self.gui_to_edit is None:
            return

        selection_draw_pos = Coord2d(-0.75, 0.75)
        self.font.draw(self.mode.name, 8, selection_draw_pos + Coord2d(0.0, 0.1), [1.0, 0.75, 1.0, 0.5])
        self._draw_gui_selection(self.main_gui, selection_draw_pos)
        
        def debug_widget_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1i(self.debug_selected_id, selected_widget_id)
            glUniform1i(self.debug_hover_id, hover_widget_id)
            glUniform1i(self.debug_align_hover_id, self.align_hover)
            glUniform4fv(self.debug_size_pos_id, GuiEditor.NUM_DEBUG_WIDGETS, self.debug_size_pos)
            glUniform2fv(self.debug_parent_pos_id, GuiEditor.NUM_DEBUG_WIDGETS, self.debug_parent_pos)
            glUniform1iv(self.debug_align_id, GuiEditor.NUM_DEBUG_WIDGETS, self.debug_align)

        # Start with no valid debug alignment, nothing will show
        hover_widget_id = -1
        selected_widget_id = -1
        for i in range(GuiEditor.NUM_DEBUG_WIDGETS):
            self.debug_align[i] = 0

        self.debug_dirty = True # remove, should be sent up the hierachy by widget mutators
        if self.debug_dirty:
            debug_widget_index = 0
            debug_children = {i: w for i, w in enumerate(self.gui_to_edit._children) if type(w) is not Gui}
            idx = 0
            for _, widget in debug_children.items():
                self.font.draw(widget.name, 8, widget._draw_pos, [0.75] * 4)
                if widget == self.widget_to_edit:
                    selected_widget_id = idx
                if widget == self.widget_to_hover:
                    hover_widget_id = idx
                sp_index = debug_widget_index * 4
                self.debug_size_pos[sp_index + 0] = widget._size.x
                self.debug_size_pos[sp_index + 1] = widget._size.y
                self.debug_size_pos[sp_index + 2] = widget._draw_pos.x
                self.debug_size_pos[sp_index + 3] = widget._draw_pos.y
                if widget._parent is not None:
                    pp_index = debug_widget_index * 2
                    self.debug_parent_pos[pp_index + 0] = widget._parent._draw_pos.x
                    self.debug_parent_pos[pp_index + 1] = widget._parent._draw_pos.y
                self.debug_align[debug_widget_index] = (widget._align.x.value * 10) + widget._align.y.value
                debug_widget_index += 1
                if debug_widget_index >= GuiEditor.NUM_DEBUG_WIDGETS:
                    break
                idx += 1

            self.sprite.draw(debug_widget_uniforms)
            self.debug_dirty = False
