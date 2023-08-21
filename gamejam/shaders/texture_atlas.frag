#version 430

in vec2 OutTexCoord;
out vec4 outColour;

uniform sampler2D SamplerTex;
uniform vec4 Colour;

uniform vec2 DrawPositions[MAX_ATLAS_DRAWS];
uniform vec2 DrawSizes[MAX_ATLAS_DRAWS];
uniform vec4 DrawColours[MAX_ATLAS_DRAWS];
uniform int DrawIndices[MAX_ATLAS_DRAWS];
uniform vec2 ItemPositions[MAX_ATLAS_ITEMS];
uniform vec2 ItemSizes[MAX_ATLAS_ITEMS];

void main() 
{
    for (int i = 0; i < MAX_ATLAS_DRAW; ++i)
    {
        vec2 draw_pos = 
        vec4 draw_col = DrawColours[i];
        char_col.a = texture(SamplerTex, OutTexCoord).r;
        outColour += char_col;
    }
}