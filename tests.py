import os
import math
import numpy as np
from font import Font
from gui import Gui
from input import InputActionKey, InputActionModifier
from settings import GameSettings
from gamejam import GameJam

class MiniGame(GameJam):
    
    def __init__(self):
        super(MiniGame, self).__init__()
        self.name = "MiniGame"
        self.score = 0
        self.magic_number = np.random.random_integers(1, 9)


    def prepare(self):
        super().prepare()

        self.font = Font(os.path.join("res", "consola.ttf"), self.graphics, self.window)
        self.gui = Gui(1024, 768, "gui")
        self.gui.set_active(True, True)

        if GameSettings.DEV_MODE:
            print("Finished preparing!")


    def update(self, dt):
        game_draw, game_input = self.gui.is_active()
        if game_draw:
            self.profile.begin("game_loop")
            self.font.draw(f"Guess the number.", 12, [-0.5, 0.0], [1.0, 1.0, 1.0, 1.0])
            self.font.draw(f"Your score: {self.score}", 10, [-0.5, -0.5], [1.0, 1.0, 1.0, 1.0])

            if game_input:
                def guess_func(num: int):
                    if num == self.magic_number:
                        self.score += 10
                    else:
                        self.score -= 1

                    for i in range(9):
                        self.input.add_key_mapping(10 + i, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, guess_func, i)
            self.profile.end()

            self.profile.begin("dev_mode")
            if GameSettings.DEV_MODE:
                cursor_pos = self.input.cursor.pos
                self.font.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
                self.font.draw(f"X: {math.floor(cursor_pos[0] * 100) / 100}\nY: {math.floor(cursor_pos[1] * 100) / 100}", 10, cursor_pos, [0.81, 0.81, 0.81, 1.0])
            self.profile.end()


    def end(self):
        super().end()


def test_mini_game():
    jam = MiniGame()
    jam.prepare()
    jam.begin()


if __name__ == "__main__":
    test_mini_game()
