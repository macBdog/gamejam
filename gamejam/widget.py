from dataclasses import dataclass
from enum import Enum
import functools


class AlignX(Enum):
    Left = 1
    Centre = 2
    Right = 3


class AlignY(Enum):
    Top = 1
    Middle = 2
    Bottom = 3


@dataclass
class Alignment():
    align_x: AlignX
    align_y: AlignY


def widget_dirty(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args[0]._dirty = True
        return func(*args, **kwargs)
    return wrapper


class Widget():
    def __init__(self, name: str=None):
        # Draw pos automatically gets refreshed when the dirty flag is set
        self._dirty = True
        self._draw_pos = [0.0, 0.0]
        self.name = name if name is None else f"Widget-{hex(id(self))[6:]}"
        
        self._offset = [0.0, 0.0]
        self._size = [0.1, 0.1]

        # Where this widget is drawn relative to it's parent anchor
        self._align_x = AlignX.Centre
        self._align_y = AlignY.Middle

        # What part of the parent this widget positions relative to
        self._align_to_x = AlignX.Centre
        self._align_to_y = AlignY.Middle
        
        # Hierarchy
        self._parent = None
        self._children = []


    def draw(self, dt: float):
        """Apply any changes to the widget rect."""
        if self._dirty:
            self._draw_pos = Widget.calc_draw_pos(self._offset, self._size, self._align_x, self._align_y, self._align_to_x, self._align_to_y, self._parent)
            self._dirty = False

        for child in self._children:
            child.draw(dt)


    def add_child(self, child):
        if child not in self._children and child._parent == None:
            child._parent = self
            self._children.append(child)
        else:
            print(f"Error when adding child widget {child.name} to {self.name}! Widget {child.name} already has a parent and it's name is {child._parent.name}.")


    @widget_dirty
    def set_offset(self, offset: list):
        self._offset = offset


    @widget_dirty
    def set_size(self, size: list):
        self._size = size


    @widget_dirty
    def set_align(self, align_x: AlignX, align_y: AlignY):
        self._align_x = align_x
        self._align_y = align_y

    
    @widget_dirty
    def set_align_to(self, align_x: AlignX, align_y: AlignY):
        self._align_to_x = align_x
        self._align_to_y = align_y


    @widget_dirty
    def set_parent(self, parent: any):
        if parent is not None and isinstance(parent, Widget):
            self._parent = parent
    

    @staticmethod
    def calc_draw_pos(
        offset: list,
        size: list,
        align_x: AlignX,
        align_y: AlignY,
        align_to_x: AlignX,
        align_to_y: AlignY,
        parent: any) -> float:
        """Widgets are drawn from middle center. Alignment is relative to the hierachy and size:
        ┌──────────────────┐
        │TopLeft           │
        │                  │
        │                  │
        │   MiddleCenter   │
        │                  │
        │                  │
        │       BottomRight│
        └──────────────────┘  
        """
        draw_pos = offset

        # Self alignment X
        if align_x == AlignX.Centre:
            draw_pos[0] -= size[0] * 0.5
        elif align_x == AlignX.Right:
            draw_pos[0] -= size[0]

        # Self alignment Y
        if align_y == AlignY.Middle:
            draw_pos[1] += size[1] * 0.5
        elif align_y == AlignY.Bottom:
            draw_pos[1] += size[1]
    
        if parent is not None:
            draw_pos += parent._draw_pos

            # Alignment to parent X
            if align_to_x == AlignX.Centre:
                draw_pos[0] += parent._size[0] * 0.5
            elif align_to_x == AlignX.Right:
                draw_pos[0] += parent._size[0]

            # Alignment to parent Y
            if align_to_y == AlignY.Middle:
                draw_pos[1] -= parent._size[1] * 0.5
            elif align_to_y == AlignY.Bottom:
                draw_pos[1] -= parent._size[1]

        return draw_pos


    def dump(self):
        """Print config to stdout for use with Gui editor"""
        print(f"offset = [{self._offset[0]:.2f}, {self._offset[1]:.2f}]")
        print(f"size = [{self._size[0]:.2f}, {self._size[1]:.2f}]")
        print(f"align = [{self._align_x}, {self._align_y}]")
        print("")

        for widget in self._children:
            widget.dump()
            