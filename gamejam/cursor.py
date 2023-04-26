from gamejam.coord import Coord2d
from gamejam.font import Font
class Cursor:
    """Encapsulates mouse, touch and other constant motion input devices that
    move on a 2D plane with 1 or more boolean inputs."""

    FONT_SIZE = 10
    KEYCODE_COMMIT = 257
    KEYCODE_CANCEL = 256
    KEYCODE_BACKSPACE = 259
    KEYCODES_INVALID = [340, 344]

    def __init__(self, font: Font):
        self.pos = Coord2d()
        self.buttons = {0: False, 2: False, 3: False, 4: False}
        self.sprite = None
        self.font = font
        self.text_edit_buffer = None
        self.text_edit_pos = None
        self.text_edit_timer = 0.0
        self.text_edit_commit_func = None
        self.text_edit_commit_kwargs = None


    def is_text_edit_active(self):
        return self.text_edit_pos is not None


    def set_sprite(self, sprite):
        self.sprite = sprite


    def draw(self, dt: float):
        if self.sprite is not None:
            self.sprite.pos = self.pos
            self.sprite.draw()

        if self.text_edit_pos is not None:
            bar_char = "_" if int(self.text_edit_timer) % 2 == 0 else "|"
            self.font.draw(f"{self.text_edit_buffer}{bar_char}", Cursor.FONT_SIZE, self.text_edit_pos, [0.0, 1.0, 0.0, 1.0])
            self.text_edit_timer += dt * 2.0


    def handle_input_key(self, window, key: int, scancode: int, action: int, mods: int):
        if action:
            if key == Cursor.KEYCODE_COMMIT:
                self.text_edit_pos = None
                if self.text_edit_commit_func is not None:
                    self.text_edit_commit_kwargs.update({"text": self.text_edit_buffer})
                    self.text_edit_commit_func(**self.text_edit_commit_kwargs)
            elif key == Cursor.KEYCODE_CANCEL:
                self.text_edit_pos = None
            elif key == Cursor.KEYCODE_BACKSPACE:
                self.text_edit_buffer = self.text_edit_buffer[:-1]
            elif key not in Cursor.KEYCODES_INVALID:
                char = chr(key) if mods else chr(key + 32)
                self.text_edit_buffer += char


    def set_text_edit(self, buffer: str, pos: Coord2d, on_commit_func=None, on_commit_kwargs=None):
        self.text_edit_pos = pos
        self.text_edit_timer = 0.0
        self.text_edit_buffer = buffer
        self.text_edit_commit_func = on_commit_func
        self.text_edit_commit_kwargs = on_commit_kwargs
