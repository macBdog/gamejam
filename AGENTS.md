# GameJam Framework - Agent Development Notes

## Project Overview

**GameJam** is a Python-based OpenGL game framework built for rapid game development and prototyping. It provides a complete 2D/3D rendering pipeline with an integrated GUI system, shader management, and input handling. The framework is optimized for game jams where speed of development is critical.

## Technology Stack

- **Language**: Python 3.x
- **Graphics**: OpenGL 3.3 Core via PyOpenGL
- **Windowing**: GLFW
- **Math**: NumPy
- **Font Rendering**: FreeType (freetype-py)
- **Image Loading**: PIL (Pillow)

## Project Structure

```
C:\projects\gamejam\
├── gamejam/
│   ├── __init__.py
│   ├── graphics.py          # Shader management, Graphics class
│   ├── texture.py           # Texture, Sprite*, TextureAtlas, TextureManager
│   ├── font.py              # Font rendering system
│   ├── input.py             # Input, InputAction*, InputMethod
│   ├── gamejam.py           # GameJam main loop class
│   ├── gui.py               # Gui widget manager
│   ├── widget.py            # Widget base class, Alignment
│   ├── gui_widget.py        # GuiWidget interactive widgets
│   ├── gui_editor.py        # Live GUI editing
│   ├── camera.py            # Camera view system
│   ├── coord.py             # Coord2d, Coord3d math
│   ├── animation.py         # Animation, AnimType
│   ├── particles.py         # Particles GPU system
│   ├── cursor.py            # Cursor input helper
│   ├── quickmaff.py         # Math utilities
│   ├── settings.py          # GameSettings
│   ├── profile.py           # Performance profiler
│   ├── bitset.py            # BitSet utility
│   └── shaders/
│       ├── texture.vert/frag
│       ├── texture_atlas.vert/frag
│       ├── font.vert/frag
│       ├── colour.vert/frag
│       ├── anim.vert/frag
│       ├── particles.frag
│       └── debug.vert/frag
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
└── README.md                # Documentation
```

## Core Components

### 1. Graphics System ([graphics.py](gamejam/graphics.py))

The Graphics class is the central shader management and rendering system.

#### Shader Enum Types

```python
class Shader(Enum):
    TEXTURE = 0          # Basic texture rendering
    TEXTURE_ATLAS = 1    # Optimized multi-texture rendering
    COLOUR = 2           # Solid color shapes
    FONT = 3             # Text rendering
    PARTICLES = 4        # Particle effects
    ANIM = 5             # Animated sprites
    DEBUG = 6            # Debug rendering

class ShaderType(Enum):
    VERTEX = 0
    PIXEL = 1
```

#### Key Methods

**`process_shader_source(src: str, subs: dict) -> str`** (Lines 118-124)

The core shader preprocessing function:

```python
@staticmethod
def process_shader_source(src: str, subs: dict) -> str:
    """String substitution for shader preprocessing.

    Args:
        src: GLSL shader source code
        subs: Dictionary of {search_string: replacement_value}

    Returns:
        Modified shader source with substitutions applied

    Example:
        shader_subs = {
            "MAX_LIGHTS": 8,
            "#define USE_SHADOWS 0": "#define USE_SHADOWS 1"
        }
        processed = Graphics.process_shader_source(shader_src, shader_subs)
    """
    for key, sub in subs.items():
        if src.find(key):
            src = src.replace(key, str(sub))
        elif GameSettings.DEV_MODE:
            print(f"Cannot find shader substitute key: {key} ")
    return src
```

**Purpose**: Enables runtime shader customization by performing string replacement before compilation. Similar to C preprocessor macros but implemented as simple string substitution.

**Use Cases**:
- Injecting array sizes (e.g., `MAX_PARTICLES`, `NUM_LIGHTS`)
- Enabling/disabling shader features (e.g., `USE_NORMAL_MAPPING`)
- Passing constants calculated at runtime
- Customizing shader behavior per-instance

**Other Key Methods**:
- `builtin_shader(shader: Shader, type: ShaderType)`: Loads built-in shaders from `gamejam/shaders/` directory
- `load_shader(path: Path) -> str`: Loads shader source from file
- `create_program(vertex_src: str, pixel_src: str) -> int`: Compiles and links shader program
- `print_all_uniforms(shader: int)`: Debug utility to list all shader uniforms

#### Projection System

- **Orthographic (2D)**: Default projection for 2D games, normalized to -1 to 1 coordinates
- **Perspective (3D)**: Optional 3D projection with camera integration
- **Display Ratio**: Automatically adjusts for aspect ratio to prevent stretching

#### Built-in Shaders

Located in `gamejam/shaders/`:

- **texture.vert/frag**: Basic textured quad rendering with transform matrices
- **texture_atlas.vert/frag**: Batched rendering system for multiple textures
- **font.vert/frag**: Single-channel texture rendering for text glyphs
- **colour.vert/frag**: Solid color shape rendering
- **anim.vert/frag**: Animated sprite effects
- **particles.frag**: GPU-accelerated particle simulation
- **debug.vert/frag**: Debug visualization overlays

---

### 2. Texture and Sprite System ([texture.py](gamejam/texture.py))

Comprehensive texture and sprite rendering with multiple rendering strategies.

#### Texture Class

Low-level OpenGL texture wrapper:

- Loads images via PIL (PNG, JPG, TGA, BMP)
- Creates OpenGL texture objects (GL_TEXTURE_2D)
- Supports wrapping modes: `GL_REPEAT`, `GL_CLAMP_TO_EDGE`
- Random texture generation for missing assets (magenta debug texture)
- Texture binding and cleanup

#### Sprite Base Class

Foundation for all sprite types:

**Properties**:
- `pos: Coord2d` - Position in normalized coordinates (-1 to 1)
- `size: Coord2d` - Size in normalized coordinates
- `col: list[float]` - RGBA color/tint (0.0 to 1.0)
- `graphics: Graphics` - Reference to graphics system

**Methods**:
- `get_object_matrix() -> list[float]`: Calculates 4x4 transformation matrix
- `draw()`: Abstract method implemented by subclasses

#### SpriteShape

Colored rectangle sprites without textures:

- Uses `COLOUR` shader
- VAO/VBO/EBO buffer management
- Efficient for UI elements and solid color shapes
- Custom shader support

#### SpriteTexture

Individual textured sprite rendering:

- One texture per sprite instance
- Uses `TEXTURE` shader
- Full transform support (position, size, rotation)
- Custom uniform callback support for shader parameters
- Color tinting via multiplication

**Usage Pattern**:
```python
sprite = SpriteTexture(graphics, texture, color, position, size, custom_shader)

def custom_uniforms():
    glUniform1f(time_loc, elapsed_time)
    glUniform2f(offset_loc, x, y)

sprite.draw(custom_uniforms)  # Optional callback for additional uniforms
```

#### TextureAtlas - Advanced Batching System

The crown jewel of the texture system - a sophisticated batching renderer.

**Capabilities**:
- Composites multiple source textures into single 4096x4096 atlas
- Batches up to **128 draw calls** into one shader pass
- Supports **64 unique texture items**
- Dynamic texture packing with automatic layout
- Configurable blending modes

**Blending Modes** (AtlasBlendMode enum):
- `MAX`: Maximum of all layers (brightest pixel wins)
- `MIN`: Minimum of all layers (darkest pixel wins)
- `ALPHA_*`: Various alpha blending strategies
- `FIRST`: First layer only (no blending)
- `LAST`: Last layer only (painter's algorithm)

**Architecture**:

1. **Build Phase** (`add_texture(name, texture)`):
   - Textures blitted into atlas at initialization
   - Packs textures horizontally with line wrapping
   - Stores UV coordinates for each named texture
   - One-time setup during game initialization

2. **Queue Phase** (`draw(name, pos, size, col)`):
   - Draw calls queued into arrays (not immediately rendered)
   - Up to 128 queued draws per frame
   - Minimal CPU overhead during game loop

3. **Render Phase** (`draw_final()`):
   - Single shader pass renders all queued draws
   - All draws batched into one OpenGL call
   - Massively reduces draw call overhead

**Shader Integration**:
```python
shader_substitutes = {
    "MAX_ATLAS_ITEMS": TextureAtlas.MaxAtlasItems,    # 64
    "MAX_ATLAS_DRAWS": TextureAtlas.MaxAtlasDraws,    # 128
}
atlas_shader = Graphics.process_shader_source(
    graphics.builtin_shader(Shader.TEXTURE_ATLAS, ShaderType.PIXEL),
    shader_substitutes
)
```

**Performance**: Can render 100+ sprites in <1ms on modern GPUs due to batching.

#### SpriteAtlasTexture

Sprite that renders via TextureAtlas:

- References texture by name instead of storing texture
- Queues draws instead of immediate rendering
- Most memory-efficient approach (shared atlas)
- No VAO/VBO overhead per sprite

#### TextureManager

Asset management system:

**Features**:
- Scans directory recursively for all image files
- Auto-builds TextureAtlas during initialization
- Provides factory methods: `create_sprite()`, `create_atlas_sprite()`
- Maintains cache of raw Texture objects
- Debug visualization: `draw_atlas_debug()`

**Initialization**:
```python
textures = TextureManager(graphics, "assets/textures/")
# Automatically loads all PNG/JPG/TGA from directory
# Creates optimized texture atlas
sprite = textures.create_atlas_sprite("player", pos, size)
```

---

### 3. Font System ([font.py](gamejam/font.py))

FreeType-based font rendering using GPU-accelerated glyph atlases.

#### Architecture

- **Font Atlas**: Single 2048x2048 R8 (single-channel) texture
- **Character Range**: ASCII 32-127 + special chars ('½')
- **Glyph Metrics**: Stores advance, bearing, size, UV coords per character
- **Dynamic Layout**: Horizontal packing with automatic line wrapping

#### Key Features

- **Anti-aliased Rendering**: FreeType rasterization for smooth glyphs
- **One-time Setup**: Atlas generated once at initialization
- **GPU-Accelerated**: All text rendering happens in shader
- **Newline Support**: Handles `\n` for multi-line text
- **Aspect Ratio Correction**: Adjusts for display ratio
- **Dimension Calculation**: Returns drawn text bounds

#### Font Shader

Uses specialized `font.vert/frag`:
- Samples single-channel (R) texture
- Maps red channel → alpha for colored text
- Supports per-character UV transformations
- Efficient for large amounts of text

#### Rendering Process

1. **Initialization**:
   - Load TTF font (default: `consola.ttf`)
   - Rasterize all ASCII glyphs using FreeType
   - Pack glyphs into 2048x2048 atlas
   - Store UV coordinates and metrics

2. **Drawing** (`draw(text, size, pos, col)`):
   - Calculate glyph positions based on metrics
   - Upload quad vertices with UV coords
   - Render using font shader
   - Apply color tint and aspect ratio

3. **Performance**:
   - No CPU text rasterization per frame
   - Batched quad rendering
   - Single texture bind for all glyphs

**Usage**:
```python
font = Font(graphics, window, "path/to/font.ttf")
width, height = font.draw("Hello World", 24, Coord2d(0.0, 0.0), [1,1,1,1])
```

---

### 4. Input System ([input.py](gamejam/input.py))

Event-driven input handling with flexible key mapping.

#### Core Enums

**InputActionKey** - Action types:
```python
ACTION_KEYUP = 0
ACTION_KEYDOWN = 1
ACTION_KEYREPEAT = 2
```

**InputActionModifier** - Modifier keys:
```python
NONE = 0
LSHIFT = 340
LCTRL = 341
LALT = 342
RSHIFT = 344
RCTRL = 345
RALT = 346
```

**InputMethod** - Input sources:
```python
KEYBOARD = 1
JOYSTICK = 2
MIDI = 3        # For MIDI controller integration
```

#### Input Class

Main input manager with GLFW callback integration.

**Key Features**:
- Event-driven architecture (no polling required)
- Flexible mapping: `(key, action, modifier)` → `(callback, kwargs)`
- Multiple callbacks per key combo supported
- Normalized cursor coordinates (-1 to 1)
- Mouse button state tracking
- Text input support via Cursor integration

**Key Mapping System**:
```python
input.add_key_mapping(
    key=glfw.KEY_ESCAPE,
    action=InputActionKey.ACTION_KEYDOWN,
    modifier=InputActionModifier.NONE,
    func=quit_game,
    func_args={"save_state": True}
)

# Multiple modifiers:
input.add_key_mapping(
    key=glfw.KEY_S,
    action=InputActionKey.ACTION_KEYDOWN,
    modifier=InputActionModifier.LCTRL,
    func=save_file
)
```

**Callbacks Receive**:
- All mapped `func_args` as keyword arguments
- Automatic handling of key repeat events
- Modifier state at time of press

**Methods**:
- `add_key_mapping()`: Register callback for key combo
- `get_cursor_pos() -> tuple[float, float]`: Get normalized mouse position
- `is_mouse_button_down(button) -> bool`: Check mouse button state
- `update()`: Process queued events (called once per frame)

---

### 5. GUI and Widget System

A hierarchical widget system for UI development with YAML persistence.

#### Widget Class ([widget.py](gamejam/widget.py))

Base positioning system for all GUI elements.

**Coordinate System**: Normalized (-1 to 1) screen space

**Alignment System**: 9-point alignment grid

```python
class Alignment(Enum):
    TopLeft = 0
    TopMiddle = 1
    TopRight = 2
    MiddleLeft = 3
    MiddleCenter = 4
    MiddleRight = 5
    BottomLeft = 6
    BottomMiddle = 7
    BottomRight = 8
```

**Key Properties**:
- `_align`: How widget aligns relative to its anchor point
- `_align_to`: What point on parent to align to
- `_offset`: Additional position offset from aligned position
- `_size`: Widget dimensions
- `_parent`: Parent widget reference

**Dirty Flag System**:
- Recalculates draw position only when needed
- Hierarchical updates (parent change → children recalc)
- Performance optimization for complex widget trees

**Hierarchical Features**:
- Parent-child relationships
- Recursive position calculations
- Alignment inheritance

#### GuiWidget ([gui_widget.py](gamejam/gui_widget.py))

Interactive widgets with rendering capabilities.

**Features**:
- Sprite attachment for backgrounds/images
- Font rendering for text labels
- Touch/click detection with callbacks
- YAML serialization for GUI editor
- Custom shader support
- Color/alpha animation support

**Widget Types**:
- Buttons with click callbacks
- Text labels
- Image panels
- Container widgets

**Interaction**:
```python
button = GuiWidget(gui, "play_button")
button.set_size(Coord2d(0.2, 0.1))
button.set_alignment(Alignment.MiddleCenter, Alignment.MiddleCenter)
button.set_text("Play Game", 18)
button.set_touch_callback(start_game)
```

#### Gui ([gui.py](gamejam/gui.py))

Widget collection manager and root container.

**Features**:
- Root-level widget container (no parent)
- Active/inactive state management
- YAML persistence: `save(path)`, `load(path)`
- Widget factory methods
- Mouse cursor integration
- Touch event propagation to children
- Batch rendering of all widgets

**Methods**:
- `add_widget(name) -> GuiWidget`: Create and add widget
- `get_widget(name) -> GuiWidget`: Retrieve by name
- `remove_widget(name)`: Delete widget
- `update(dt)`: Update animations and state
- `draw()`: Render all active widgets
- `check_touch(cursor) -> bool`: Propagate touch events

**YAML Structure**:
```yaml
widgets:
  main_menu:
    size: [0.8, 0.6]
    align: MiddleCenter
    align_to: MiddleCenter
    text: "Main Menu"
    font_size: 24
  play_button:
    size: [0.3, 0.1]
    align: MiddleCenter
    align_to: MiddleCenter
    offset: [0.0, -0.15]
    text: "Play"
```

#### GuiEditor ([gui_editor.py](gamejam/gui_editor.py))

Live GUI editing tool (toggle with `Ctrl+G`).

**Features**:
- Visual widget manipulation via mouse
- Alignment control via numpad (1-9 keys)
- Size/position/offset editing modes
- Widget creation/deletion/duplication
- Live YAML export on save
- Overlay showing widget bounds and alignment points

**Controls**:
- `Numpad 1-9`: Set alignment
- `Arrow Keys`: Adjust offset
- `Shift+Arrows`: Adjust size
- `Ctrl+S`: Save to YAML
- `Ctrl+D`: Duplicate selected widget
- `Del`: Delete selected widget

---

### 6. Animation System ([animation.py](gamejam/animation.py))

Shader-based animation system for visual effects.

#### AnimType Enum

```python
FadeIn = 1               # Fade from transparent to opaque
FadeOut = 2              # Fade from opaque to transparent
Pulse = 3                # Pulsing opacity
FadeInOutSmooth = 4      # Smooth fade in and out
Rotate = 5               # Rotation animation
Throb = 6                # Size pulsing
ScrollHorizontal = 7     # Horizontal scrolling
ScrollVertical = 8       # Vertical scrolling
FillHorizontal = 9       # Horizontal wipe
FillVertical = 10        # Vertical wipe
FillRadial = 11          # Radial fill
Flash = 12               # Rapid flashing
```

#### Animation Class

**Properties**:
- `time: float` - Current time (0.0 to 1.0)
- `length: float` - Duration in seconds
- `loop: bool` - Repeat animation
- `magnitude: float` - Effect strength multiplier
- `type: BitSet` - Combination of AnimType flags

**Features**:
- Shader-driven effects (no CPU interpolation)
- Multiple effects can combine (BitSet)
- Action callbacks at specific times
- Automatic time progression

**Usage**:
```python
anim = Animation()
anim.length = 2.0
anim.loop = True
anim.type.set(AnimType.FadeInOutSmooth)
anim.type.set(AnimType.Pulse)  # Combine multiple

# In shader, these are passed as uniforms
```

---

### 7. Particle System ([particles.py](gamejam/particles.py))

GPU-accelerated particle system using compute shaders.

**Capabilities**:
- **8 concurrent emitters** (configurable via shader substitution)
- Shader-based particle simulation (no CPU overhead)
- Emitter properties: position, color, speed, attractor point
- Automatic particle lifecycle management
- Random texture generation for visual diversity

**Shader Integration**:
```python
shader_subs = {
    "NUM_EMITTERS": Particles.NumEmitters,  # 8
}
particle_shader = Graphics.process_shader_source(
    graphics.builtin_shader(Shader.PARTICLES, ShaderType.PIXEL),
    shader_subs
)
```

**Properties per Emitter**:
- Position (Coord2d)
- Color (RGBA)
- Speed (float)
- Attractor (Coord2d) - Particle target point
- Active state (bool)

**Rendering**:
- Single fullscreen quad
- All particle simulation in fragment shader
- Particles calculated per-pixel based on emitter data
- Highly efficient for thousands of particles

---

### 8. Coordinate and Math System

#### Coord2d ([coord.py](gamejam/coord.py))

2D vector math class.

**Operations**:
- `add(other)`, `sub(other)`, `mul(scalar)`
- `length()` - Magnitude
- `normalize()` - Unit vector
- `dot(other)` - Dot product
- `cross(other)` - 2D cross product (z-component)
- `__str__()` - String serialization: "x,y"

**Usage**:
```python
pos = Coord2d(0.5, 0.3)
vel = Coord2d(0.1, -0.05)
new_pos = pos.add(vel.mul(dt))
```

#### Coord3d ([coord.py](gamejam/coord.py))

3D vector math class with same operations as Coord2d.

**Additional Methods**:
- 3D cross product
- Camera positioning

#### QuickMaff ([quickmaff.py](gamejam/quickmaff.py))

Math utility functions.

**Functions**:
- `clamp(value, min, max)` - Constrain value to range
- `lerp(a, b, t)` - Linear interpolation
- `bicubic(a, b, c, d, t)` - Smooth cubic interpolation
- `ortho(left, right, bottom, top, near, far)` - Orthographic projection matrix
- `perspective(fov, aspect, near, far)` - Perspective projection matrix

**Predefined Matrices**:
```python
IDENTITY = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
ORTHO = ortho(-1, 1, -1, 1, 0.1, 100)
PERSPECTIVE = perspective(45, 16/9, 0.1, 1000)
```

---

### 9. Camera System ([camera.py](gamejam/camera.py))

Simple 3D camera for perspective rendering.

**Properties**:
- `pos: Coord3d` - Camera position in world space
- `target: Coord3d` - Look-at target point
- `mat_view: list[float]` - 4x4 view matrix

**Methods**:
- `look_at(target: Coord3d)` - Point camera at target (partial implementation)
- Integration with Graphics class for view matrix

**Note**: Camera system is basic and primarily for 3D debug visualization. Most games use 2D orthographic projection.

---

### 10. Main Game Loop ([gamejam.py](gamejam/gamejam.py))

The **GameJam** base class provides the core game loop and initialization.

#### Initialization Flow (`prepare()`)

1. Initialize GLFW with OpenGL 3.3 Core profile
2. Create window (1920x1080 default, configurable)
3. Set up Graphics system
4. Initialize Font with default font (`consola.ttf`)
5. Create TextureManager and build texture atlas
6. Configure Input system with GLFW callbacks
7. Create Particles system
8. Initialize Profiler
9. Create main Gui
10. Set up GuiEditor
11. Configure OpenGL state:
    - Enable alpha blending: `GL_SRC_ALPHA`, `GL_ONE_MINUS_SRC_ALPHA`
    - Enable depth testing for 3D rendering
    - Set clear color

#### Main Loop (`begin()`)

```python
while running and not window_should_close:
    1. profiler.update()                # Performance tracking
    2. dt = calculate_delta_time()      # Frame time
    3. glClear(COLOR | DEPTH)           # Clear buffers
    4. textures.draw_atlas()            # Batch render all atlas sprites

    5. if gui_edit_mode:
        gui_editor.update(dt)           # Edit mode
        gui_editor.draw()
    else:
        gui.update(dt)                  # Normal mode
        gui.check_touch(cursor)
        gui.draw()

    6. user_update(dt)                  # Game-specific logic

    7. if DEV_MODE:
        draw_debug_stats()              # FPS, mouse coords, profiler

    8. particles.draw()                 # Particle effects
    9. cursor.draw()                    # Mouse cursor sprite
    10. glfwSwapBuffers(window)         # Present frame
    11. glfwPollEvents()                # Process input events
```

#### Built-in Hotkeys

Automatically registered by framework:

- `ESC` - Quit application
- `PrtSc` - Dump profiling info to console
- `Ctrl+D` - Toggle dev mode (FPS counter, debug overlay)
- `Ctrl+G` - Toggle GUI editor
- `2` - Switch to orthographic projection
- `3` - Switch to perspective projection
- `WASD` - Move camera (dev mode only)
- `E/Q` - Move camera up/down (dev mode only)

#### Game Subclass Pattern

```python
class MyGame(GameJam):
    def __init__(self):
        super().__init__()
        self.name = "My Game"

    def prepare(self):
        super().prepare()
        # Custom initialization

    def update(self, dt):
        # Game logic here

    def end(self):
        # Cleanup
        super().end()

game = MyGame()
game.prepare()
game.begin()  # Runs until quit
game.end()
```

---

### 11. Utility Systems

#### Settings ([settings.py](gamejam/settings.py))

Global configuration.

```python
class GameSettings:
    DEV_MODE = False      # Debug features and logging
    VSYNC = True          # V-sync toggle
```

#### Profile ([profile.py](gamejam/profile.py))

Performance profiling system.

**Features**:
- Named sections
- Hierarchical timing
- Min/max/average tracking
- Console output on demand

**Usage**:
```python
profiler.begin("rendering")
draw_scene()
profiler.end("rendering")

profiler.print()  # Dump stats
```

#### BitSet ([bitset.py](gamejam/bitset.py))

Bit manipulation utility.

**Methods**:
- `set(bit)` - Set bit to 1
- `clear(bit)` - Set bit to 0
- `toggle(bit)` - Flip bit
- `test(bit) -> bool` - Check if bit is set

**Use Case**: Combining multiple AnimType flags in Animation system.

#### Cursor ([cursor.py](gamejam/cursor.py))

Mouse cursor helper.

**Features**:
- 2D position tracking (normalized coordinates)
- Button state management (left/right/middle)
- Optional sprite attachment for custom cursor
- Text editing buffer with live display
- Commit/cancel callbacks for text input

---

## Architecture Principles

### 1. Batching Philosophy

The framework heavily emphasizes **batching** for performance:

- **TextureAtlas**: 128 sprites → 1 draw call
- **Font**: All glyphs → 1 texture → batched quads
- **Particles**: All particles simulated in single shader pass

**Why**: Modern GPUs are fast at processing, slow at state changes. Batching minimizes CPU-GPU communication.

### 2. Shader-Driven Effects

Animation and particles use **GPU-based logic**:

- CPU sets parameters (uniforms)
- GPU computes effects per-pixel/vertex
- No CPU interpolation overhead

**Why**: Offload computation to GPU, freeing CPU for game logic.

### 3. Flexible Shader Customization

The `process_shader_source()` function enables **template-based shaders**:

- Inject array sizes at runtime
- Enable/disable features via substitution
- Customize shaders per-instance

**Why**: Avoid shader permutation explosion. One shader template → many configurations.

### 4. Normalized Coordinates

All positions/sizes use **-1 to 1 range**:

- Origin at center (0, 0)
- Display ratio correction automatic
- Resolution-independent layout

**Why**: Hardware-native coordinate system. No pixel calculations. Scales to any resolution.

### 5. Event-Driven Input

Input uses **callbacks, not polling**:

- Register key combos → function mappings
- Modifier key support
- No manual input checking per frame

**Why**: Cleaner code. Less CPU overhead. Easier to remap controls.

### 6. Hierarchical GUI

Widgets use **parent-child relationships**:

- Alignment system (9-point grid)
- Recursive position calculations
- YAML persistence

**Why**: Complex UIs easy to build. Visual editor support. Data-driven design.

---

## Framework Strengths

1. **Rapid Prototyping**: Complete rendering stack out-of-box
2. **Batched Rendering**: High-performance sprite rendering (100+ sprites <1ms)
3. **Flexible Shaders**: Template system allows runtime customization
4. **Complete UI Stack**: Hierarchical widgets with live editor
5. **Debug Tooling**: Built-in profiler, dev mode, GUI editor
6. **Asset Management**: Automatic texture atlas building
7. **Cross-Platform**: GLFW + OpenGL for broad compatibility
8. **Minimal Dependencies**: Only requires GLFW, PyOpenGL, NumPy, FreeType, PIL

---

## Framework Limitations

1. **2D-Focused**: 3D support is basic (camera system incomplete)
2. **No Physics**: Physics must be implemented separately
3. **No Audio**: Audio system not included
4. **Single Window**: Multi-window not supported
5. **Fixed Pipeline**: Extension requires subclassing or modification
6. **No Hot-Reload**: Shader/asset changes require restart (TODO item)

---

## Common Usage Patterns

### Creating a New Game

```python
from gamejam.gamejam import GameJam
from gamejam.coord import Coord2d

class MyGame(GameJam):
    def __init__(self):
        super().__init__()
        self.name = "My Game"
        self.player_sprite = None

    def prepare(self):
        super().prepare()
        # Create player sprite from texture atlas
        self.player_sprite = self.textures.create_atlas_sprite(
            "player",
            Coord2d(0.0, 0.0),
            Coord2d(0.1, 0.1)
        )

    def update(self, dt):
        # Game logic
        self.player_sprite.pos.x += 0.1 * dt

        # Rendering (atlas sprites auto-queued)
        # Manual draws:
        # self.player_sprite.draw()

if __name__ == "__main__":
    game = MyGame()
    game.prepare()
    game.begin()
    game.end()
```

### Custom Shaders with Substitution

```python
# Load custom shader
shader_src = Graphics.load_shader("shaders/custom.frag")

# Define substitutions
shader_subs = {
    "MAX_LIGHTS": 8,
    "USE_NORMAL_MAPPING": 1,
    "#define QUALITY 0": "#define QUALITY 2"
}

# Process shader
processed = Graphics.process_shader_source(shader_src, shader_subs)

# Compile shader
shader = Graphics.create_program(vertex_src, processed)
```

### Widget Creation

```python
# Create GUI
menu_gui = Gui(graphics, input, cursor)

# Add button
play_button = menu_gui.add_widget("play")
play_button.set_size(Coord2d(0.3, 0.1))
play_button.set_alignment(Alignment.MiddleCenter, Alignment.MiddleCenter)
play_button.set_text("Play Game", 24)
play_button.set_touch_callback(start_game_callback)

# Save layout
menu_gui.save("gui/main_menu.yaml")

# Load layout
menu_gui.load("gui/main_menu.yaml")
```

### Input Mapping

```python
# Add key mapping
input.add_key_mapping(
    key=glfw.KEY_SPACE,
    action=InputActionKey.ACTION_KEYDOWN,
    modifier=InputActionModifier.NONE,
    func=player_jump
)

# With arguments
input.add_key_mapping(
    key=glfw.KEY_1,
    action=InputActionKey.ACTION_KEYDOWN,
    modifier=InputActionModifier.NONE,
    func=switch_weapon,
    func_args={"weapon_id": 0}
)
```

---

## Dependencies

From `requirements.txt`:

```
glfw>=2.0.0          # Windowing and OpenGL context
PyOpenGL>=3.1.5      # OpenGL bindings
freetype-py>=2.2.0   # Font rendering
numpy>=1.21.0        # Math operations
Pillow>=8.3.0        # Image loading
```

---

## Future Enhancements (TODO)

Based on code comments and architecture:

1. **Hot-Reload**: Live shader and asset reloading
2. **Audio System**: Sound effects and music playback
3. **Networking**: Multiplayer support
4. **3D Camera**: Complete look-at and movement system
5. **Physics Integration**: Box2D or similar
6. **Render Targets**: Offscreen rendering and post-processing
7. **Compute Shaders**: GPU-based game logic
8. **Mobile Support**: Touch input and mobile optimizations

---

## Project Dependencies

Known projects using GameJam framework:

- **MidiMaster** (`C:\Projects\midimaster`) - MIDI rhythm game using musical notation
  - Uses custom shaders via `process_shader_source()`
  - Heavy use of TextureAtlas for sprite batching
  - Font system for note letters and UI
  - Input system for keyboard/MIDI integration

---

This framework provides a solid foundation for rapid game development, particularly for 2D games and prototypes where speed of development is paramount.
