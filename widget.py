import enum

from gamejam.animation import AnimType, Animation
from gamejam.graphics import Shader
from gamejam.texture import SpriteTexture
from gamejam.cursor import Cursor
from gamejam.font import Font


class AlignX(enum.Enum):
    Left = 1
    Centre = 2
    Right = 3

class AlignY(enum.Enum):
    Top = 1
    Middle = 2
    Bottom = 3

class Widget:
    """A collection of functionality around the display of a texture for interfaces.
        It owns a reference to a SpriteTexture or SpriteShape for drawing.
        Base class can display and animate alpha, width, height. 
        Child classes are expected to handle input and other functionality."""

    def __init__(self, sprite: SpriteTexture, font:Font=None):
        self.sprite = sprite
        self.alignX = AlignX.Centre
        self.alignY = AlignY.Middle
        self.touched = False
        self.hover_begin = None
        self.hover_end = None
        self.action = None
        self.action_kwargs = None
        self.colour_func = None
        self.colour_kwargs = None
        self.actioned = False
        if self.sprite is not None:
            self.alpha_start = self.sprite.colour[3]
        self.alpha_hover = -0.25
        self.font = font
        self.text = ""
        self.text_size = 0
        self.text_alignX = AlignX.Centre
        self.text_alignY = AlignY.Middle
        self.text_pos = [0.0, 0.0]
        self.text_col = [1.0, 1.0, 1.0, 1.0]

        self.animation = None


    def hover_begin_default(self):
        if self.sprite is not None:
            self.sprite.set_alpha(self.alpha_start + self.alpha_hover)


    def hover_end_default(self):
        if self.sprite is not None:
            self.sprite.set_alpha(self.alpha_start)


    def set_text(self, text: str, size:int, offset=None, align_x=AlignX.Centre, align_y=AlignY.Middle):
        self.text = text
        self.text_size = size
        self.text_alignX = align_x
        self.text_alignY = align_y
        if offset is not None:
            self.text_pos = offset


    def set_text_colour(self, colour: list):
        self.text_col = colour


    def set_colour_func(self, colour_func, colour_kwargs=None):
        """ Set a function that determines the colour of a button."""
        self.colour_func = colour_func
        self.colour_kwargs = colour_kwargs


    def set_action(self, activation_func, activation_kwargs):
        """Set the function to call on activate. Leave the hover functions defaulted."""
        self.action = activation_func
        self.action_kwargs = activation_kwargs
        self.on_hover_begin = self.hover_begin_default
        self.on_hover_end = self.hover_end_default


    def set_actions(self, activation_func, hover_start_func, hover_end_func, activation_arg):
        """Set the function to call on activate with custom hover start and end functions."""
        self.hover_begin = hover_start_func
        self.hover_end = hover_end_func
        self.action = activation_func
        self.action_kwargs = activation_arg


    def set_pos(self, pos: list):
        # TODO - Hierachy of widgets with a parent position and offsets for sprite and text separately
        if self.sprite is None:
            self.text_pos = pos
        else:
            self.sprite.pos = pos


    def on_hover_begin(self):
        pass

    def on_hover_end(self):
        pass

    def on_activate(self):
        pass


    def animate(self, anim_type: AnimType, time: float):
        if self.animation == None:
            self.animation = Animation(anim_type, time)
        else:
            self.animation.reset(anim_type, time)

        anim_prog = self.sprite.graphics.get_program(Shader.ANIM)
        if self.sprite.shader != anim_prog:
            self.sprite.shader = anim_prog


    def align(self, x: AlignX, y: AlignY):
        if self.sprite is not None:
            if x == AlignX.Left:
                self.sprite.pos = [self.sprite.pos[0] - self.sprite.size[0] * 0.5, self.sprite.pos[1]]
            elif x == AlignX.Centre:
                pass
            elif x == AlignX.Right:
                self.sprite.pos = [self.sprite.pos[0] + self.sprite.size[0] * 0.5, self.sprite.pos[1]]
            if y == AlignY.Top:
                self.sprite.pos = [self.sprite.pos[0], self.sprite.pos[1] - self.sprite.size[1] * 0.5]
            elif y == AlignY.Middle:
                pass
            elif y == AlignY.Bottom:
                self.sprite.pos = [self.sprite.pos[0], self.sprite.pos[1] + self.sprite.size[1] * 0.5]


    def touch(self, mouse: Cursor):
        """Test for activation and hover states."""
        if self.sprite is not None:
            if self.action is not None:
                size_half = [abs(i * 0.5) for i in self.sprite.size]
                inside = (  mouse.pos[0] >= self.sprite.pos[0] - size_half[0] and
                            mouse.pos[0] <= self.sprite.pos[0] + size_half[0] and
                            mouse.pos[1] >= self.sprite.pos[1] - size_half[1] and
                            mouse.pos[1] <= self.sprite.pos[1] + size_half[1])
                if self.touched:
                    if not inside:
                        self.on_hover_end()
                        self.touched = False
                else:
                    if inside:
                        self.on_hover_begin()
                        self.touched = True

                # Perform the action on mouse up
                if inside:
                    if mouse.buttons[0]:
                        if not self.actioned:
                            self.actioned = True
                    elif self.actioned:
                        self.action(**self.action_kwargs)
                        self.actioned = False

                if not mouse.buttons[0]:
                    self.actioned = False


    def draw(self, dt: float):
        """Apply any changes to the widget rect."""

        # Apply any active animation
        if self.animation and self.animation.active:
            self.animation.tick(dt)
            
        if self.sprite is not None:
            # Apply any colour changes
            if self.colour_func is not None:
                self.sprite.set_colour(self.colour_func(**self.colour_kwargs))

            if self.animation is not None:
                self.sprite.set_alpha(self.animation.val)

            self.sprite.draw()

        if len(self.text) > 0 and self.font is not None:
            text_pos = self.text_pos[:]

            if self.sprite is not None:
                text_pos[0] += self.sprite.pos[0]
                text_pos[1] += self.sprite.pos[1]
                
            self.font.draw(self.text, self.text_size, text_pos, self.text_col)


