#version 430

in vec2 OutTexCoord;
uniform int AnimType;
uniform float AnimVal;
uniform float Time;
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;

// AnimTypes match animation.AnimType
#define at_fade_in 1
#define at_fade_out 2
#define at_pulse 3
#define at_in_out_smooth 4
#define at_rotate 5
#define at_throb 6
#define at_scroll 7
#define at_scroll_h 8
#define at_scroll_v 9

void main() 
{
    vec2 uv = OutTexCoord;
    vec4 col = Colour;
    if (AnimType == at_fade_in || AnimType == at_fade_out ||
        AnimType == at_pulse ||
        AnimType == at_in_out_smooth)
    {
        col.a * AnimVal;
    }
    else if (AnimType == at_scroll) 
    {
        uv += vec2(Time*0.05, Time*0.05);
    }
    outColour = texture(SamplerTex, uv) * col;
}