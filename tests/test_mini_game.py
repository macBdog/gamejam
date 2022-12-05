import os
import math
import numpy as np
import time
import sys

from gamejam.animation import AnimType
from gamejam.gui_widget import GuiWidget
from gamejam.input import InputActionKey, InputActionModifier
from gamejam.settings import GameSettings
from gamejam.gamejam import GameJam
from gamejam.texture import Texture, SpriteTexture

class MiniGame(GameJam):
    
    def __init__(self):
        super(MiniGame, self).__init__()
        self.name = "MiniGame"
        self.reset()
        

    def reset(self, reset_score:bool=True):
        if reset_score:
            self.score = 0
        self.magic_number = np.random.randint(1, 9 + 1)

    @staticmethod
    def guess_func(**kwargs):
        game = kwargs["game"]
        num = kwargs["num"]
        if num == game.magic_number:
            game.score += 10
        else:
            game.score -= 1
        MiniGame.reset(game, reset_score=False)


    def prepare(self):
        super().prepare()

        # Make ten guessing buttons each with a different animation effect
        num_widgets = 10
        widget_dimension = 0.35
        widget_size = [widget_dimension * self.graphics.display_ratio, widget_dimension]
        self.guess_widgets = []
        self.guess_sprites = []
        for i in range(num_widgets):
            idx = i + 1
            anim = AnimType(11 - i
            
            )
            widget_pos = [-0.65 + (i * 0.3) - ((i // 5) * (5 * 0.3)), 0.25 - ((i // 5) * 0.5)]
            
            sprite = SpriteTexture(self.graphics, Texture("", 64, 64), [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], widget_size)
            widget = GuiWidget(name=f"Guess{idx}", font=self.font)
            widget.set_size(widget_size)
            widget.set_offset(widget_pos)
            widget.set_sprite(sprite, stretch=True)
            
            widget.set_text(str(idx), 14, [0.0, 0.0])
            widget.set_action(MiniGame.guess_func, {"game": self, "num": idx})
            widget.animate(anim)
            self.gui.add_child(widget)

            self.guess_sprites.append(sprite)
            self.guess_widgets.append(widget)

            self.input.add_key_mapping(48 + i, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, MiniGame.guess_func, {"game": self, "num": i})
            
        if GameSettings.DEV_MODE:
            print("Finished preparing!")


    def update(self, dt):
        game_draw, game_input = self.gui.is_active()
        if game_draw:
            self.profile.begin("game_loop")
            self.font.draw(f"+", 18, self.gui.cursor.pos, [1.0] * 4)
            self.font.draw(f"Guess the number.", 12, [-0.5, 0.7], [1.0, 1.0, 1.0, 1.0])
            self.font.draw(f"Your score: {self.score}", 10, [-0.5, -0.5], [1.0, 1.0, 1.0, 1.0])
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

    test_time = 10
    arg_string = "seconds"
    for _, arg in enumerate(sys.argv):
        found_char = arg.find(arg_string)
        if found_char >= 0:
            arg_val = arg[found_char + len(arg_string):].replace("=", "")
            arg_val = arg_val.replace(" ", "")
            test_time = float(arg_val)

    if time.time() >= jam.start_time + test_time:
        jam.end()
        return True
    
    return False


if __name__ == "__main__":
    test_mini_game()
