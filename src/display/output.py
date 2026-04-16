import sys
from typing import TextIO

from colorbrew import Color
from colorbrew.exceptions import ColorParseError

from src.errors import SimulationError
from src.models import Drone
from src.simulation import SimulationEngine


class AnsiColorFormatter:
    """Formats move tokens with ANSI colors for terminal output."""

    def __init__(self) -> None:
        """Initializes ANSI escape codes used by the formatter.

        Returns:
            None.
        """
        self.reset_code = "\033[0m"
        self.ansi_256_color_template = "\033[38;5;{}m"
        self.white_code = "\033[37m"

    def rgb_to_ansi_256(self, red: int, green: int, blue: int) -> str:
        """Converts an RGB color to the closest ANSI 256-color code.

        Args:
            red: Red component between 0 and 255.
            green: Green component between 0 and 255.
            blue: Blue component between 0 and 255.

        Returns:
            ANSI escape sequence for the computed color.
        """
        if red == green == blue:
            if red < 8:
                color_code = 16
            elif red > 248:
                color_code = 231
            else:
                color_code = 232 + round((red - 8) / 247 * 24)
            return self.ansi_256_color_template.format(color_code)

        red_code = round(red / 255 * 5)
        green_code = round(green / 255 * 5)
        blue_code = round(blue / 255 * 5)
        color_code = 16 + (36 * red_code) + (6 * green_code) + blue_code
        return self.ansi_256_color_template.format(color_code)

    def get_ansi_color(self, color_name: str) -> str | None:
        """Resolves a metadata color name to an ANSI escape sequence.

        Args:
            color_name: Zone color name from the parsed map.

        Returns:
            ANSI escape sequence for the color, or ``None`` when color
            output should be skipped.
        """
        normalized_name = color_name.lower()
        if normalized_name == "none":
            return None

        try:
            rgb = Color.from_name(normalized_name).rgb
        except ColorParseError:
            return self.white_code
        return self.rgb_to_ansi_256(rgb[0], rgb[1], rgb[2])

    def colorize(self, text: str, color_name: str) -> str:
        """Wraps text in the ANSI code matching a zone color.

        Args:
            text: Text to colorize.
            color_name: Zone color name from the map.

        Returns:
            The original text or its colorized representation.
        """
        ansi_color = self.get_ansi_color(color_name)
        if ansi_color is None:
            return text
        return f"{ansi_color}{text}{self.reset_code}"


class SimulationRenderer:
    """Renders simulation turns into output lines."""

    def __init__(
        self,
        engine: SimulationEngine,
        stream: TextIO | None = None,
        color_formatter: AnsiColorFormatter | None = None,
        show_zone: bool = False,
    ) -> None:
        """Initializes a renderer for a simulation engine.

        Args:
            engine: Simulation engine to render.
            stream: Output stream used to detect color support.
            color_formatter: Optional formatter for ANSI coloring.
            show_zone: Whether zone occupancy states should be shown after
                each turn.

        Returns:
            None.
        """
        self.engine = engine
        self.stream = sys.stdout if stream is None else stream
        self.color_formatter = (
            AnsiColorFormatter()
            if color_formatter is None
            else color_formatter
        )
        self.show_zone = show_zone

    def should_use_color(self) -> bool:
        """Checks whether color output should be enabled.

        Returns:
            ``True`` when the target stream is a TTY, else ``False``.
        """
        return self.stream.isatty()

    def get_target_for_drone(self, drone: Drone) -> tuple[str, str]:
        """Builds the output target token for a moved drone.

        Args:
            drone: Drone to inspect after a simulation turn.

        Returns:
            A tuple containing the printed target token and the destination
            zone name used for color lookup.

        Raises:
            ValueError: If the drone state is internally inconsistent.
        """
        if drone.is_in_restricted_move():
            origin_name = drone.restricted_origin_name
            destination_name = drone.restricted_destination_name
            if origin_name is None or destination_name is None:
                raise ValueError("invalid move")
            return f"{origin_name}-{destination_name}", destination_name

        destination_name = drone.current_zone_name
        if destination_name is None:
            raise ValueError("invalid move")
        return destination_name, destination_name

    def render_move(self, drone: Drone, use_color: bool) -> str:
        """Renders a single drone movement token.

        Args:
            drone: Drone that moved during the current turn.
            use_color: Whether ANSI coloring should be applied.

        Returns:
            Rendered token for the move.
        """
        target, destination_name = self.get_target_for_drone(drone)
        move_text = f"D{drone.drone_id}-{target}"
        if not use_color:
            return move_text

        color_name = self.engine.map_data.get_zone(destination_name).color
        return self.color_formatter.colorize(move_text, color_name)

    def render_zone_states(self, use_color: bool) -> str:
        """Renders the current zone occupancy summary.

        Args:
            use_color: Whether ANSI coloring should be applied.

        Returns:
            Human-readable zone occupancy line for the current turn.
        """
        zone_states = []
        for zone_load in self.engine.map_load.zones:
            zone_state = zone_load.to_state_text()
            if use_color:
                color_name = self.engine.map_data.get_zone(
                    zone_load.zone_name
                ).color
                zone_state = self.color_formatter.colorize(
                    zone_state,
                    color_name,
                )
            zone_states.append(zone_state)
        return "Zone states: " + ", ".join(zone_states)

    def render(self) -> list[str]:
        """Runs the simulation and renders all output lines.

        Returns:
            Ordered output lines for the full simulation. When
            ``show_zone`` is enabled, an additional zone-state line is
            emitted after each movement line.

        Raises:
            SimulationError: If the simulation becomes blocked.
        """
        lines = []
        use_color = self.should_use_color()

        while not self.engine.all_drones_arrived():
            moved_drones = self.engine.run_turn()
            if not moved_drones:
                raise SimulationError("simulation blocked")

            move_texts = [
                self.render_move(drone, use_color)
                for drone in moved_drones
            ]
            lines.append(" ".join(move_texts))
            if self.show_zone:
                lines.append(self.render_zone_states(use_color))

        return lines
