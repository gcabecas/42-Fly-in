from pathlib import Path

from src.errors import ParseError
from src.models import Connection
from src.models import MapData
from src.models import Zone

from .common import SourceLine
from .common import parse_positive_int
from .common import read_line_type
from .common import read_lines
from .connections import get_connection_name
from .connections import parse_connection_line
from .zones import parse_zone_line
from .zones import register_zone


class MapParser:
    """Parses Fly-in map files into ``MapData`` objects."""

    def read_drone_count(self, lines: list[SourceLine]) -> int:
        """Reads the drone count from the first meaningful line.

        Args:
            lines: Parsed non-comment source lines.

        Returns:
            Number of drones declared in the map.

        Raises:
            ParseError: If the declaration is missing or invalid.
        """
        if not lines:
            raise ParseError("missing nb_drones declaration", 1)

        first_line = lines[0]
        if not first_line.text.startswith("nb_drones:"):
            raise ParseError(
                "expected nb_drones declaration as first non-comment line",
                first_line.number,
            )

        value = first_line.text.removeprefix("nb_drones:").strip()
        if not value:
            raise ParseError("missing nb_drones value", first_line.number)
        return parse_positive_int(
            value,
            first_line.number,
            "nb_drones must be a positive integer",
        )

    def parse(self, map_path: Path) -> MapData:
        """Parses a map file into a ``MapData`` object.

        Args:
            map_path: Path to the input map file.

        Returns:
            Fully parsed map description.

        Raises:
            ParseError: If the file content violates the map grammar.
        """
        lines = read_lines(map_path)
        drone_count = self.read_drone_count(lines)
        end_of_input_line_number = lines[-1].number
        start_hub: Zone | None = None
        end_hub: Zone | None = None
        hubs: list[Zone] = []
        connections: list[Connection] = []
        zone_names: set[str] = set()
        zone_positions: dict[tuple[int, int], tuple[str, int]] = {}
        connection_names: set[tuple[str, str]] = set()

        for line in lines[1:]:
            line_type = read_line_type(line)

            if line_type == "start_hub":
                if start_hub is not None:
                    raise ParseError(
                        "duplicate start_hub definition",
                        line.number,
                    )
                start_hub = parse_zone_line(line, "start_hub:")
                register_zone(
                    zone_names,
                    zone_positions,
                    start_hub,
                    line.number,
                )
                continue

            if line_type == "end_hub":
                if end_hub is not None:
                    raise ParseError(
                        "duplicate end_hub definition",
                        line.number,
                    )
                end_hub = parse_zone_line(line, "end_hub:")
                register_zone(
                    zone_names,
                    zone_positions,
                    end_hub,
                    line.number,
                )
                continue

            if line_type == "hub":
                hub = parse_zone_line(line, "hub:")
                register_zone(
                    zone_names,
                    zone_positions,
                    hub,
                    line.number,
                )
                hubs.append(hub)
                continue

            connection = parse_connection_line(line)
            if connection.start_name not in zone_names:
                raise ParseError(
                    "connection references unknown "
                    f"zone '{connection.start_name}'",
                    line.number,
                )
            if connection.end_name not in zone_names:
                raise ParseError(
                    "connection references unknown "
                    f"zone '{connection.end_name}'",
                    line.number,
                )
            connection_name = get_connection_name(
                connection.start_name,
                connection.end_name,
            )
            if connection_name in connection_names:
                raise ParseError(
                    "duplicate connection "
                    f"'{connection_name[0]}-{connection_name[1]}'",
                    line.number,
                )
            connection_names.add(connection_name)
            connections.append(connection)

        if start_hub is None:
            raise ParseError(
                "missing start_hub definition",
                end_of_input_line_number,
            )
        if end_hub is None:
            raise ParseError(
                "missing end_hub definition",
                end_of_input_line_number,
            )

        return MapData(
            drone_count=drone_count,
            start_hub=start_hub,
            end_hub=end_hub,
            hubs=hubs,
            connections=connections,
        )
