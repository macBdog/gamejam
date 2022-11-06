import os
import math
import numpy as np

from gamejam.font import Font
from gamejam.gui import Gui
from gamejam.input import InputActionKey, InputActionModifier
from gamejam.settings import GameSettings
from gamejam.gamejam import GameJam

class GameWithGui(GameJam):
    
    def __init__(self):
        super(GameWithGui, self).__init__()
        self.name = "GameWithGui"


    def prepare(self):
        super().prepare()

        self.font = Font(os.path.join("gamejam", "res", "consola.ttf"), self.graphics, self.window)
        self.gui = Gui("gui", self.graphics)
        self.gui.set_active(True, True)


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

    gui_splash = Gui("parent")
    gui_splash.set_active(True, True)
    jam.gui.add_child(gui_splash)

    jam.end()
    return True


if __name__ == "__main__":
    test_gui()
