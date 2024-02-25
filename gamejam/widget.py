from copy import copy
from dataclasses import dataclass
from enum import Enum
import functools
from gamejam.coord import Coord2d


class AlignX(Enum):
    Left = 1
    Centre = 2
    Right = 3


class AlignY(Enum):
    Top = 1
    Middle = 2
    Bottom = 3


@dataclass(init=True, eq=True)
class Alignment:
    x: AlignX
    y: AlignY


    def __str__(self) -> str:
        return f"{self.x}, {self.y}"


    @staticmethod
    def from_string(input: str):
        aterms = input["align"].replace(" ", "").split(",")
        return Alignment(AlignX[aterms[0].split(".")[1]], AlignY[aterms[1].split(".")[1]])


def widget_dirty(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args[0]._dirty = True
        return func(*args, **kwargs)
    return wrapper


class Widget():
    """A widget is a position-based hierarchical node. It's an empty anchor 
    without any utility. For drawing textures, font and interactions see GuiWidget."""

    def __repr__(self) -> str:
        return self.name


    def __contains__(self, widget) -> bool:
        return widget in self._children


    def __init__(self, name: str=""):
        # Draw pos automatically gets refreshed when the dirty flag is set
        self.name = f"Widget-{hex(id(self))[6:]}" if not name else name

        self._parent = None
        self._children = []
        self._dirty = True
        self._draw_pos = Coord2d()
        self._offset = Coord2d()
        self._size = Coord2d(0.1, 0.1)

        # Where this widget is drawn relative to it's parent anchor
        self._align = Alignment(AlignX.Centre, AlignY.Middle)

        # What part of the parent this widget positions relative to
        self._align_to = Alignment(AlignX.Centre, AlignY.Middle)


    def draw(self, dt: float):
        """Apply any changes to the widget rect."""
        if self._dirty:
            self._draw_pos = Widget.calc_draw_pos(self._offset, self._size, self._align, self._align_to, self._parent)
            self._dirty = False

        for child in self._children:
            child.draw(dt)


    def add_child(self, child):
        if child not in self and child._parent == None:
            child._parent = self
            self._children.append(child)
        else:
            print(f"Error when adding child widget {child.name} to {self.name}! Widget {child.name} already has a parent and it's name is {child._parent.name}.")


    @widget_dirty
    def set_offset(self, offset: Coord2d):
        self._offset = offset


    @widget_dirty
    def set_size(self, size: Coord2d):
        self._size = size


    @widget_dirty
    def set_align(self, align: Alignment):
        self._align = align

    
    @widget_dirty
    def set_align_to(self, align_to: Alignment):
        self._align_to = align_to


    @widget_dirty
    def set_parent(self, parent: any):
        if parent is not None and isinstance(parent, Widget):
            self._parent = parent
    

    @staticmethod
    def calc_draw_pos(
        offset: Coord2d,
        size: Coord2d,
        align: Alignment,
        align_to: Alignment,
        parent: any) -> Coord2d:
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
        draw_pos = copy(offset)

        # Self alignment X
        if align.x == AlignX.Left:
            draw_pos.x += size.x * 0.5
        elif align.x == AlignX.Right:
            draw_pos.x -= size.x * 0.5

        # Self alignment Y
        if align.y == AlignY.Top:
            draw_pos.y -= size.y * 0.5
        elif align.y == AlignY.Bottom:
            draw_pos.y += size.y * 0.5
    
        if parent is not None:
            draw_pos += parent._draw_pos

            # Alignment to parent X
            if align_to.x == AlignX.Left:
                draw_pos.x -= parent._size.x * 0.5
            elif align_to.x == AlignX.Right:
                draw_pos.x += parent._size.x * 0.5

            # Alignment to parent Y
            if align_to.y == AlignY.Top:
                draw_pos.y += parent._size.y * 0.5
            elif align_to.y == AlignY.Bottom:
                draw_pos.y -= parent._size.y * 0.5
        return draw_pos
