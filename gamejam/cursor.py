from gamejam.coord import Coord2d
class Cursor:
    """Encapsulates mouse, touch and other constant motion input devices that
    move on a 2D plane with 1 or more boolean inputs."""
    def __init__(self):
        self.pos = Coord2d()
        self.buttons = {0: False, 2: False, 3: False, 4: False}
        self.sprite = None
        self.text_edit_buffer = None
        self.text_edit_pos = Coord2d()


    def set_sprite(self, sprite):
        self.sprite = sprite


    def draw(self, dt: float):
        if self.sprite is not None:
            self.sprite.pos = self.pos
            self.sprite.draw()


    def set_text_edit(self, pos: Coord2d, input, on_key_func, on_commit_func):
        self.text_edit_pos = pos