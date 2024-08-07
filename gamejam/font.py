from copy import copy
import glfw
import numpy as np
from pathlib import Path
from freetype import Face, ctypes
from OpenGL.GL import (
    glGenBuffers, glBindBuffer, glBufferData,
    glGenTextures, glBindTexture, glActiveTexture,
    glTexImage2D, glTexParameteri,
    glGenVertexArrays,
    glUseProgram,
    glBindVertexArray,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glGetAttribLocation,
    glGetUniformLocation,
    glUniformMatrix4fv,
    glUniform2f, glUniform4f,
    glDrawElements,
    GL_TEXTURE_2D, GL_TEXTURE0,
    GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T,
    GL_CLAMP_TO_EDGE,
    GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
    GL_LINEAR, GL_TRUE,
    GL_R8, GL_RED, GL_FLOAT, GL_UNSIGNED_INT, GL_UNSIGNED_BYTE, GL_FALSE,
    GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_TRIANGLES
)

from gamejam.graphics import Graphics, Shader
from gamejam.settings import GameSettings
from gamejam.coord import Coord2d
from gamejam.quickmaff import MATRIX_IDENTITY

class Font():
    def __init__(self, graphics: Graphics, window, filename: str=None):
        self.graphics = graphics
        if filename is None:
            self.filename = Path(__file__).parent / "res" / "consola.ttf"
        else:
            self.filename = filename
        self.face = Face(str(self.filename))
        self.face.set_char_size(9000)
        self.sizes = {}
        self.positions = {}
        self.advance = {}
        self.offsets = {}
        self.bearings = {}
        self.char_start = 32
        self.char_end = 127
        self.special_chars = ['½']
        self.num_chars = (self.char_end - self.char_start) + len(self.special_chars)
        window_size = glfw.get_framebuffer_size(window)
        self.window_ratio = window_size[0] / window_size[1]
        self.line_height = 10000.0

        # Create one big texture for all the glyphs
        self.tex_width = 2048
        self.tex_height = 2048
        self.image_data = np.zeros((self.tex_width, self.tex_height), dtype=np.uint8)
        self.object_mat = MATRIX_IDENTITY

        if GameSettings.DEV_MODE:
            print(f"Building font atlas for {self.filename}: ", end='')

        # Blit font chars into the texture noting the individual char size and tex coords
        atlas_pos = (0, 0)        
        self.largest_glyph_height = 0
        
        all_chars = []
        for c in range(self.char_start, self.char_end):
            all_chars.append(chr(c))

        for _, c in enumerate(self.special_chars):
            all_chars.append(c)
        
        for _, char in enumerate(all_chars):
            c = ord(char)
            self.face.load_char(char)
            atlas_pos = self.blit_char(self.image_data, self.face.glyph, atlas_pos, c)
            self.advance[c] = self.face.glyph.advance.x
            bbox = self.face.glyph.outline.get_bbox()
            self.offsets[c] = (bbox.xMax - bbox.xMin, bbox.yMax - bbox.yMin)
            metrics = self.face.glyph.metrics
            self.bearings[c] = (metrics.horiBearingX, metrics.horiBearingY)

            if c == 32:
                self.line_height = self.face.height * 2.75

            if GameSettings.DEV_MODE:
                print(chr(c), end='')

        if GameSettings.DEV_MODE:
            print(' OK!')

        # Generate texture data
        self.image_data_texture = self.image_data.flatten()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, self.tex_width, self.tex_height, 0, GL_RED, GL_UNSIGNED_BYTE, self.image_data_texture)
        
        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)
        self.rectangle = np.array([-0.5, -0.5, 
                                       0.5, -0.5, 
                                       0.5, 0.5, 
                                      -0.5, 0.5, 0.0, 1.0, 1.0, 1.0,1.0, 0.0, 0.0, 0.0], dtype = np.float32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 64, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 24, self.graphics.default_indices, GL_STATIC_DRAW)

        shader_font = graphics.get_program(Shader.FONT)
        self.vertex_pos_id = glGetAttribLocation(shader_font, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)
 
        self.tex_coord_id = glGetAttribLocation(shader_font, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)
 
        self.char_coord_id = glGetUniformLocation(shader_font, "CharCoord")
        self.char_size_id = glGetUniformLocation(shader_font, "CharSize")
        self.colour_id = glGetUniformLocation(shader_font, "Colour")
        self.pos_id = glGetUniformLocation(shader_font, "Position")
        self.size_id = glGetUniformLocation(shader_font, "Size")
        self.object_mat_id = glGetUniformLocation(shader_font, "ObjectMatrix")
        self.view_mat_id = glGetUniformLocation(shader_font, "ViewMatrix")
        self.projection_mat = glGetUniformLocation(shader_font, "ProjectionMatrix")


    def blit(self, dest, src, loc):
        pos = [i if i >= 0 else None for i in loc]
        neg = [-i if i < 0 else None for i in loc]
        target = dest[tuple([slice(i,None) for i in pos])]

        src = src[tuple([slice(i, j) for i,j in zip(neg, target.shape)])]
        target[tuple([slice(None, i) for i in src.shape])] = src
        return dest


    def blit_char(self, dest, glyph, loc, char_index: int):
        bitmap = glyph.bitmap
        width  = bitmap.rows
        height = bitmap.width

        if width <= 0 or height <= 0:
            return loc

        if height > self.largest_glyph_height:
            self.largest_glyph_height = height

        if loc[0] + width >= self.tex_width:
            loc = (0, loc[1] + self.largest_glyph_height)

        if loc[0] > self.tex_width or loc[1] > self.tex_width:
            print(f"Font atlas not large enough for all characters!")
            return loc
            
        src = np.reshape(bitmap.buffer, (width, height))
        self.blit(dest, src, loc)

        self.sizes[char_index] = (height / self.tex_width, width / self.tex_height)
        self.positions[char_index] = (loc[1] / self.tex_height, loc[0] / self.tex_width)
        return (loc[0] + width, loc[1])


    def get_line_display_height(self, font_size: int):
        display_size = font_size * 0.0000005
        return self.line_height * display_size


    def draw(self, string: str, font_size: int, pos: Coord2d, colour: list) -> Coord2d:
        """ Draw a string of text with the bottom left of the first glyph at the pos coordinate."""
        shader_font = self.graphics.get_program(Shader.FONT)
        glUseProgram(shader_font)
        glUniform4f(self.colour_id, colour[0], colour[1], colour[2], colour[3]) 
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.VAO)
        glUniformMatrix4fv(self.object_mat_id, 1, GL_TRUE, self.object_mat)
        glUniformMatrix4fv(self.view_mat_id, 1, GL_TRUE, self.graphics.camera.mat)
        glUniformMatrix4fv(self.projection_mat, 1, GL_TRUE, self.graphics.projection_mat)
        draw_pos, display_size = copy(pos), font_size * 0.0000005

        for i in range(len(string)):
            c = ord(string[i])

            # Special case for unsupported or whitespace characters
            if c not in self.sizes:
                if c == 13 or c == 10:
                    draw_pos.x = pos.x
                    draw_pos.y = pos.y - self.line_height * display_size
                else:
                    draw_pos.x = draw_pos.x + (self.advance[32] * display_size) / self.window_ratio
                continue

            # Size and position in texture
            tex_coord, tex_size = self.positions[c], self.sizes[c]

            # Size and position of glyph
            offset = self.offsets[c]
            bearing = ((self.bearings[c][0] * display_size) / self.window_ratio, self.bearings[c][1] * display_size)
            char_size = (offset[0] * display_size, offset[1] * display_size)
            char_pos = (draw_pos.x + bearing[0] + (char_size[0] * 0.5), draw_pos.y + bearing[1] - (char_size[1] * 0.5))

            glUniform4f(self.colour_id, colour[0], colour[1], colour[2], colour[3])
            glUniform2f(self.pos_id, char_pos[0], char_pos[1])
            glUniform2f(self.size_id, char_size[0] / self.window_ratio, char_size[1]) 
            glUniform2f(self.char_coord_id, tex_coord[0], tex_coord[1]) 
            glUniform2f(self.char_size_id, tex_size[0], tex_size[1])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

            draw_pos.x = draw_pos.x + ((self.advance[c] * display_size) / self.window_ratio)

        text_dim = draw_pos - pos
        text_dim.y = max(abs(text_dim.y), self.line_height * display_size)
        return text_dim
