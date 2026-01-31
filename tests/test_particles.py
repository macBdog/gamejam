import os
import math
import time
import sys

from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.gui_widget import GuiWidget
from gamejam.input import InputActionKey, InputActionModifier
from gamejam.settings import GameSettings
from gamejam.gamejam import GameJam
from gamejam.texture import Texture, SpriteTexture

class ParticleTest(GameJam):
    """Test game that exercises all particle system features."""

    def __init__(self):
        super(ParticleTest, self).__init__()
        self.name = "ParticleTest"
        self.test_index = 0
        self.test_timer = 0.0
        self.test_interval = 2.0  # Spawn new particles every 2 seconds
        self.auto_test = True
        self.continuous_timer = 0.0
        self.continuous_spawn_interval = 0.5  # Initial spawn interval for continuous mode
        self.continuous_spawn_count = 0

        # Test configurations: (name, speed, color, life, num_particles, has_attractor, is_continuous)
        self.test_configs = [
            ("Continuous", 2.0, [0.5, 0.8, 1.0], 1.0, 3, False, True),
            ("1 Particle", 2.0, [1.0, 0.0, 0.0], 1.5, 1, False, False),
            ("8 Particles", 2.0, [0.0, 1.0, 0.0], 1.5, 8, False, False),
            ("16 Particles", 2.0, [0.0, 0.0, 1.0], 1.5, 16, False, False),
            ("32 Particles (Default)", 2.0, [1.0, 1.0, 0.0], 1.5, 32, False, False),
            ("64 Particles", 2.0, [1.0, 0.0, 1.0], 1.5, 64, False, False),
            ("128 Particles (Max)", 2.0, [0.0, 1.0, 1.0], 1.5, 128, False, False),
            ("Fast Decay (speed=5)", 5.0, [1.0, 0.5, 0.0], 1.0, 32, False, False),
            ("Slow Decay (speed=0.5)", 0.5, [0.5, 0.5, 1.0], 2.0, 32, False, False),
            ("Long Life (life=3)", 1.0, [1.0, 1.0, 1.0], 3.0, 32, False, False),
            ("With Attractor", 2.0, [0.3, 1.0, 0.3], 1.5, 32, True, False),
            ("Dense (128 + Attractor)", 1.5, [1.0, 0.8, 0.2], 2.0, 128, True, False),
        ]

        self.spawn_positions = [
            Coord2d(-0.6, 0.6),
            Coord2d(0.0, 0.6),
            Coord2d(0.6, 0.6),
            Coord2d(-0.6, 0.0),
            Coord2d(0.0, 0.0),
            Coord2d(0.6, 0.0),
            Coord2d(-0.6, -0.6),
            Coord2d(0.0, -0.6),
            Coord2d(0.6, -0.6),
        ]

    @staticmethod
    def spawn_test_particles(game, config_index):
        """Spawn particles with a specific test configuration at cursor position."""
        if config_index >= len(game.test_configs):
            config_index = 0

        name, speed, color, life, num_particles, has_attractor, is_continuous = game.test_configs[config_index]

        # Use cursor position for spawning
        cursor_pos = game.gui.cursor.pos

        # Setup attractor if needed
        attractor_pos = None
        if has_attractor:
            # Attractor at center screen
            attractor_pos = [0.0, 0.0]

        # Spawn the particles at cursor position
        game.particles.spawn(
            speed=speed,
            pos=[cursor_pos.x, cursor_pos.y],
            colour=color,
            life=life,
            attractor_pos=attractor_pos,
            num_particles=num_particles
        )

    @staticmethod
    def manual_spawn(**kwargs):
        """Manually spawn particles at cursor position."""
        game = kwargs["game"]
        config_index = kwargs.get("config", 0)
        ParticleTest.spawn_test_particles(game, config_index)

    @staticmethod
    def toggle_auto_test(**kwargs):
        """Toggle automatic testing mode."""
        game = kwargs["game"]
        game.auto_test = not game.auto_test
        if GameSettings.DEV_MODE:
            print(f"Auto-test: {'ON' if game.auto_test else 'OFF'}")

    @staticmethod
    def next_test(**kwargs):
        """Advance to next test configuration."""
        game = kwargs["game"]
        game.test_index = (game.test_index + 1) % len(game.test_configs)
        ParticleTest.spawn_test_particles(game, game.test_index)

    def prepare(self):
        super().prepare()

        # Create test control buttons
        button_size = Coord2d(0.3 * self.graphics.display_ratio, 0.15)

        # Manual spawn button
        spawn_button = GuiWidget(name="SpawnButton", font=self.font)
        spawn_button.set_size(button_size)
        spawn_button.set_offset(Coord2d(-0.7, -0.8))
        spawn_sprite = SpriteTexture(self.graphics, Texture("", 64, 32), [0.2, 0.6, 0.2, 1.0], Coord2d(), button_size)
        spawn_button.set_sprite(spawn_sprite, stretch=True)
        spawn_button.set_text("Spawn (Space)", 10)
        spawn_button.set_action(ParticleTest.manual_spawn, {"game": self, "config": -1})
        self.gui.add_child(spawn_button)

        # Next test button
        next_button = GuiWidget(name="NextButton", font=self.font)
        next_button.set_size(button_size)
        next_button.set_offset(Coord2d(-0.35, -0.8))
        next_sprite = SpriteTexture(self.graphics, Texture("", 64, 32), [0.2, 0.2, 0.6, 1.0], Coord2d(), button_size)
        next_button.set_sprite(next_sprite, stretch=True)
        next_button.set_text("Next (N)", 10)
        next_button.set_action(ParticleTest.next_test, {"game": self})
        self.gui.add_child(next_button)

        # Toggle auto-test button
        auto_button = GuiWidget(name="AutoButton", font=self.font)
        auto_button.set_size(button_size)
        auto_button.set_offset(Coord2d(0.0, -0.8))
        auto_sprite = SpriteTexture(self.graphics, Texture("", 64, 32), [0.6, 0.4, 0.2, 1.0], Coord2d(), button_size)
        auto_button.set_sprite(auto_sprite, stretch=True)
        auto_button.set_text("Toggle Auto (A)", 10)
        auto_button.set_action(ParticleTest.toggle_auto_test, {"game": self})
        self.gui.add_child(auto_button)

        # Keyboard mappings
        self.input.add_key_mapping(32, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE,
                                   ParticleTest.manual_spawn, {"game": self, "config": -1})  # Space
        self.input.add_key_mapping(78, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE,
                                   ParticleTest.next_test, {"game": self})  # N
        self.input.add_key_mapping(65, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE,
                                   ParticleTest.toggle_auto_test, {"game": self})  # A

    def update(self, dt):
        game_draw, _ = self.gui.is_active()
        if game_draw:
            self.profile.begin("particle_test")

            # Check if current test is continuous
            is_continuous = self.test_configs[self.test_index][6] if self.test_index < len(self.test_configs) else False

            # Continuous mode: always active when continuous test is selected
            if is_continuous:
                self.continuous_timer += dt

                # Constant spawn interval (10 spawns per second)
                spawn_interval = 0.1

                if self.continuous_timer >= spawn_interval:
                    self.continuous_timer = 0.0
                    ParticleTest.spawn_test_particles(self, self.test_index)
                    self.continuous_spawn_count += 1

            # Auto-test mode: advance through tests automatically
            if self.auto_test:
                self.test_timer += dt

                if self.test_timer >= self.test_interval:
                    self.test_timer = 0.0
                    self.continuous_timer = 0.0
                    self.continuous_spawn_count = 0

                    # In non-continuous mode, spawn once before advancing
                    if not is_continuous:
                        ParticleTest.spawn_test_particles(self, self.test_index)

                    self.test_index = (self.test_index + 1) % len(self.test_configs)

            # Minimal UI - only 6-8 font draws total
            # Title and test info combined
            if self.test_index < len(self.test_configs):
                name, speed, color, life, num_particles, has_attractor, is_continuous = self.test_configs[self.test_index]

                # Single multi-line draw for main info (1 draw call)
                info_text = f"{name} Count:{num_particles} Speed:{speed} Life:{life}s Attractor:{'Y' if has_attractor else 'N'}"
                self.font.draw(info_text, 11, Coord2d(-0.75, 0.85), [1.0, 1.0, 1.0, 1.0])

                # Progress indicator for auto mode (1 draw call)
                if self.auto_test:
                    progress = int((self.test_timer / self.test_interval) * 100)
                    self.font.draw(f"Next: {progress}% [{self.test_index+1}/{len(self.test_configs)}]", 10,
                                     Coord2d(-0.75, 0.62), [0.7, 0.7, 0.7, 1.0])

            # Compact controls (1 draw call)
            self.font.draw("SPACE:Spawn N:Next A:Auto ESC:Exit", 9, Coord2d(-0.75, -0.85), [0.8, 0.8, 0.8, 1.0])

            # Cursor (1 draw call)
            self.font.draw("+", 14, self.gui.cursor.pos, [1.0, 0.0, 0.0, 1.0])

            # Dev info - minimal (1-2 draw calls)
            if GameSettings.DEV_MODE:
                active_emitters = sum(1 for e in self.particles.emitters if e > 0.0)
                self.font.draw(f"FPS:{math.floor(self.fps)} Emitters:{active_emitters}/8", 10,
                             Coord2d(0.55, 0.85), [0.81, 0.81, 0.81, 1.0])

            self.profile.end()

    def end(self):
        super().end()

def test_particles():
    """Run particle system test."""
    jam = ParticleTest()
    jam.prepare()
    jam.begin()

    # Check for custom test duration
    test_time = 30  # Default 30 seconds
    arg_string = "seconds"
    for _, arg in enumerate(sys.argv):
        found_char = arg.find(arg_string)
        if found_char >= 0:
            arg_val = arg[found_char + len(arg_string):].replace("=", "")
            arg_val = arg_val.replace(" ", "")
            test_time = float(arg_val)

    if time.time() >= jam.start_time + test_time:
        jam.end()
        return True

    return False

if __name__ == "__main__":
    test_particles()
