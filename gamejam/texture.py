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
from gamejam.settings import GameSettings
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
    index: int

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
    MaxDraws = 128
    def __init__(self, graphics: Graphics, default_width:int=4096, default_height:int=4096):
        self.graphics = graphics
        self.size = Coord2d(default_width, default_height)
        self.img_data = np.zeros(4 * self.size.x * self.size.y, dtype=np.uint8)

        self.debug_atlas = False
        if self.debug_atlas:
            fg_shape = Coord2d(int(self.size.x / 2), int(self.size.y))
            fg_col = np.array([255, 0, 0, 255], dtype=np.uint8)
            debug_img_data = np.full((fg_shape.x, fg_shape.y, 4), fg_col, dtype=np.uint8)
            TextureAtlas.blit(self.img_data, self.size, debug_img_data, fg_shape, Coord2d(0.0, 0.0))

        self.texture_id = glGenTextures(1)

        self.texture_items: Dict[TextureAtlasItem] = {}
        self.item_pos = np.zeros(TextureAtlas.MaxDraws * 2, dtype=np.float32)
        self.item_size = np.zeros(TextureAtlas.MaxDraws * 2, dtype=np.float32)

        self.texture_draw_count = 0
        self.draw_index = np.zeros(TextureAtlas.MaxDraws, dtype=np.int32)
        self.draw_index.fill(-1)
        self.draw_pos = np.zeros(TextureAtlas.MaxDraws * 2, dtype=np.float32)
        self.draw_size = np.zeros(TextureAtlas.MaxDraws * 2, dtype=np.float32)
        self.draw_col = np.zeros(TextureAtlas.MaxDraws * 4, dtype=np.float32)

        self._next_pos = Coord2d()
        self._next_largest = 0.0

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

        self.VAO, self.VBO, self.EBO = Texture.create_buffers(self.graphics)

        self.vertex_pos_id = glGetAttribLocation(self.shader, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)

        self.tex_coord_id = glGetAttribLocation(self.shader, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)

        self.pos_id = glGetUniformLocation(self.shader, "Position")
        self.size_id = glGetUniformLocation(self.shader, "Size")
        self.object_mat_id = glGetUniformLocation(self.shader, "ObjectMatrix")
        self.view_mat_id = glGetUniformLocation(self.shader, "ViewMatrix")
        self.projection_mat = glGetUniformLocation(self.shader, "ProjectionMatrix")

        self.draw_index_id = glGetUniformLocation(self.shader, "DrawIndices")
        self.draw_pos_id = glGetUniformLocation(self.shader, "DrawPositions")
        self.draw_size_id = glGetUniformLocation(self.shader, "DrawSizes")
        self.draw_col_id = glGetUniformLocation(self.shader, "DrawColours")
        self.item_pos_id = glGetUniformLocation(self.shader, "ItemPositions")
        self.item_size_id = glGetUniformLocation(self.shader, "ItemSizes")

        # Also bind a debug shader for drawing the complete atlas
        self.debug_shader = self.graphics.get_program(Shader.TEXTURE)
        self.debug_colour_id = glGetUniformLocation(self.debug_shader, "Colour")
        self.debug_pos_id = glGetUniformLocation(self.debug_shader, "Position")
        self.debug_size_id = glGetUniformLocation(self.debug_shader, "Size")
        self.debug_object_mat_id = glGetUniformLocation(self.debug_shader, "ObjectMatrix")
        self.debug_view_mat_id = glGetUniformLocation(self.debug_shader, "ViewMatrix")
        self.debug_projection_mat = glGetUniformLocation(self.debug_shader, "ProjectionMatrix")

    @staticmethod
    def blit(dst_image, dst_size: Coord2d, src_image, src_size: Coord2d, pos: Coord2d):
        dst = np.reshape(dst_image, (dst_size.x, dst_size.y, 4), order="A")
        src = np.reshape(src_image, (src_size.x, src_size.y, 4), order="F")
        src = np.flip(src, axis=0)
        dst[int(pos.x):int(pos.x + src_size.x), int(pos.y):int(pos.y + src_size.y)] = src
        return dst.reshape((4 * dst_size.x * dst_size.y), order="A")

    def add(self, texture_path: Path, name: str=None) -> str:
        """Composite a texture into the atlas an add it to the dictionary of textures."""

        if texture_path.exists():
            tex = Image.open(texture_path)
            size = Coord2d(tex.width, tex.height)

            if name is None:
                name = texture_path.stem

            avail = self.size - self._next_pos - size

            if avail.x < size.x:
                self._next_pos.x = 0
                self._next_pos.y += self._next_largest
                self._next_largest = 0
                avail = self.size - self._next_pos - size

            if avail.x >= size.x and avail.y >= size.y:
                tex_data = np.array(list(tex.getdata()), np.uint8)
                pos = copy(self._next_pos)

                # Add a new item to the list of items, writing the a sequence of items for the shader to lookup
                index = len(self.texture_items)
                self.texture_items[name] = TextureAtlasItem(name, size, pos, index)
                self.item_pos[index * 2] = pos.x / self.size.x
                self.item_pos[(index * 2) + 1] = pos.y / self.size.y
                self.item_size[index * 2] = size.x / self.size.x
                self.item_size[(index * 2) + 1] = size.y / self.size.y

                if not self.debug_atlas:
                    TextureAtlas.blit(self.img_data, self.size, tex_data, size, pos)

                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.size.x, self.size.y, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.img_data)
                self._next_pos.x += size.x
                if size.y > self._next_largest:
                    self._next_largest = size.y

    def draw(self, name, pos: Coord2d, size: Coord2d, col: list):
        draw_item = self.texture_items[name]
        i = draw_item.index
        n = self.texture_draw_count
        self.draw_index[n] = i
        self.draw_pos[(n * 2)] = pos.x
        self.draw_pos[(n * 2) + 1] = pos.y
        self.draw_size[(n * 2)] = size.x
        self.draw_size[(n * 2) + 1] = size.y
        self.draw_col[(n * 4)] = col[0]
        self.draw_col[(n * 4) + 1] = col[1]
        self.draw_col[(n * 4) + 2] = col[2]
        self.draw_col[(n * 4) + 3] = col[3]
        self.texture_draw_count += 1

    def draw_debug_atlas_item(self, item_index: int, pos: Coord2d, size: Coord2d):
        if item_index < 0:
            self.draw_index[0] = 0
            self.item_pos[0] = 0.0
            self.item_pos[1] = 0.0
            self.item_size[0] = 1.0
            self.item_size[1] = 1.0
        else:
            self.draw_index[0] = item_index

        self.draw_pos[0] = pos.x
        self.draw_pos[1] = pos.y
        self.draw_size[0] = size.x
        self.draw_size[1] = size.y
        self.draw_col[0] = 1.0
        self.draw_col[1] = 1.0
        self.draw_col[2] = 1.0
        self.draw_col[3] = 1.0
        self.texture_draw_count = 1

    def draw_final(self):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.object_mat_id, 1, GL_TRUE, MATRIX_IDENTITY[:])
        glUniformMatrix4fv(self.view_mat_id, 1, GL_TRUE, self.graphics.camera.mat)
        glUniformMatrix4fv(self.projection_mat, 1, GL_TRUE, self.graphics.projection_mat)
        glUniform2f(self.pos_id, 0.0, 0.0)
        glUniform2f(self.size_id, 2.0, 2.0)

        glUniform2fv(self.item_pos_id, TextureAtlas.MaxItems, self.item_pos)
        glUniform2fv(self.item_size_id, TextureAtlas.MaxItems, self.item_size)

        glUniform1iv(self.draw_index_id, TextureAtlas.MaxDraws, self.draw_index)
        glUniform2fv(self.draw_pos_id, TextureAtlas.MaxDraws, self.draw_pos)
        glUniform2fv(self.draw_size_id, TextureAtlas.MaxDraws, self.draw_size)
        glUniform4fv(self.draw_col_id, TextureAtlas.MaxDraws, self.draw_col)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        self.texture_draw_count = 0
        self.draw_index.fill(-1)

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

        textures = list()
        for e in Texture.FILE_EXTENSIONS:
            textures.extend(self.base_path.rglob(f"*{e}"))

        if GameSettings.DEV_MODE:
            print(f"Building atlas for {len(textures)} textures: ", end='')

        for tex in textures:
            if GameSettings.DEV_MODE:
                print(f"▓", end='')
            rel_name = str(tex.relative_to(self.base_path).as_posix())
            self.atlas.add(tex, name=rel_name)

        if GameSettings.DEV_MODE:
            print(' OK!')

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

    def create_sprite_texture(self, name: str, pos: Coord2d, size: Coord2d, shader=None, wrap:bool=True):
        return SpriteTexture(self.graphics, self.get_raw(name, wrap=wrap), [1.0] * 4, pos, size, shader)

    def create_sprite_texture_tinted(self, name: str, colour: list, pos: Coord2d, size: Coord2d, shader=None, wrap:bool=True):
        return SpriteTexture(self.graphics, self.get_raw(name, wrap=wrap), colour, pos, size, shader)

    def create_sprite_atlas_texture(self, name: str, pos: Coord2d, size: Coord2d, colour = [1.0, 1.0, 1.0, 1.0]):
        return SpriteAtlasTexture(self.graphics, self.atlas, name, colour, pos, size)

    def draw_debug_atlas(self):
        self.atlas.draw_debug_atlas_item(-1, Coord2d(0.0, 0.0), Coord2d(1.0, 1.0))

    def draw_debug_atlas_item(self, item_index: int, pos: Coord2d, size: Coord2d):
        self.atlas.draw_debug_atlas_item(item_index, pos, size)

    def draw_atlas(self):
        self.atlas.draw_final()
