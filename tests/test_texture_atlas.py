from pathlib import Path
import time

from gamejam.font import Font
from gamejam.gui import Gui
from gamejam.gamejam import GameJam
from gamejam.texture import SpriteTexture
from gamejam.coord import Coord2d

class GameWithTextureAtlas(GameJam):

    def __init__(self):
        super(GameWithTextureAtlas, self).__init__()
        self.name = "GameWithTextureAtlas"


    def prepare(self):
        super().prepare(texture_path="C:\\Projects\\midimaster\\tex\\gui")

        test_gui = Gui("test_gui", self.graphics, self.font)
        test_gui.set_active(True, True)
        
        test_atlas_image = self.textures.create_sprite_atlas_texture("btnback", Coord2d(0.0, 0.0), Coord2d(0.5, 0.5))
        test_gui.add_create_widget(test_atlas_image)

        self.gui.add_child(test_gui)


    def update(self, dt):
        game_draw, _ = self.gui.is_active()
        if game_draw:
            self.profile.begin("game_loop")

            self.profile.end()

    def end(self):
        super().end()


def test_texture_atlas():
    jam = GameWithTextureAtlas()
    jam.prepare()

    gui_splash = Gui("test_texture_atlas", jam.graphics, jam.font)
    gui_splash.set_active(True, True)
    jam.gui.add_child(gui_splash)

    jam.begin()

    test_time = 10.0
    if time.time() >= jam.start_time + test_time:
        jam.end()
        return True
    return False


if __name__ == "__main__":
    test_texture_atlas()
