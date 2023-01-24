#version 430

#define antialias 0.08
#define line_width 0.002
#define align_x_left 1
#define align_x_centre 2
#define align_x_right 3
#define align_y_top 1
#define align_y_middle 2
#define align_y_bottom 3
    
#ifdef shadertoy
#define NUM_DEBUG_WIDGETS 128
vec4 WidgetSizePosition[NUM_DEBUG_WIDGETS];
vec2 WidgetParentPosition[NUM_DEBUG_WIDGETS];
int WidgetAlign[NUM_DEBUG_WIDGETS];
int WidgetHoverId;
int WidgetSelectedId;
int AlignHoverId;
#else
in vec2 OutTexCoord;
out vec4 outColour;

uniform vec4 Colour;
uniform float DisplayRatio;
uniform vec4 WidgetSizePosition[NUM_DEBUG_WIDGETS];
uniform vec2 WidgetParentPosition[NUM_DEBUG_WIDGETS];
uniform int WidgetAlign[NUM_DEBUG_WIDGETS];
uniform int WidgetHoverId;
uniform int WidgetSelectedId;
uniform int AlignHoverId;
#endif

float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
{
    vec2 disRec = abs(uv - center) - wh * 0.5;
    float dis = max(disRec.x, disRec.y);
    return clamp(float(dis < 0.0), 0.0, 1.0);
}

float drawHollowRect(in vec2 uv, in vec2 center, in vec2 wh, in vec2 thickness)
{
    return drawRect(uv, center, wh) - drawRect(uv, center, wh - thickness);
}

float distanceToSegment(vec2 a, vec2 b, vec2 p)
{
    vec2 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    return length( pa - ba*h );
}

float drawLineRounded(in vec2 uv, in vec2 start, in vec2 end, in float width)
{
    return mix(0.0, 1.0, 1.0-smoothstep(width-antialias*0.02,width, distanceToSegment(start, end, uv)));
}

float drawLineSquare(in vec2 uv, in vec2 start, in vec2 end, in float width, bool vertical)
{
    float col = drawLineRounded(uv, start, end, width);
    vec2 clip_box = vec2(0.015, width * 4.0);
    float leftBox = drawRect(uv, start + vec2(clip_box.x * -0.5, 0.0), clip_box);
    float rightBox = drawRect(uv, end + vec2(clip_box.x * 0.5, 0.0), clip_box);
    if (vertical)
    {
        clip_box = vec2(width * 4.0, 0.02);
        leftBox = drawRect(uv, start, clip_box);
        rightBox = drawRect(uv, end, clip_box);
    }
    col -= leftBox + rightBox;
    return clamp(col, 0.0, 1.0);
}

vec4 drawWidget(in float ratio, in vec2 uv, in bool show_align, in vec2 anchor, in vec2 size, in vec2 offset, in int align, in int align_to)
{
    vec4 col = vec4(0.0);
    vec2 thickness = vec2(line_width, line_width / ratio);
    size = abs(size);
    vec2 hsize = size * -0.5;
    
    // Outline in white
    vec2 shader_pos = (offset + 1.0) * 0.5;
#ifndef shadertoy
    shader_pos.y = 1.0 - shader_pos.y;
    size *= 0.5;
    hsize = size * 0.5;
#endif
    col += drawHollowRect(uv, shader_pos, size, thickness);
    
    if (show_align)
    {
        // Aligment in red with pink for hover or aligned
        vec2 anchor_size = vec2(0.02, 0.02 / ratio);
        int align_x =  align / 10;
        int align_y = align - (align_x * 10);
        vec4 elem_col = vec4(0.5, 0.1, 0.08, 0.75);
        vec4 elem_col_sel = elem_col + vec4(0.4, 0.12, 0.8, 0.25);
        
        // 9 anchors in red with hover/selected in pink
        vec2 a_pos = vec2(0.0);
        vec2 hsize = size * 0.5;
        int a_x[9] = int[](1,1,1,2,2,2,3,3,3);
        int a_y[9] = int[](1,2,3,1,2,3,1,2,3);
        for (int i = 0; i < 9; i++)
        {
            if (a_x[i] == 1 && a_y[i] == 1) { a_pos = vec2(-hsize.x, hsize.y); }
            else if (a_x[i] == 1 && a_y[i] == 2) { a_pos = vec2(-hsize.x, 0.0); }
            else if (a_x[i] == 1 && a_y[i] == 3) { a_pos = vec2(-hsize.x, -hsize.y); }
            else if (a_x[i] == 2 && a_y[i] == 1) { a_pos = vec2(0.0, hsize.y); }
            else if (a_x[i] == 2 && a_y[i] == 3) { a_pos = vec2(0.0, -hsize.y); }
            else if (a_x[i] == 3 && a_y[i] == 1) { a_pos = vec2(hsize.x, hsize.y); }
            else if (a_x[i] == 3 && a_y[i] == 2) { a_pos = vec2(hsize.x, 0.0); }
            else if (a_x[i] == 3 && a_y[i] == 3) { a_pos = vec2(hsize.x, -hsize.y); }  

            bool sel = align_x == a_x[i] && align_y == a_y[i];
            col += (sel ? elem_col_sel : elem_col) * drawHollowRect(uv, shader_pos + a_pos, anchor_size, thickness);
        }

        // Anchor in blue
        vec2 anchor_pos = (anchor + 1.0) * 0.5;
        col += elem_col * drawHollowRect(uv, anchor_pos, anchor_size, thickness);
        col += elem_col * drawLineRounded(uv, anchor_pos, shader_pos + a_pos, line_width);
    }
    return col;
}

vec4 drawWidgets(in float ratio, in vec2 uv)
{
    vec4 col = vec4(0.0);
    for (int i = 0; i < NUM_DEBUG_WIDGETS; ++i)
    {
        if (WidgetAlign[i] > 0)
        {
            bool selected = i == WidgetSelectedId;
            int selected_id = selected ? 1 : 0;
            vec4 widget = drawWidget(ratio, uv, selected, WidgetParentPosition[i], WidgetSizePosition[i].xy, WidgetSizePosition[i].zw, AlignHoverId > 0 ? AlignHoverId : WidgetAlign[i], 0);
            widget.a = selected ? 1.0 : i == WidgetHoverId ? 0.75 : 0.5;
            col += widget;
        }
    }
    return col;
}

#ifdef shadertoy
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    float DisplayRatio = 1.0 / (iResolution.x / iResolution.y);
    vec2 uv = fragCoord/iResolution.xy;
    vec4 col = vec4(1.0, 1.0, 1.0, 1.0);
#else
void main()
{
    vec2 uv = OutTexCoord;
    vec4 col = Colour;
#endif    

#ifdef shadertoy
    vec4 bg = texture(iChannel0, uv);
    
    int w_id = 0;
    WidgetSizePosition[w_id] = vec4(0.35, 0.55, 0.05, 0.075);
    WidgetParentPosition[w_id] = vec2(0.1, 0.21);
    WidgetAlign[w_id] = 22;
    outColour = drawWidgets(DisplayRatio, uv);
    fragColor = outColour + bg;
#else
    outColour = drawWidgets(DisplayRatio, uv);
    outColour.a = col.a;
#endif
}