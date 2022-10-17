import os
import glfw
import time
import math
from pathlib import Path
from OpenGL.GL import (
    glViewport,
    glClear, glClearColor,
    glShadeModel,
    glEnable,
    glDepthFunc, glBlendFunc,
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    GL_BLEND, GL_SMOOTH, GL_DEPTH_TEST, GL_LEQUAL,
    GL_TRUE
)

from gamejam.graphics import Graphics
from gamejam.input import Input, InputActionKey, InputMethod, InputActionModifier
from gamejam.texture import TextureManager
from gamejam.gui import Gui
from gamejam.font import Font
from gamejam.profile import Profile
from gamejam.particles import Particles
from gamejam.settings import GameSettings

class GameJam:
    """A generic interactive frame interpolation loop without connection to specific logic."""

    def __init__(self):
        self.name = "game"
        self.running = False
        self.window_width = 1920
        self.window_height = 1080
        self.window_ratio = self.window_width / self.window_height
        self.start_time = 0
        self.dt = 0.03
        self.fps = 0
        self.fps_last_update = 1
    

    def prepare(self, texture_path: str = "tex"):
        if not glfw.init():
            return

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(self.window_width, self.window_height, self.name, None, None)
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        if not self.window:
            glfw.terminate()
            return

        glfw.make_context_current(self.window)

        self.running = True

        # Now we have an OpenGL context we can compile GPU programs
        self.graphics = Graphics(self.window_width / self.window_height)
        self.textures = TextureManager(texture_path, self.graphics)
        self.input = Input(self.window, InputMethod.KEYBOARD)
        self.particles = Particles(self.graphics)
        self.profile = Profile()

        # Bind escape to quit and prtscn to outputing profile info
        self.input.add_key_mapping(256, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.quit)
        self.input.add_key_mapping(283, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.profile.capture_next_frame)

        def toggle_dev_mode():
            GameSettings.DEV_MODE = not GameSettings.DEV_MODE

        # CtrlD to enable developer mode
        self.input.add_key_mapping(68, InputActionKey.ACTION_KEYDOWN, InputActionModifier.LCTRL, toggle_dev_mode)

        glViewport(0, 0, self.window_width, self.window_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
        glfw.swap_interval(GameSettings.VSYNC)

        self.gui = Gui("gui")
        self.gui.set_active(False, False)
        font_path = Path(__file__).parent / "res" / "consola.ttf"
        self.font = Font(str(font_path), self.graphics, self.window)


    def begin(self):
        self.start_time = time.time()
        dt_cur = dt_last = self.start_time

        while self.running and not glfw.window_should_close(self.window):
            self.profile.update()

            dt_cur = time.time()
            self.dt = dt_cur - dt_last
            dt_last = dt_cur
            self.fps_last_update -= self.dt

            if self.fps_last_update <= 0:
                self.fps = 1.0 / self.dt
                self.fps_last_update = 1.0

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self.profile.begin("gui")
            self.gui.touch(self.input.cursor)
            self.gui.draw(self.dt)
            self.input.cursor.draw(self.dt)
            self.profile.end()

            self.profile.begin("game")
            self.update(self.dt)
            self.profile.end()

            self.profile.begin("dev_stats")
            if GameSettings.DEV_MODE:
                cursor_pos = self.input.cursor.pos
                self.font.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
                self.font.draw(f"X: {math.floor(cursor_pos[0] * 100) / 100}\nY: {math.floor(cursor_pos[1] * 100) / 100}", 10, cursor_pos, [0.81, 0.81, 0.81, 1.0])
            self.profile.end()

            self.profile.begin("particles")
            self.particles.draw(self.dt)
            self.profile.end()

            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.end()


    def update(self, dt):
        # Child classes define frame specific behaviour here
        pass


    def quit(self):
        self.running = False


    def end(self):
        self.running = False
        glfw.terminate()
