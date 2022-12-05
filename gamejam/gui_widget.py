import enum

from gamejam.animation import AnimType, Animation
from gamejam.graphics import Shader
from gamejam.texture import SpriteTexture
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.widget import Widget, Alignment, AlignX, AlignY


class TouchState(enum.Enum):
    Clear = 0
    Hover = 1
    Touching = 2 
    Touched = 3


class GuiWidget(Widget):
    """A collection of functionality around the display of a texture for interfaces.
        It owns a reference to a SpriteTexture or SpriteShape for drawing.
        Base class can display and animate alpha, width, height. 
        Child classes are expected to handle input and other functionality."""

    def __init__(self, name: str="", font: Font=None):
        super().__init__(name=name)
        self.sprite = None
        self.sprite_stretch = False
        self.hover = False
        self.hover_begin = None
        self.hover_end = None
        self.action = None
        self.action_kwargs = None
        self.colour_func = None
        self.colour_kwargs = None
        self.actioned = False
        self.alpha_start = 1.0 
        self.alpha_hover = -0.25
        self.font = font
        self.text = ""
        self.text_size = 0
        self.text_align = Alignment(AlignX.Centre, AlignY.Middle)
        self.text_offset = [0.0, 0.0]
        self.text_col = [1.0, 1.0, 1.0, 1.0]
        self.animation = None


    def set_sprite(self, sprite: SpriteTexture, stretch:bool=False):
        """The widget now controls the sprite's position."""
        self.sprite = sprite
        self.sprite_stretch = stretch
        self.alpha_start = self.sprite.colour[3]
        self.sprite.size = self._size
        self.sprite.pos = self._draw_pos


    def hover_begin_default(self):
        if self.sprite is not None:
            self.sprite.set_alpha(self.alpha_start + self.alpha_hover)

        self.text_col[3] = self.alpha_start + self.alpha_hover


    def hover_end_default(self):
        if self.sprite is not None:
            self.sprite.set_alpha(self.alpha_start)

        self.text_col[3] = self.alpha_start


    def set_text(self, text: str, size:int, offset=None, align:Alignment=None):
        self.text = text
        self.text_size = size
        if align is not None:
            self.text_align = align
        if offset is not None:
            self.text_offset = offset


    def set_text_colour(self, colour: list):
        self.text_col = colour


    def set_colour_func(self, colour_func, colour_kwargs=None):
        """ Set a function that determines the colour of a gui widget."""
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


    def on_hover_begin(self):
        pass

    def on_hover_end(self):
        pass

    def on_activate(self):
        pass


    def animate(self, anim_type: AnimType, time: float=-1.0) -> Animation:
        if self.animation == None:
            self.animation = Animation(self.sprite)

        anim_prog = self.sprite.graphics.get_program(Shader.ANIM)
        if self.sprite.shader != anim_prog:
            self.sprite.bind(anim_prog)

        self.animation.reset(anim_type, time)
        return self.animation


    def touch(self, mouse: Cursor) -> TouchState:
        """Test for activation and hover states."""
        state = TouchState.Clear
        touch_pos = self._draw_pos
        touch_size = self._size

        size_half = [abs(i * 0.5) for i in touch_size]
        inside = (  mouse.pos[0] >= touch_pos[0] - size_half[0] and
                    mouse.pos[0] <= touch_pos[0] + size_half[0] and
                    mouse.pos[1] >= touch_pos[1] - size_half[1] and
                    mouse.pos[1] <= touch_pos[1] + size_half[1])
        if self.hover:
            if inside:
                state = TouchState.Hover
            else:
                self.on_hover_end()
                self.hover = False
        else:
            if inside:
                self.on_hover_begin()
                self.hover = True

        # Perform the action on release
        if inside:
            if mouse.buttons[0]:
                if not self.actioned:
                    self.actioned = True
                    state = TouchState.Touching
            elif self.actioned:
                if self.action is not None:
                    self.action(**self.action_kwargs)
                self.actioned = False
                state = TouchState.Touched

        if not mouse.buttons[0]:
            self.actioned = False
        return state


    def draw(self, dt: float):
        super().draw(dt)

        # Apply any active animation
        if self.animation:
            if self.animation.active:
                self.animation.tick(dt)
            self.animation.draw(dt)
        
        if self.sprite is not None:
            # Apply any colour changes defined by user funcs
            if self.colour_func is not None:
                self.sprite.set_colour(self.colour_func(**self.colour_kwargs))

            self.sprite.pos = self._draw_pos
            
            if self.sprite_stretch:
                self.sprite.size = self._size

            self.sprite.draw()

        if len(self.text) > 0 and self.font is not None:
            text_offset = self.text_offset[:]

            if self.sprite is not None:
                text_offset[0] += self.sprite.pos[0]
                text_offset[1] += self.sprite.pos[1]
                
            self.font.draw(self.text, self.text_size, text_offset, self.text_col)

