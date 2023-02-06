from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from gamejam.widget import Alignment, AlignX, AlignY
from gamejam.gui_widget import TouchState
from gamejam.texture import SpriteTexture
from gamejam.coord import Coord2d
from gamejam.cursor import Cursor
from gamejam.font import Font
from gamejam.input import Input
from gamejam.graphics import Graphics
from gamejam.texture import Sprite, SpriteShape, SpriteTexture
from gamejam.gui import Gui


class AssetType(Enum):
    NONE = 0,
    TEXTURE = 1,
    SOUND = 2,


@dataclass(init=True, eq=True)
class Asset:
    path: str
    name: str
    thumb: Sprite


class AssetPicker():
    """Selectable grid of textures and other assets used with GuiEditor."""
    ASSET_DISPLAY_SIZE = Coord2d(0.02, 0.02)
    ASSET_SPACING = Coord2d(0.005, 0.005)
    FILE_EXTENSIONS = {
        AssetType.TEXTURE: [ ".png", ".jpg", ".tga" ],
        AssetType.SOUND: [ ".wav" ],
    }


    def __init__(self, editor: Gui, graphics: Graphics, input: Input, font: Font):
        super().__init__()
        self.editor = editor
        self.type = AssetType.TEXTURE
        self.display_ratio = graphics.display_ratio
        self.font = font
        self.close()
        self._init_debug_bindings(input)


    def close(self):
        self.active = False
        self.items = []
        self.hovered_item_id = -1
        self.hovered_item = None
        self.selected_item = None


    def _init_debug_bindings(self, input: Input):
        pass


    def show(self, type: AssetType, path: Path):
        if self.type is not AssetType.NONE:
            if path.exists() and path.is_dir():
                asset_paths = [f for f in path.iterdir() if any(AssetPicker.FILE_EXTENSIONS[type] in f.lower*())]
                for asset in asset_paths:
                    self.items.append(Asset(asset, asset, None))

            num_items = len(self.items)
            dx = num_items // 2
            dy = num_items // 2
            pos = Coord2d()
            for i in range(num_items):
                if type is AssetType.TEXTURE:
                    self.items[i].sprite = SpriteTexture(self.graphics, self.items[i].path, [0.75] * 4, pos, AssetPicker.ASSET_DISPLAY_SIZE)
                else:
                    self.items[i].sprite = SpriteShape(self.graphics, [0.75] * 4, pos)
                self.items[i].pos = pos
                pos.x += AssetPicker.ASSET_DISPLAY_SIZE.x + AssetPicker.ASSET_SPACING.x
                if i % dx == 0:
                    pos.x = 0.0
                    pos.y += AssetPicker.ASSET_DISPLAY_SIZE.y + AssetPicker.ASSET_SPACING.y


    def touch(self, mouse: Cursor):
        self.hovered_item_id = -1
        self.hovered_item = None
        for item in self.items:
            item_pos = item.sprite.pos
            item_size = item.sprite.size
            size_half = Coord2d(abs(item_size.x) * 0.5, abs(item_size.y))
            inside = (  mouse.pos.x >= item_pos.x - size_half.x and
                        mouse.pos.x <= item_pos.x + size_half.x and
                        mouse.pos.y >= item_pos.y - size_half.y and
                        mouse.pos.y <= item_pos.y + size_half.y)
            if inside:
                self.hovered_item = item
                item.sprite.colour = [1.0] * 4

    def draw(self, dt: float):
        pass
        
            
       