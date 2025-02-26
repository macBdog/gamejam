#version 430

#define NO_TEXTURE_INDEX MAX_ATLAS_DRAWS + 1

#define BLEND_MAX 1
#define BLEND_MIN 2
#define BLEND_ALPHA_G 3
#define BLEND_ALPHA_GE 4
#define BLEND_ALPHA_L 5
#define BLEND_ALPHA_LE 6
#define BLEND_LAST 7
#define BLEND_FIRST 8

#define BLEND BLEND_LAST

in vec2 OutTexCoord;
uniform sampler2D SamplerTex;
out vec4 outColour;

uniform int DrawIndices[MAX_ATLAS_DRAWS];
uniform vec2 DrawPositions[MAX_ATLAS_DRAWS];
uniform vec2 DrawSizes[MAX_ATLAS_DRAWS];
uniform vec4 DrawColours[MAX_ATLAS_DRAWS];
uniform vec2 ItemPositions[MAX_ATLAS_ITEMS];
uniform vec2 ItemSizes[MAX_ATLAS_ITEMS];

vec4 blend(in vec4 a, in vec4 b) {
    if (BLEND == BLEND_MAX) {
        return max(a, b);
    } else if (BLEND == BLEND_MIN) {
        return min(a, b).a > 0.0 ? min(a, b) : a+b;
    } else if (BLEND == BLEND_ALPHA_G) {
        return a.a > b.a ? a : b;
    }  else if (BLEND == BLEND_ALPHA_GE) {
        return a.a >= b.a ? a : b;
    } else if (BLEND == BLEND_ALPHA_L) {
        return a.a < b.a ? a : b;
    } else if (BLEND == BLEND_ALPHA_LE) {
        return a.a <= b.a ? a : b;
    } else if (BLEND == BLEND_FIRST) {
        return a.a > 0.0 ? a : b;
    } else if (BLEND == BLEND_LAST) {
        return b.a > 0.0 ? b : a;
    }
    return a+b;
}

float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
{
    vec2 disRec = abs(uv - center) - wh * 0.5;
    float dis = max(disRec.x, disRec.y);
    return clamp(float(dis < 0.0), 0.0, 1.0);
}

void main()
{
    vec4 gui_col = vec4(0.0, 0.0, 0.0, 0.0);
    vec2 uv = OutTexCoord;

    for (int i = 0; i < MAX_ATLAS_DRAWS; ++i)
    {
        if (DrawIndices[i] < 0)
        {
            continue;
        }

        vec2 draw_pos = DrawPositions[i];
        draw_pos.y = -draw_pos.y;

        vec2 draw_size = DrawSizes[i] * 0.5;
        vec4 draw_col = DrawColours[i];

        vec4 item_col = vec4(1.0, 1.0, 1.0, 1.0);
        if (DrawIndices[i] != NO_TEXTURE_INDEX) {

            // First, lookup the item declaration
            vec2 item_size = ItemSizes[DrawIndices[i]];
            vec2 item_pos = ItemPositions[DrawIndices[i]];

            // First get the uv's to be item relative
            vec2 item_uv = uv - (draw_pos * 0.5);
            
            // Then apply offset and scale
            vec2 draw_size_offset = (1.0 - draw_size) * -0.5;
            item_uv += draw_size_offset;
            item_uv *= (1.0 / draw_size);

            // Normalize to GUI coords
            item_uv = vec2(item_uv.y, 1.0-item_uv.x);
            item_uv *= vec2(item_size.y, item_size.x);
            item_uv += vec2(item_pos.y, item_pos.x);

            item_col = texture(SamplerTex, item_uv);
        }

        draw_pos = (draw_pos + 1.0) * 0.5;

        vec4 prev_col = gui_col;
        gui_col = blend(prev_col, drawRect(uv, draw_pos, draw_size) * item_col * draw_col);
    }

    outColour = gui_col;
}