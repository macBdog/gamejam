import enum
from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1i,
    glUniform1f, 
)

from gamejam.bitset import BitSet
from gamejam.texture import SpriteTexture

class AnimType(enum.Enum):
    """Matches shader preprocessor definitions in anim.frag"""
    FadeIn = 1
    FadeOut = 2
    Pulse = 3
    FadeInOutSmooth = 4
    Rotate = 5
    Throb = 6
    ScrollHorizontal = 7
    ScrollVertical = 8
    FillHorizontal = 9
    FillVertical = 10
    FillRadial = 11

class Animation:
    """ Animations store the state and timers for controller
    a variety of 2D tweens. The timer always counts down to 0.
    The value is in range 0.0 <= val <= 1.0 and drives the visuals.
    :param anim_type: An enum of a function describing the relation between time and val
    :param time: A float for the duration of the function
    """
    def __init__(self, sprite: SpriteTexture):
        self.timer = 0.0
        self.time = 1.0
        self.frac = 0.0
        self.mag = 1.0
        self.sprite = sprite
        self.active = True
        self.action = None
        self.action_kwargs = None
        self.action_time = -1
        self.actioned = False
        self.type = BitSet()
        self.loop = True

        self._type_id = -1
        self._mag_id = -1       # The magnitude of the effect, a multiplier
        self._frac_id = -1      # The fraction of the effect between 0.0 and 1.0   


    def reset(self, new_type=None, time=-1.0, mag=1.0):
        self.timer = 0.0
        self.time = 1.0
        self.frac = 0.0
        self.mag = mag   

        if new_type is not None:
            self.type.set_bit(new_type.value)   

        if self._type_id < 0:
            self._type_id = glGetUniformLocation(self.sprite.shader, "Type")
            self._mag_id = glGetUniformLocation(self.sprite.shader, "Mag")
            self._frac_id = glGetUniformLocation(self.sprite.shader, "Frac")
            self._display_ratio_id = glGetUniformLocation(self.sprite.shader, "DisplayRatio")


    def set_animation(self, type:AnimType):
        self.type.set_bit(type.value)


    def set_action(self, time: float, activation_func, action_kwargs=None):
        """Setup an action to be called at a specific time in the animation.
        :param time for the time in the animation to execute
        """
        self.action = activation_func
        self.action_kwargs = action_kwargs
        self.action_time = time
       

    def tick(self, dt: float):
        """Update timers and values as per the animation type.
        :param dt: The time that has elapsed since the last tick.
        """
        if self.active:
            self.timer += dt

            # Using a timer to drive frac
            do_action = False
            if self.time > 0.0:
                if self.timer >= self.time:
                    do_action = True
                    if self.loop:
                        self.timer = 0.0
                        self.active = True
                    else:
                        self.active = False
                        self.timer = self.time

                self.frac = self.timer / self.time    

            if self.action is not None:
                if do_action:
                    if not self.actioned:
                        if self.action_kwargs is None:
                            self.action()
                        else:
                            self.action(**self.action_kwargs)
                        self.actioned = True


    def draw(self, dt: float):
        def anim_uniforms():
            glUniform1i(self._type_id, self.type.get_bits())
            glUniform1f(self._mag_id, self.mag)
            glUniform1f(self._frac_id, self.frac)
            glUniform1f(self._display_ratio_id, self.sprite.graphics.display_ratio)

        self.sprite.draw(anim_uniforms)
