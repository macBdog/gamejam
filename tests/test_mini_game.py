import os
import time
import math
import numpy as np

from gamejam.animation import AnimType
from gamejam.font import Font
from gamejam.gui import Gui
from gamejam.widget import Widget
from gamejam.input import InputActionKey, InputActionModifier
from gamejam.settings import GameSettings
from gamejam.gamejam import GameJam
from gamejam.texture import Texture, SpriteTexture

class MiniGame(GameJam):
    
    def __init__(self):
        super(MiniGame, self).__init__()
        self.name = "MiniGame"
        self.score = 0
        self.magic_number = np.random.randint(1, 9 + 1)


    def prepare(self):
        super().prepare()

        self.font = Font(os.path.join("gamejam", "res", "consola.ttf"), self.graphics, self.window)
        self.gui = Gui("gui")
        self.gui.set_active(True, True)

        self.animated_bg_tex = Texture("", 128, 128)
        self.animated_sprite = SpriteTexture(self.graphics, self.animated_bg_tex, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [0.5, 0.5])
        self.animated_widget = Widget(self.animated_sprite)
        self.animated_widget.animate(AnimType.Rotate)
        self.animated_widget.animation.set_animation(AnimType.InOutSmooth)
        self.gui.add_widget(self.animated_widget)

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

    if time.time() >= jam.start_time + 100:
        jam.end()
        return True
    
    return False


if __name__ == "__main__":
    test_mini_game()
