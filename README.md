# gamejam
A Python and OpenGL game jamming framework. See tests.py for a minimal example.

## Hotkeys:
* `PrtSc` - Dump profiling information to the command line
* `Ctrl+D` - Toggle dev mode (default off)
Dev mode will run the game in debug mode with the following features:
    1. Print input logging and extra info on the command line
    2. Show FPS and mouse coords on screen

* Ctrl+G - Toggle GUI editing mode (default off)
GUI editing mode will show the layout and alignment controls for widgets. Exiting GUI edit mode will dump the currently active gui configuration to the command line. Editor controls:
    1. `Ctrl+N` will create a new widget
    2. `Ctrl+D` will duplicate a widget
    3. `Ctrl+X` will delete a widget
    4. `O` while widget selected to modify offset with mouse
    5. `S` while widget selected to modify size with mouse
    4. `F` to modify font size with mouse
    5. `T` to modify text offset size with mouse
    8. `Numpad` to change alignment
    9. `A` then select another widget to re-parent

### Task Queue:
1. Hot reload shaders