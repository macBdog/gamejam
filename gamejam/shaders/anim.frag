#version 430

#define PI 3.141529
#define TAU 6.28318

#ifndef shadertoy
in vec2 OutTexCoord;
uniform int Type;
uniform float Val;
uniform float Timer;
uniform float DisplayRatio;
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;
#endif

// Types match animation.AnimType
#define at_fade_in 1
#define at_fade_out 2
#define at_pulse 3
#define at_in_out_smooth 4
#define at_rotate 5
#define at_throb 6
#define at_scroll_h 7
#define at_scroll_v 8
#define at_fill_h 9
#define at_fill_v 10
#define at_fill_radial 11

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

#ifdef shadertoy
void mainImage( out vec4 fragColor, in vec2 fragCoord)
{
    int Type = setEffect(at_fade_in);
    Type = setEffect(Type, at_rotate);
    float Val = 1.0;
    float Timer = iTime - floor(iTime);
    float DisplayRatio = 1.0 / (iResolution.x / iResolution.y);
    vec2 uv = fragCoord/iResolution.xy;
    vec4 outColour;
    vec4 col = vec4(1.0, 1.0, 1.0, 1.0);
#else
void main()
{
    vec2 uv = OutTexCoord;
    vec4 col = Colour;
#endif

    // Multiple effects can be set at once
    if (hasEffect(Type, at_fade_in))
    {
        col.a = Timer / Val;
    }
    if (hasEffect(Type, at_fade_out))
    {
        col.a = 1.0 - (Timer/ Val);
    }
    if (hasEffect(Type, at_pulse))
    {
        col.a = (sin(Timer * PI) + 1.0) * 0.5;
    }
    if (hasEffect(Type, at_in_out_smooth))
    {
        float t = Timer / Val;
        col.a = (sin((t * PI * 2.0) - PI * 0.5) + 1.0) * 0.5;
    }
    if (hasEffect(Type, at_rotate))
    {
        float rx = sin(Timer * Val);
        float ry = cos(Timer * Val);
        uv = vec2((uv.x - 0.5) / DisplayRatio, uv.y - 1.5) * mat2(ry, rx, -rx, ry);
        uv.x += rx;
        uv.y += ry;
    }
    if (hasEffect(Type, at_throb))
    {
        float amount = (sin(Timer * PI) + 1.0) * 0.5;
        uv -= 0.5;
        uv *= 1.0 + amount;
        uv += 0.5;
    }
    if (hasEffect(Type, at_scroll_h))
    {
        uv.x += Timer * Val;
    }
    if (hasEffect(Type, at_scroll_v))
    {
        uv.y += Timer * Val;
    }
    if (hasEffect(Type, at_fill_h))
    {
        col *= uv.x > Timer * Val ? 0.333 : 1.0;
    }
    if (hasEffect(Type, at_fill_v))
    {
        col *= uv.y > Timer * Val ? 0.333 : 1.0;
    }
    if (hasEffect(Type, at_fill_radial))
    {
        float theta = TAU / (Timer / Val);
        vec2 ruv = vec2((uv.x - 0.5) / DisplayRatio, uv.y - 0.5);
        float a = atan(ruv.x, ruv.y);
        float b = TAU * 2.0  - atan(ruv.x, ruv.y);
        col *= b > theta ? 1.0 : 0.333;
    }
    
#ifdef shadertoy
    vec4 bg = texture(iChannel1, uv);
    outColour = texture(iChannel0, uv) * col;
    fragColor = mix(outColour, bg, col.a);
#else
    outColour = texture(SamplerTex, uv) * col;
#endif
}