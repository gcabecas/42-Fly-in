from src.errors import ParseError
from src.models import Connection

from .common import SourceLine
from .common import parse_positive_int
from .common import split_metadata_block
from .common import split_metadata_items


def parse_connection_base_line(
    line: str,
    line_number: int,
) -> tuple[str, str]:
    """Parses the non-metadata portion of a connection line.

    Args:
        line: Declaration text without metadata.
        line_number: Line number used for error reporting.

    Returns:
        Start and end zone names.

    Raises:
        ParseError: If the connection syntax is invalid.
    """
    if not line.startswith("connection:"):
        raise ParseError("invalid connection declaration", line_number)

    value = line.removeprefix("connection:").strip()
    if value.count("-") != 1:
        raise ParseError(
            "invalid connection syntax, expected '<zone1>-<zone2>'",
            line_number,
        )
    start_name, end_name = value.split("-", 1)
    if not start_name or not end_name:
        raise ParseError(
            "invalid connection syntax, expected '<zone1>-<zone2>'",
            line_number,
        )
    if start_name == end_name:
        raise ParseError(
            "connection cannot link a zone to itself",
            line_number,
        )
    return start_name, end_name


def parse_connection_metadata(
    metadata: str | None,
    line_number: int,
) -> int:
    """Parses connection metadata.

    Args:
        metadata: Optional metadata string.
        line_number: Line number used for error reporting.

    Returns:
        Maximum capacity for the connection.

    Raises:
        ParseError: If the metadata is invalid.
    """
    max_link_capacity = 1
    for key, value in split_metadata_items(
        metadata,
        line_number,
        "connection",
    ):
        if key != "max_link_capacity":
            raise ParseError(
                f"unknown connection metadata '{key}'",
                line_number,
            )
        max_link_capacity = parse_positive_int(
            value,
            line_number,
            "max_link_capacity must be a positive integer",
        )
    return max_link_capacity


def parse_connection_line(line: SourceLine) -> Connection:
    """Parses a full connection declaration line.

    Args:
        line: Source line to parse.

    Returns:
        Parsed connection object.

    Raises:
        ParseError: If the line is invalid.
    """
    base_line, metadata = split_metadata_block(
        line,
        "connection",
    )
    start_name, end_name = parse_connection_base_line(
        base_line,
        line.number,
    )
    max_link_capacity = parse_connection_metadata(
        metadata,
        line.number,
    )
    return Connection(
        start_name=start_name,
        end_name=end_name,
        max_link_capacity=max_link_capacity,
    )


def get_connection_name(
    first_zone_name: str,
    second_zone_name: str,
) -> tuple[str, str]:
    """Builds a canonical connection key.

    Args:
        first_zone_name: First zone name.
        second_zone_name: Second zone name.

    Returns:
        Ordered connection key used for duplicate detection.
    """
    if first_zone_name <= second_zone_name:
        return (first_zone_name, second_zone_name)
    return (second_zone_name, first_zone_name)
