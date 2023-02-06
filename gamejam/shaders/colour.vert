#version 430

in vec2 VertexPosition;
uniform vec2 Position;
uniform vec2 Size;
uniform mat4 ObjectMatrix;
uniform mat4 ViewMatrix;
uniform mat4 ProjectionMatrix;
void main() 
{
    vec4 Pos = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
    gl_Position = ProjectionMatrix * ViewMatrix * ObjectMatrix * Pos;
}