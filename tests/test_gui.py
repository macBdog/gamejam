import os
import time

from gamejam.font import Font
from gamejam.gui import Gui
from gamejam.gamejam import GameJam

class GameWithGui(GameJam):
    
    def __init__(self):
        super(GameWithGui, self).__init__()
        self.name = "GameWithGui"


    def prepare(self):
        super().prepare()

        self.font = Font(self.graphics, self.window, os.path.join("gamejam", "res", "consola.ttf"))
        test_gui = Gui("test_gui", self.graphics, self.font)
        test_gui.set_active(True, True)

        self.gui.add_child(test_gui)


    def update(self, dt):
        game_draw, game_input = self.gui.is_active()
        if game_draw:
            self.profile.begin("game_loop")

            self.profile.end()

    def end(self):
        super().end()


def test_gui():
    jam = GameWithGui()
    jam.prepare()

    gui_splash = Gui("test_gui_sibling", jam.graphics, jam.font)
    gui_splash.set_active(True, True)
    jam.gui.add_child(gui_splash)

    jam.begin()

    test_time = 10.0
    if time.time() >= jam.start_time + test_time:
        jam.end()
        return True
    return False


if __name__ == "__main__":
    test_gui()
