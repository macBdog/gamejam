#version 430

in vec2 OutTexCoord;
uniform sampler2D SamplerTex;
out vec4 outColour;

uniform int DrawIndices[MAX_ATLAS_DRAWS];
uniform vec2 DrawPositions[MAX_ATLAS_DRAWS];
uniform vec2 DrawSizes[MAX_ATLAS_DRAWS];
uniform vec4 DrawColours[MAX_ATLAS_DRAWS];
uniform vec2 ItemPositions[MAX_ATLAS_ITEMS];
uniform vec2 ItemSizes[MAX_ATLAS_ITEMS];

float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
{
    vec2 disRec = abs(uv - center) - wh * 0.5;
    float dis = max(disRec.x, disRec.y);
    return clamp(float(dis < 0.0), 0.0, 1.0);
}

void main()
{
    outColour = vec4(0.0, 0.0, 0.0, 0.0);
    vec2 uv = OutTexCoord;

    for (int i = 0; i < MAX_ATLAS_DRAWS; ++i)
    {
        if (DrawIndices[i] < 0)
        {
            continue;
        }

        // First, lookup the item declaration
        vec2 item_size = ItemSizes[DrawIndices[i]];
        vec2 item_pos = ItemPositions[DrawIndices[i]];

        vec2 draw_pos = DrawPositions[i];
        draw_pos.y = -draw_pos.y;

        vec2 draw_size = DrawSizes[i];
        vec4 draw_col = DrawColours[i];

        // First get the uv's to be item relative
        vec2 item_uv = uv - (draw_pos * 0.5);
        
        // Then apply offset and scale
        vec2 draw_size_offset = (1.0 - draw_size) * -0.5;
        item_uv += draw_size_offset;
        item_uv *= (1.0 / draw_size);

        item_uv = vec2(item_uv.y, 1.0-item_uv.x);
        item_uv *= vec2(item_size.y, item_size.x);
        item_uv += vec2(item_pos.y, item_pos.x);

        draw_pos = (draw_pos + 1.0) * 0.5;
        outColour += drawRect(uv, draw_pos, draw_size) * texture(SamplerTex, item_uv) * draw_col;
    }
}