#ifndef shadertoy
#version 430

in vec2 OutTexCoord;
uniform int AnimType;
uniform float AnimVal;
uniform float Timer;
uniform float DisplayRatio;
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;
#endif

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

bool hasEffect(const int Val, const int Effect)
{
    return (Val & (1 << Effect)) != 0;
}

int setEffect(const int Effect)
{
    return 1 << Effect;
}

int setEffect(int Val, const int Effect)
{
    return Val | (1 << Effect);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
#ifdef shadertoy
    int AnimType = setEffect(at_fade_in);
    AnimType = setEffect(AnimType, at_rotate);
    float AnimVal = 0.15;
    float Time = iTime - floor(iTime);
    float DisplayRatio = 1.0 / (iResolution.x / iResolution.y);
    vec2 uv = fragCoord/iResolution.xy;
    vec4 outColour;
    vec4 col = vec4(1.0, 1.0, 1.0, 1.0);
#else
    vec2 uv = OutTexCoord;
    vec4 col = Colour;
#endif

    // Multiple effects can be set at once
    if (hasEffect(AnimType, at_fade_in))
    {
        col.a = Time;
    }
    if (hasEffect(AnimType, at_fade_out))
    {
        col.a = 1.0 - Time;
    }
    if (hasEffect(AnimType, at_pulse))
    {
        col.a = (sin(Time) + 1.0) * 0.5;
    }
    if (hasEffect(AnimType, at_in_out_smooth))
    {
        float t = Time;
        col.a = t * t * (3.0 - 2.0 * t);
    }
    if (hasEffect(AnimType, at_rotate))
    {
        float rx = sin(Time * AnimVal);
        float ry = cos(Time * AnimVal);
        uv = vec2((uv.x - 0.5) / DisplayRatio, uv.y - 1.5) * mat2(ry, rx, -rx, ry);
        uv.x += rx;
        uv.y += ry;
    }
    if (hasEffect(AnimType, at_scroll_h) || hasEffect(AnimType, at_scroll))
    {
        uv.x += Time * AnimVal;
    }
    if (hasEffect(AnimType, at_scroll_v) || hasEffect(AnimType, at_scroll))
    {
        uv.y += Time * AnimVal;
    }
    
    
#ifdef shadertoy
    vec4 bg = texture(iChannel1, uv);
    outColour = texture(iChannel0, uv) * col;
    fragColor = mix(outColour, bg, col.a);
#else
    outColour = texture(SamplerTex, uv) * col;
#endif
}