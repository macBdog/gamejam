import glfw
from enum import Enum

from gamejam.coord import Coord2d
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.settings import GameSettings
from gamejam.quickmaff import clamp


class InputActionKey(Enum):
    ACTION_KEYUP = 0
    ACTION_KEYDOWN = 1
    ACTION_KEYREPEAT = 2


class InputActionModifier(Enum):
    NONE = 0
    LSHIFT = 340
    LCTRL = 341
    LALT = 342
    RSHIFT = 344
    RCTRL = 345
    RALT = 346


class InputMethod(Enum):
    KEYBOARD = 1
    JOYSTICK = 2
    MIDI = 3


class Input:
    """Utility class to handle different methods of input to the game, handles all events from the window system."""

    def __init__(self, window, method: InputMethod, font: Font):
        self.method = method
        self.window = window
        self.cursor = Cursor(font)
        self.keys_down = {}
        self.key_mapping = {}
        self.scroll_mapping = []

        glfw.set_key_callback(window, self.handle_input_key)
        glfw.set_mouse_button_callback(window, self.handle_mouse_button)
        glfw.set_cursor_pos_callback(window, self.handle_cursor_update)
        glfw.set_scroll_callback(window, self.handle_scroll_update)


    def add_key_mapping(self, key: int, action: InputActionKey, modifier: InputActionModifier, func, kwargs=None):
        key_action_pair = (key, action, modifier)
        if key_action_pair in self.key_mapping:
            self.key_mapping[key_action_pair].extend([func, kwargs])
        else:
            self.key_mapping.update({key_action_pair: [func, kwargs]})


    def add_scroll_mapping(self, func, kwargs={}):
        self.scroll_mapping.append((func, kwargs))


    def add_joystick_mapping(self, button: int, func, args=None):
        pass


    def add_midi_mapping(self, note: int, func, args=None):
        pass


    def handle_cursor_update(self, window, xpos, ypos):
        window_size = glfw.get_framebuffer_size(window)
        xpos = clamp(xpos, 0.0, window_size[0])
        ypos = clamp(ypos, 0.0, window_size[1])
        self.cursor.pos = Coord2d(((xpos / window_size[0]) * 2.0) - 1.0, ((ypos / window_size[1]) * -2.0) + 1.0)


    def handle_scroll_update(self, window, xpos, ypos):
        if GameSettings.DEV_MODE:
            print(f"Scroll event log x[{xpos}], y[{ypos}]")

        for mapping in self.scroll_mapping:
            func = mapping[0]
            kwargs = mapping[1]
            kwargs.update({"x": xpos, "y": ypos})
            func(**kwargs)


    def handle_mouse_button(self, window, button: int, action: int, mods: int):
        if GameSettings.DEV_MODE:
            print(f"Mouse event log button[{button}], action[{action}], mods[{mods}]")

        # Update the state of each button
        if action == InputActionKey.ACTION_KEYDOWN.value:
            self.cursor.buttons[button] = True
        elif action == InputActionKey.ACTION_KEYUP.value:
            self.cursor.buttons[button] = False


    def handle_input_key(self, window, key: int, scancode: int, action: int, mods: int):
        if GameSettings.DEV_MODE:
            print(f"Input event log key[{key}], scancode[{scancode}], action[{action}], mods[{mods}]")

        if self.cursor.is_text_edit_active():
            self.cursor.handle_input_key(window, key, scancode, action, mods)

        # Update the state of each key
        if action == InputActionKey.ACTION_KEYDOWN.value:
            self.keys_down[key] = True
        elif action == InputActionKey.ACTION_KEYUP.value:
            self.keys_down[key] = False

        # Check to see if any modifier keys are down
        mods_down = [x for x in InputActionModifier if x.value in self.keys_down and self.keys_down[x.value] is True]
        no_mods_down = len(mods_down) == 0

        for _, map in enumerate(self.key_mapping.items()):
            mapping = map[0]
            map_key = mapping[0]
            map_action = mapping[1]
            map_modifier = mapping[2]
            matches_action = map_action.value == action or map_action == InputActionKey.ACTION_KEYREPEAT
            matches_modifier = (map_modifier.value in self.keys_down and self.keys_down[map_modifier.value] == True) or (map_modifier == InputActionModifier.NONE and no_mods_down)
            if map_key == key and matches_action and matches_modifier:
                func_args = map[1]
                num_mappings = len(func_args) // 2
                for i in range(num_mappings):
                    func = func_args[i * 2]
                    kwargs = func_args[i * 2 + 1]
                    if kwargs is None:
                        func()
                    else:
                        func(**kwargs)
