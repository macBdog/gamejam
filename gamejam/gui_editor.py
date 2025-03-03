import os
from enum import Enum
from pathlib import Path

from gamejam.asset_picker import AssetPicker, AssetType
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
from gamejam.gui_widget import GuiWidget

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
    NAME = 9,
    TEXT = 10,


class GuiEditor():
    """Editor for a GUI to show properties of child widgets and add remove."""
    NUM_DEBUG_WIDGETS = 128

    def __init__(self, main_gui: Gui, graphics: Graphics, input: Input, font: Font):
        super().__init__()
        self.main_gui = main_gui
        self.mode = GuiEditMode.NONE
        self.gui = Gui("GuiEditor", graphics, font, False)
        self.display_ratio = graphics.display_ratio
        self.font = font
        self.edit_start_pos = Coord2d()
        self.debug_dirty = False
        self.gui_to_edit = None
        self.widget_to_edit = None
        self.widget_to_hover = None
        self.widget_to_set_parent = None
        self.align_hover = -1
        self.parent_hover = None
        self.parent_align_hover = -1
        self.picker = AssetPicker(self, graphics, input, font)
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
        self.picker._init_debug_bindings(input)


    def _init_debug_bindings(self, input: Input):
        # Ctrl+N for add widget
        input.add_key_mapping(78, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.add_new_widget, {"editor": self})

        # Ctrl+X to remove selected widget
        input.add_key_mapping(88, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.remove_widget, {"editor": self})

        # Ctrl-G to enable gui editing mode
        input.add_key_mapping(71, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.toggle_gui_mode, {"editor": self})

        # Ctrl-S to serialize gui to yaml file
        input.add_key_mapping(83, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, GuiEditor.to_file, {"editor": self})

        # I for input source asset
        input.add_key_mapping(73, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, GuiEditor.show_asset_picker, {"editor": self})

        # Direction keys to move around the widget hierachy
        input.add_key_mapping(264, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "down"})
        input.add_key_mapping(265, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "up"})
        input.add_key_mapping(262, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "right"})
        input.add_key_mapping(263, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.change_gui_edit, {"editor": self, "dir": "left"})

        # Add a button for each different editor property
        edit_buttons_pos = Coord2d(-0.5, 0.05)
        self.edit_buttons: list[GuiWidget] = []
        for e in GuiEditMode:
            if e != GuiEditMode.NONE and e != GuiEditMode.INSPECT:
                edit_widget = self.gui.add_create_text_widget(
                    font=self.font, 
                    text=f"Set {e.name.lower()}",
                    size=6, 
                    offset=edit_buttons_pos + Coord2d(0.2 * e.value[0], 0.0),
                    name=e.name
                )
                edit_widget.set_align(Alignment(AlignX.Left, AlignY.Middle))
                edit_widget.set_align_to(Alignment(AlignX.Left, AlignY.Bottom))
                edit_widget.set_action(GuiEditor.toggle_edit_mode, {"editor": self, "mode": e})


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
                editor.gui.active_draw = False
                editor.gui.active_input = False


    @staticmethod
    def toggle_edit_mode(**kwargs):
        editor = kwargs["editor"]
        mode = kwargs["mode"]
        edit_kwargs = kwargs.copy()
        edit_kwargs["widget"] = editor.widget_to_edit
        if editor.mode is not GuiEditMode.NONE:
            if editor.mode is GuiEditMode.INSPECT:
                editor.mode = mode
                if editor.mode == GuiEditMode.PARENT:
                    editor.widget_to_set_parent = editor.widget_to_edit
                elif editor.mode == GuiEditMode.NAME:
                    editor.gui.cursor.set_text_edit(
                        buffer=editor.widget_to_edit.name,
                        pos=editor.widget_to_edit._draw_pos,
                        on_commit_func=GuiEditor.on_commit_widget_text,
                        on_commit_kwargs=edit_kwargs,
                    )
                elif editor.mode == GuiEditMode.TEXT:
                    editor.gui.cursor.set_text_edit(
                        buffer=editor.widget_to_edit.text, 
                        pos=editor.widget_to_edit._draw_pos,
                        on_commit_func=GuiEditor.on_commit_widget_text,
                        on_commit_kwargs=edit_kwargs
                    )
            else:
                editor.mode = GuiEditMode.INSPECT
                editor.edit_start_pos = None


    @staticmethod
    def on_commit_widget_text(**kwargs):
        editor = kwargs["editor"]
        widget = kwargs["widget"]
        mode = kwargs["mode"]
        text = kwargs["text"]
        if mode == GuiEditMode.NAME:
            widget.name = text
        elif mode == GuiEditMode.TEXT:
            widget.set_text(text=text, text_size=10, font=editor.font)


    @staticmethod
    def show_asset_picker(**kwargs):
        editor = kwargs["editor"]
        if editor.mode == GuiEditMode.INSPECT:
            if editor.widget_to_edit is not None and editor.picker.active is False:
                editor.picker.show(AssetType.TEXTURE, Path(os.getcwd()))


    def deselect(self):
        self.widget_to_edit = None
        self.mode = GuiEditMode.INSPECT
        self.gui.active_draw = False
        self.gui.active_input = False


    def _get_align_hover(self, mouse_pos: Coord2d, widget: any) -> int:
        align_hover = -1
        a_half = Coord2d(0.02, 0.04 * self.display_ratio)
        w_half = widget._size * 0.5
        w_half.x = abs(w_half.x)
        w_half.y = abs(w_half.y)
        if (mouse_pos.x >= widget._draw_pos.x - w_half.x - a_half.x and 
            mouse_pos.x <= widget._draw_pos.x - w_half.x + a_half.x):
            align_hover = 10
        elif (mouse_pos.x <= widget._draw_pos.x + a_half.x and 
            mouse_pos.x >= widget._draw_pos.x - a_half.x):
            align_hover = 20
        elif (mouse_pos.x <= widget._draw_pos.x + w_half.x + a_half.x and 
            mouse_pos.x >= widget._draw_pos.x + w_half.x - a_half.x):
            align_hover = 30
        if self.align_hover > 0:
            if (mouse_pos.y <= widget._draw_pos.y + w_half.y + a_half.y and 
                mouse_pos.y >= widget._draw_pos.y + w_half.y - a_half.y):
                align_hover += 3
            elif (mouse_pos.y <= widget._draw_pos.y + a_half.y and 
                mouse_pos.y >= widget._draw_pos.y - a_half.y):
                align_hover += 2
            elif (mouse_pos.y >= widget._draw_pos.y - w_half.y - a_half.y and 
                mouse_pos.y <= widget._draw_pos.y - w_half.y + a_half.y):
                align_hover += 1
            else:
                align_hover = -1
        return align_hover


    def touch(self, mouse: Cursor):
        if self.mode is GuiEditMode.NONE or self.gui_to_edit is None:
            return

        if self.picker.active:
            self.picker.touch(mouse)
            return

        touched_widget = False
        if self.widget_to_edit is not None:
            if self.gui.touch(mouse) != TouchState.Clear:
                touched_widget = True

            self._align_hover = self._get_align_hover(mouse.pos, self.widget_to_edit)

            if self.edit_start_pos is None:
                self.edit_start_pos = mouse.pos
            else:
                edit_diff = mouse.pos - self.edit_start_pos
                if self.mode is GuiEditMode.OFFSET:
                    self.widget_to_edit.set_offset(edit_diff)
                elif self.mode is GuiEditMode.SIZE:
                        self.widget_to_edit.set_size(edit_diff)

        self.widget_to_hover = None
        for _, child in enumerate(self.gui_to_edit._children):
            if type(child) is Gui:
                pass
            else:
                if hasattr(child, "touch"):
                    touch_state = child.touch(mouse)
                    if touch_state == TouchState.Hover:
                        self.widget_to_hover = child

                        if self.mode is GuiEditMode.PARENT:
                            self.parent_hover = child
                            self.parent_align_hover = self._get_align_hover(mouse.pos, child)

                    if self.widget_to_edit is None:
                        if touch_state == TouchState.Touched:
                            self.widget_to_edit = child
                            self.gui.active_draw = True
                            self.gui.active_input = True

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

        if self.picker.active:
            self.picker.draw(dt)
            return

        if self.widget_to_edit is not None:
            self.gui.draw(dt)

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
