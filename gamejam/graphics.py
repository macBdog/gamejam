from enum import Enum, auto
import os
import numpy
from pathlib import Path
from OpenGL.GL import (
    glCreateProgram, glCreateShader,
    glShaderSource,
    glCompileShader, glAttachShader, glLinkProgram,
    glGetProgramiv,
    glGetActiveUniform,
    glGetShaderInfoLog, glGetProgramInfoLog,
    GL_VERTEX_SHADER, GL_FRAGMENT_SHADER,
    GL_ACTIVE_UNIFORMS
)
from OpenGL.GL.shaders import (
    compileProgram, compileShader
)

from gamejam.settings import GameSettings

class Shader(Enum):
    TEXTURE = 0
    COLOUR = auto()
    FONT = auto()
    PARTICLES = auto()
    ANIM = auto()
    DEBUG = auto()

class ShaderType(Enum):
    VERTEX = 0
    PIXEL = auto()

class Graphics:
    SHADER_PATH = "shaders"
    DEFAULT_RECTANGLE = numpy.array([-0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, 0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], dtype=numpy.float32)

    def __init__(self, display_width_over_height: float):
        self.display_ratio = 1.0 / display_width_over_height
        self._programs = {}
        self._shaders = {}
        self.default_indices = numpy.array([0, 1, 2, 2, 3, 0], dtype=numpy.uint32)

        # Pre-compile multiple shaders for general purpose drawing
        self._programs[Shader.TEXTURE] = compileProgram(
            compileShader(self.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.TEXTURE, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )

        self._programs[Shader.COLOUR] = compileProgram(
            compileShader(self.builtin_shader(Shader.COLOUR, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.COLOUR, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )

        self._programs[Shader.FONT] = compileProgram(
            compileShader(self.builtin_shader(Shader.FONT, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.FONT, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )

        self._programs[Shader.ANIM] = compileProgram(
            compileShader(self.builtin_shader(Shader.ANIM, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.ANIM, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )
        

    def get_program(self, shader: Shader):
        return self._programs[shader]


    def builtin_shader(self, shader: Shader, type: ShaderType) -> str:
        name = Graphics.get_shader_name(shader, type)
        if name not in self._shaders:
            path = Path(__file__).parent / Graphics.SHADER_PATH / name
            with open(path, 'r') as shader_file:
                self._shaders[name] = shader_file.read()   
        return self._shaders[name]


    @staticmethod
    def get_shader_name(shader: Shader, type: ShaderType) -> str:
        return f"{shader._name_.lower()}.{'vert' if type is ShaderType.VERTEX else 'frag'}"


    @staticmethod
    def create_program(vertex_shader_source: str, pixel_shader_source: str):
        return compileProgram(
            compileShader(vertex_shader_source, GL_VERTEX_SHADER), 
            compileShader(pixel_shader_source, GL_FRAGMENT_SHADER)
        )

    
    @staticmethod
    def load_shader(shader_path: str) -> str:
        if os.path.exists(shader_path):
            with open(shader_path, 'r') as shader_file:
                return shader_file.read()
        elif GameSettings.DEV_MODE:
            print(f"Shader load failure, cannot find path: {shader_path}")


    @staticmethod
    def process_shader_source(src: str, subs: dict) -> str:
        for key, sub in subs.items():
            if src.find(key):
                src = src.replace(key, str(sub))
            elif GameSettings.DEV_MODE:
                print(f"Cannot find shader substitute key: {key} ")
        return src


    @staticmethod
    def print_all_uniforms(shader: int):
        num_uniforms = glGetProgramiv(shader, GL_ACTIVE_UNIFORMS)
        for i in range(num_uniforms):
            name, size, type = glGetActiveUniform(shader, i)
            print(f"Shader unfiform dump - Name: {name}, type: {type}, size: {size}")


    @staticmethod
    def debug_print_shader(vertex_source: str, fragment_source: str):
        """Utility function to compile and link a shader and print all log info out."""
        program = glCreateProgram()

        vshader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vshader, vertex_source)
        glCompileShader(vshader)
        glAttachShader(program, vshader)
        print(glGetShaderInfoLog(vshader))
        
        fshader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fshader, fragment_source)
        glCompileShader(fshader)
        glAttachShader(program, fshader)
        print(glGetShaderInfoLog(fshader))
        
        glLinkProgram(program)
        print(glGetProgramInfoLog(program))   
