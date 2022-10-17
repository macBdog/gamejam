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
    FadeInOutSmooth = 3
    Pulse = 4
    Rotate = 5
    Throb = 6
    Scroll = 7
    ScrollHorizontal = 8
    ScrollVertical = 9
  

class Animation:
    """ Animations store the state and timers for controller
    a variety of 2D tweens. The timer always counts down to 0.
    The value is in range 0.0 <= val <= 1.0 and drives the visuals.
    :param anim_type: An enum of a function describing the relation between time and val
    :param time: A float for the duration of the function
    """
    def __init__(self, sprite: SpriteTexture):
        self.sprite = sprite
        self.val = 1.0
        self.active = True
        self.action = None
        self.action_kwargs = None
        self.action_time = -1
        self.actioned = False
        self.type = BitSet()

        self._type_id = -1
        self._val_id = -1
        self._timer_id = -1


    def reset(self, new_type=None, value=1.0):
        self.timer = 0.0
        self.val = value

        if new_type is not None:
            self.type.set_bit(new_type.value)   

        if self._type_id < 0:
            self._type_id = glGetUniformLocation(self.sprite.shader, "Type")
            self._val_id = glGetUniformLocation(self.sprite.shader, "Val")
            self._timer_id = glGetUniformLocation(self.sprite.shader, "Timer")
            self._display_ratio_id = glGetUniformLocation(self.sprite.shader, "DisplayRatio")


    def set_animation(self, type:AnimType):
        self.type.set_bit(type.value)


    def set_action(self, time: float, activation_func, action_kwargs=None):
        """Setup an action to be called at a specific time in the animation.
        :param time for the time in the animation to execute, -1 means when complete.
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

            if self.val > 0 and self.timer >= self.val:
                self.active = False
                
            if self.action is not None:
                do_action = self.timer >= self.action_time

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
            glUniform1f(self._val_id, self.val)
            glUniform1f(self._timer_id, self.timer)
            glUniform1f(self._display_ratio_id, self.sprite.graphics.display_ratio)

        self.sprite.draw(anim_uniforms)
