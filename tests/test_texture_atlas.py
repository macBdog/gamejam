import math
from pathlib import Path
import time

from gamejam.gui import Gui
from gamejam.gamejam import GameJam
from gamejam.coord import Coord2d

class GameWithTextureAtlas(GameJam):

    def __init__(self):
        super(GameWithTextureAtlas, self).__init__()
        self.name = "GameWithTextureAtlas"
        self.anim = 0.0

    def prepare(self):
        super().prepare(texture_path="C:\\Projects\\midimaster\\tex\\gui")

        test_gui = Gui("test_gui", self.graphics, self.font)
        test_gui.set_active(True, True)

        test_atlas_image = self.textures.create("btn_devices.png", Coord2d(0.0, 0.0), Coord2d(0.15, 0.15))
        test_gui.add_create_widget(test_atlas_image)

        test_atlas_image2 = self.textures.create("btn_options.png", Coord2d(0.66, 0.66), Coord2d(0.15, 0.15))
        self.anim_widget = test_gui.add_create_widget(test_atlas_image2)

        self.anim_text = test_gui.add_create_text_widget(self.font, "Moving Text", 12, Coord2d(0.1, 0.1))

        self.gui.add_child(test_gui)


    def update(self, dt):
        game_draw, _ = self.gui.is_active()
        if game_draw:
            self.profile.begin("game_loop")

            self.anim_text.set_offset(Coord2d(math.sin(self.anim), math.cos(self.anim)))
            self.anim_widget.set_offset(Coord2d(math.sin(self.anim), math.cos(self.anim)))
            self.anim += dt
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

