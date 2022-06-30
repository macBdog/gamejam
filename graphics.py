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
    TEXTURE_ANIM = auto()
    COLOUR = auto()
    FONT = auto()
    PARTICLES = auto()

class ShaderType(Enum):
    VERTEX = 0
    PIXEL = auto()

class Graphics:
    SHADER_PATH = "shaders"
    

    def __init__(self):
        self.shaders = {}
        self.indices = numpy.array([0, 1, 2, 2, 3, 0], dtype=numpy.uint32)

        # Pre-compile multiple shaders for general purpose drawing
        self.shader_texture = compileProgram(
            compileShader(self.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.TEXTURE, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )

        self.shader_colour = compileProgram(
            compileShader(self.builtin_shader(Shader.COLOUR, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.COLOUR, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )

        self.shader_font = compileProgram(
            compileShader(self.builtin_shader(Shader.FONT, ShaderType.VERTEX), GL_VERTEX_SHADER), 
            compileShader(self.builtin_shader(Shader.FONT, ShaderType.PIXEL), GL_FRAGMENT_SHADER)
        )


    @staticmethod
    def get_shader_name(shader: Shader, type: ShaderType) -> str:
        return f"{shader._name_.lower()}.{'vert' if type is ShaderType.VERTEX else 'frag'}"


    def builtin_shader(self, shader: Shader, type: ShaderType) -> str:
        name = Graphics.get_shader_name(shader, type)
        if name not in self.shaders:
            path = Path(__file__).parent / Graphics.SHADER_PATH / name
            with open(path, 'r') as shader_file:
                self.shaders[name] = shader_file.read()
        return self.shaders[name]


    @staticmethod
    def create_shader(vertex_shader_source: str, pixel_shader_source: str):
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
