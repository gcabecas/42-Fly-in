from src.errors import ParseError
from src.models import Zone
from src.models import ZoneType

from .common import SourceLine
from .common import parse_positive_int
from .common import split_metadata_block
from .common import split_metadata_items


def validate_zone_name(
    name: str,
    line_number: int,
) -> None:
    """Validates a zone name against subject constraints.

    Args:
        name: Zone name to validate.
        line_number: Line number used for error reporting.

    Returns:
        None.

    Raises:
        ParseError: If the name is missing or contains forbidden
            characters.
    """
    if not name:
        raise ParseError("missing zone name", line_number)
    if " " in name:
        raise ParseError(
            f"zone name '{name}' cannot contain spaces",
            line_number,
        )
    if "-" in name:
        raise ParseError(
            f"zone name '{name}' cannot contain dashes",
            line_number,
        )


def parse_zone_base_line(
    line: str,
    prefix: str,
    line_number: int,
) -> tuple[str, int, int]:
    """Parses the non-metadata portion of a zone declaration.

    Args:
        line: Declaration text without metadata.
        prefix: Expected declaration prefix.
        line_number: Line number used for error reporting.

    Returns:
        Zone name and coordinates.

    Raises:
        ParseError: If the declaration syntax is invalid.
    """
    if not line.startswith(prefix):
        raise ParseError("invalid zone declaration", line_number)

    parts = line.removeprefix(prefix).strip().split()
    if len(parts) != 3:
        raise ParseError(
            "invalid zone declaration, expected '<name> <x> <y>'",
            line_number,
        )
    name = parts[0]
    validate_zone_name(name, line_number)
    try:
        x = int(parts[1])
        y = int(parts[2])
    except ValueError as error:
        raise ParseError(
            "zone coordinates must be integers",
            line_number,
        ) from error
    return name, x, y


def parse_zone_metadata(
    metadata: str | None,
    line_number: int,
) -> tuple[ZoneType, str, int]:
    """Parses zone metadata fields.

    Args:
        metadata: Optional metadata string.
        line_number: Line number used for error reporting.

    Returns:
        Zone type, color name, and zone capacity.

    Raises:
        ParseError: If any metadata entry is invalid.
    """
    zone_type = ZoneType.NORMAL
    color = "none"
    max_drones = 1

    for key, value in split_metadata_items(
        metadata,
        line_number,
        "zone",
    ):
        if key == "zone":
            try:
                zone_type = ZoneType(value)
            except ValueError as error:
                raise ParseError(
                    f"invalid zone type '{value}'",
                    line_number,
                ) from error
            continue
        if key == "color":
            color = value
            continue
        if key == "max_drones":
            max_drones = parse_positive_int(
                value,
                line_number,
                "max_drones must be a positive integer",
            )
            continue
        raise ParseError(
            f"unknown zone metadata '{key}'",
            line_number,
        )
    return zone_type, color, max_drones


def parse_zone_line(
    line: SourceLine,
    prefix: str,
) -> Zone:
    """Parses a full zone declaration line.

    Args:
        line: Source line to parse.
        prefix: Expected declaration prefix.

    Returns:
        Parsed zone object.

    Raises:
        ParseError: If the line is invalid.
    """
    base_line, metadata = split_metadata_block(line, "zone")
    name, x, y = parse_zone_base_line(
        base_line,
        prefix,
        line.number,
    )
    zone_type, color, max_drones = parse_zone_metadata(
        metadata,
        line.number,
    )
    return Zone(
        name=name,
        x=x,
        y=y,
        zone_type=zone_type,
        color=color,
        max_drones=max_drones,
    )


def register_zone(
    zone_names: set[str],
    zone_positions: dict[tuple[int, int], tuple[str, int]],
    zone: Zone,
    line_number: int,
) -> None:
    """Registers a zone and rejects duplicate names or coordinates.

    Args:
        zone_names: Set of zone names already seen.
        zone_positions: Known zone coordinates mapped to name and line.
        zone: Zone being registered.
        line_number: Line number used for error reporting.

    Returns:
        None.

    Raises:
        ParseError: If the zone name or coordinates are duplicated.
    """
    if zone.name in zone_names:
        raise ParseError(
            f"duplicate zone name '{zone.name}'",
            line_number,
        )
    position = (zone.x, zone.y)
    if position in zone_positions:
        previous_zone_name, previous_line_number = zone_positions[position]
        raise ParseError(
            "duplicate zone coordinates "
            f"({zone.x}, {zone.y}), already used by zone "
            f"'{previous_zone_name}' at line {previous_line_number}",
            line_number,
        )
    zone_names.add(zone.name)
    zone_positions[position] = (zone.name, line_number)
