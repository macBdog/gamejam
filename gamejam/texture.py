from copy import copy
from dataclasses import dataclass
from OpenGL.GL import *
import os.path
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Dict, List

from gamejam.coord import Coord2d
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.quickmaff import MATRIX_IDENTITY


class Texture:
    """Encapsulates the resources required to render a image data with it's own
    image resources mapped onto it. Keeps hold of the image data and the
    ID represetnation in OpenGL."""
    FILE_EXTENSIONS = [ ".png", ".jpg", ".tga" ]

    @staticmethod
    def get_random_pixel():
        return [np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255)]


    @staticmethod
    def get_random_texture(width:int, height:int) -> np.array:
        tex = []
        for _ in range(width * height):
            tex += Texture.get_random_pixel()
        return np.array(tex)


    @staticmethod
    def create_buffers(graphics):
        # Create array object
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        # Create Buffer object in gpu
        vbo = glGenBuffers(1)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, 64, Graphics.DEFAULT_RECTANGLE, GL_STATIC_DRAW)

        # Create EBO
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 24, graphics.default_indices, GL_STATIC_DRAW)

        return vao, vbo, ebo


    def __init__(self, texture_path: str, default_width:int=32, default_height:int=32, wrap:bool=True):
        if os.path.exists(texture_path):
            self.image = Image.open(texture_path)
            self.width = self.image.width
            self.height = self.image.height
            self.img_data = np.array(list(self.image.getdata()), np.uint8)
        else:
            self.img_data = Texture.get_random_texture(default_width, default_height)
            self.width = default_width
            self.height = default_height
        self.texture_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        if wrap:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.img_data)


class Sprite:
    def __init__(self, graphics: Graphics, colour: list, pos: Coord2d, size: Coord2d):
        self.graphics = graphics
        self.pos = pos
        self.colour = colour[:]
        self.object_mat = MATRIX_IDENTITY[:]
        self.size = size

    def set_alpha(self, new_alpha: float):
        self.colour[3] = new_alpha

    def set_colour(self, new_colour: list):
        self.colour = new_colour[:]


class SpriteShape(Sprite):
    def __init__(self, graphics: Graphics, colour: list, pos: Coord2d, size: Coord2d, shader=None):
        Sprite.__init__(self, graphics, colour, pos, size)

        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)
        self.rectangle = np.array([-0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, 0.5], dtype=np.float32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 32, self.rectangle, GL_STATIC_DRAW)

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 24, self.graphics.default_indices, GL_STATIC_DRAW)

        self.shader = self.graphics.get_program(Shader.COLOUR) if shader is None else shader

        self.vertex_pos_id = glGetAttribLocation(self.shader, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)

        self.colour_id = glGetUniformLocation(self.shader, "Colour")
        self.pos_id = glGetUniformLocation(self.shader, "Position")
        self.size_id = glGetUniformLocation(self.shader, "Size")
        self.object_mat_id = glGetUniformLocation(self.shader, "ObjectMatrix")
        self.view_mat_id = glGetUniformLocation(self.shader, "ViewMatrix")
        self.projection_mat = glGetUniformLocation(self.shader, "ProjectionMatrix")


    def draw(self, custom_uniforms_func=None):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.object_mat_id, 1, GL_TRUE, self.object_mat)
        glUniformMatrix4fv(self.view_mat_id, 1, GL_TRUE, self.graphics.camera.mat)
        glUniformMatrix4fv(self.projection_mat, 1, GL_TRUE, self.graphics.projection_mat)
        glUniform4f(self.colour_id, self.colour[0], self.colour[1], self.colour[2], self.colour[3])
        glUniform2f(self.pos_id, self.pos.x, self.pos.y)
        glUniform2f(self.size_id, self.size.x, self.size.y)
        if custom_uniforms_func is not None:
            custom_uniforms_func()
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


class SpriteTexture(Sprite):
    def __init__(self, graphics: Graphics, tex: Texture, colour: list, pos: Coord2d, size: Coord2d, shader=None):
        Sprite.__init__(self, graphics, colour, pos, size)
        self.texture = tex
        self.bind(shader)


    def bind(self, shader=None):
        self.shader = self.graphics.get_program(Shader.TEXTURE) if shader is None else shader

        self.VAO, self.VBO, self.EBO = Texture.create_buffers(self.graphics)

        self.vertex_pos_id = glGetAttribLocation(self.shader, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)

        self.tex_coord_id = glGetAttribLocation(self.shader, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)

        self.colour_id = glGetUniformLocation(self.shader, "Colour")
        self.pos_id = glGetUniformLocation(self.shader, "Position")
        self.size_id = glGetUniformLocation(self.shader, "Size")
        self.object_mat_id = glGetUniformLocation(self.shader, "ObjectMatrix")
        self.view_mat_id = glGetUniformLocation(self.shader, "ViewMatrix")
        self.projection_mat = glGetUniformLocation(self.shader, "ProjectionMatrix")


    def draw(self, custom_uniforms_func=None):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.object_mat_id, 1, GL_TRUE, self.object_mat)
        glUniformMatrix4fv(self.view_mat_id, 1, GL_TRUE, self.graphics.camera.mat)
        glUniformMatrix4fv(self.projection_mat, 1, GL_TRUE, self.graphics.projection_mat)
        glUniform4f(self.colour_id, self.colour[0], self.colour[1], self.colour[2], self.colour[3])
        glUniform2f(self.pos_id, self.pos.x, self.pos.y)
        glUniform2f(self.size_id, self.size.x, self.size.y)
        if custom_uniforms_func is not None:
            custom_uniforms_func()
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.texture_id)
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


@dataclass(init=True)
class TextureAtlasItem:
    name: str
    size: Coord2d
    pos: Coord2d


@dataclass(init=True)
class TextureAtlasDraw:
    item: TextureAtlasItem
    size: Coord2d
    pos: Coord2d
    col: list


class TextureAtlas:
    """A texture atlas is a composite of multiple textures into one larger composite. 
    The orignal textures can be accessed and drawn by name."""
    MaxItems = 64
    MaxDraws = 512
    def __init__(self, graphics: Graphics, default_width:int=4096, default_height:int=4096):
        self.graphics = graphics
        self.img_data = np.zeros(4 * default_width * default_height, dtype=np.uint8)
        self.size = Coord2d(default_width, default_height)
        self.texture_id = glGenTextures(1)
        self.texture_items: Dict[TextureAtlasItem] = {}
        self.texture_draws: List[TextureAtlasDraw] = []

        self._sentinel = Coord2d()

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.size.x, self.size.y, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.img_data)

        self.object_mat = MATRIX_IDENTITY[:]

        shader_substitutes = {
            "MAX_ATLAS_ITEMS": TextureAtlas.MaxItems,
            "MAX_ATLAS_DRAWS": TextureAtlas.MaxDraws,
        }

        atlas_shader = Graphics.process_shader_source(graphics.builtin_shader(Shader.TEXTURE_ATLAS, ShaderType.PIXEL), shader_substitutes)
        self.shader = Graphics.create_program(graphics.builtin_shader(Shader.TEXTURE_ATLAS, ShaderType.VERTEX), atlas_shader)
        self.graphics.set_program(Shader.TEXTURE_ATLAS, self.shader)

        # Setup buffers with indices for drawing MaxDraws number of rectangles every call
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        self.atlas_verts = np.zeros(16 * TextureAtlas.MaxDraws, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, TextureAtlas.MaxDraws * 64, self.atlas_verts, GL_DYNAMIC_DRAW)

        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        multi_rect_indices = np.array([0, 1, 2, 2, 3, 0] * TextureAtlas.MaxDraws, dtype=np.uint32)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 24 * TextureAtlas.MaxDraws, multi_rect_indices, GL_STATIC_DRAW)

        self.VAO, self.VBO, self.EBO = Texture.create_buffers(self.graphics)

        self.object_mat_id = glGetUniformLocation(self.shader, "ObjectMatrix")
        self.view_mat_id = glGetUniformLocation(self.shader, "ViewMatrix")
        self.projection_mat = glGetUniformLocation(self.shader, "ProjectionMatrix")
        self.vertex_pos_id = glGetAttribLocation(self.shader, "VertexPosition")
        """uniform vec2 DrawPositions;
        uniform vec2 DrawSizes;
        uniform vec4 DrawColours;
        uniform int DrawIndices;
        uniform vec2 ItemPositions;
        uniform vec2 ItemSizes;"""
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)

        self.tex_coord_id = glGetAttribLocation(self.shader, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)


    def add(self, texture_path: Path, name: str=None) -> str:
        """Composite a texture into the atlas an add it to the dictionary of textures."""
        if texture_path.exists():
            image = Image.open(texture_path)
            size = Coord2d(image.width, image.height)

            if name is not None and name not in self.texture_items:
                self.name = name
            else:
                name = texture_path.stem

            avail = self.size - self._sentinel - size
            if avail.x >= size.x:
                if avail.y < size.y:
                    self._sentinel += Coord2d(0.0, size.y - avail.y)

                if avail.y >= size.y:
                    img_data = np.array(list(image.getdata()), np.uint8)
                    pos = copy(self._sentinel)
                    self._sentinel += size
                    self.texture_items[name] = TextureAtlasItem(name, size, pos)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, size.x, size.y, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)


    def draw(self, name, pos: Coord2d, size: Coord2d, col: list):
        self.texture_draws.append(TextureAtlasDraw(self.texture_items[name], pos, size, col))


    def draw_final(self):
        glUseProgram(self.shader)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.VAO)
        for draw in self.texture_draws:
            glUniform4f(self.colour_id, draw.col[0], draw.col[1], draw.col[2], draw.col[3])
            glUniform2f(self.pos_id, draw.pos.x, draw.pos.y)
            glUniform2f(self.size_id, draw.size.x, draw.size.y) 
            glUniform2f(self.tex_coord_id, draw.item.pos.x, draw.item.pos.y) 
            glUniform2f(self.char_size_id, draw.item.size.x, draw.item.size.y)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


class SpriteAtlasTexture(Sprite):
    def __init__(self, graphics: Graphics, atlas: TextureAtlas, name: str, colour: list, pos: Coord2d, size: Coord2d, shader=None):
        Sprite.__init__(self, graphics, colour, pos, size)
        self.atlas = atlas
        self.name = name

    def draw(self):
        self.atlas.draw(self.name, self.pos, self.size, self.colour)


class TextureManager:
    """The textures class handles loading and management of all image resources for the game.
    The idea is that textures are loaded on demand and stay loaded until explicitly unloaded
    or the game is shutdown."""

    def __init__(self, base: Path, graphics):
        self.base_path = Path(base)
        self.graphics = graphics
        self.raw_textures = {}
        self.atlas = TextureAtlas(graphics)

        textures = [f for f in self.base_path.iterdir() if str(f)[str(f).rfind('.'):].lower() in Texture.FILE_EXTENSIONS]
        for tex in textures:
            self.atlas.add(tex)


    def get_raw(self, texture_name: str, wrap:bool=True) -> SpriteTexture:
        if texture_name in self.raw_textures:
            return self.raw_textures[texture_name]
        else:
            texture_path = os.path.join(self.base_path, texture_name)
            new_texture = Texture(texture_path, wrap=wrap)
            self.raw_textures[texture_name] = new_texture
            return new_texture


    def create_sprite_shape(self, colour: list, pos: Coord2d, size: Coord2d, shader=None):
        return SpriteShape(self.graphics, colour, pos, size, shader)


    def create_sprite_texture(self, texture_name: str, pos: Coord2d, size: Coord2d, shader=None, wrap:bool=True):
        return SpriteTexture(self.graphics, self.get_raw(texture_name, wrap=wrap), [1.0] * 4, pos, size, shader)


    def create_sprite_texture_tinted(self, name: str, colour: list, pos: Coord2d, size: Coord2d, shader=None, wrap:bool=True):
        return SpriteTexture(self.graphics, self.get_raw(texture_name, wrap=wrap), name, colour, pos, size)


    def create_sprite_atlas_texture(self, name: str, pos: Coord2d, size: Coord2d):
        return SpriteAtlasTexture(self.graphics, self.atlas, name, [1.0] * 4, pos, size)
