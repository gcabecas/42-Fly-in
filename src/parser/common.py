from pathlib import Path
from typing import NamedTuple

from src.errors import ParseError


class SourceLine(NamedTuple):
    """Represents a meaningful source line in the input map.

    Attributes:
        number: Original line number in the source file.
        text: Raw line content without the trailing newline.
    """

    number: int
    text: str


def read_lines(map_path: Path) -> list[SourceLine]:
    """Reads non-comment lines from a map file.

    Args:
        map_path: Path to the map file.

    Returns:
        Parsed source lines preserved with their original numbers.
    """
    lines = []
    with map_path.open("r") as file:
        for number, raw_line in enumerate(file, start=1):
            line = raw_line.removesuffix("\n")
            if not line or line.startswith("#"):
                continue
            lines.append(SourceLine(number, line))
    return lines


def read_line_type(line: SourceLine) -> str:
    """Determines the semantic type of a source line.

    Args:
        line: Source line to inspect.

    Returns:
        One of ``start_hub``, ``end_hub``, ``hub``, or ``connection``.

    Raises:
        ParseError: If the line does not match the expected grammar.
    """
    stripped_text = line.text.strip()
    if not stripped_text:
        raise ParseError(
            "blank lines must be completely empty",
            line.number,
        )
    if stripped_text.startswith("#") and not line.text.startswith("#"):
        raise ParseError(
            "comments must start with '#' at column 1",
            line.number,
        )
    if line.text.startswith("start_hub:"):
        return "start_hub"
    if line.text.startswith("end_hub:"):
        return "end_hub"
    if line.text.startswith("hub:"):
        return "hub"
    if line.text.startswith("connection:"):
        return "connection"
    raise ParseError("unknown line type", line.number)


def parse_positive_int(
    value: str,
    line_number: int,
    message: str,
) -> int:
    """Parses a positive integer from text.

    Args:
        value: Raw numeric string.
        line_number: Line number used for error reporting.
        message: Error message emitted on failure.

    Returns:
        Parsed positive integer.

    Raises:
        ParseError: If the value is not a positive integer.
    """
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise ParseError(message, line_number) from error
    if parsed_value <= 0:
        raise ParseError(message, line_number)
    return parsed_value


def split_metadata_block(
    line: SourceLine,
    kind: str,
) -> tuple[str, str | None]:
    """Separates a declaration from its metadata block.

    Args:
        line: Source line being parsed.
        kind: Logical declaration kind for error messages.

    Returns:
        Tuple containing the declaration text and optional metadata.

    Raises:
        ParseError: If the metadata block syntax is invalid.
    """
    text = line.text
    invalid_message = f"invalid {kind} metadata block"
    if "[" not in text and "]" not in text:
        return text, None
    if "[" not in text or "]" not in text:
        raise ParseError(invalid_message, line.number)
    if text.count("[") != 1 or text.count("]") != 1:
        raise ParseError(invalid_message, line.number)

    start = text.index("[")
    end = text.index("]")
    if end < start:
        raise ParseError(invalid_message, line.number)
    if text[end + 1:].strip():
        raise ParseError(
            f"unexpected characters after {kind} metadata block",
            line.number,
        )
    return text[:start].rstrip(), text[start + 1:end].strip()


def split_metadata_items(
    metadata: str | None,
    line_number: int,
    kind: str,
) -> list[tuple[str, str]]:
    """Splits metadata into ``key=value`` items.

    Args:
        metadata: Raw metadata string without surrounding brackets.
        line_number: Line number used for error reporting.
        kind: Logical declaration kind for error messages.

    Returns:
        Ordered metadata items as key-value pairs.

    Raises:
        ParseError: If the metadata contains invalid or duplicate items.
    """
    if not metadata:
        return []

    items = []
    seen_keys = set()
    for raw_item in metadata.split():
        if raw_item.count("=") != 1:
            raise ParseError(
                f"invalid {kind} metadata '{raw_item}'",
                line_number,
            )
        key, value = raw_item.split("=", 1)
        if not key or not value:
            raise ParseError(
                f"invalid {kind} metadata '{raw_item}'",
                line_number,
            )
        if key in seen_keys:
            raise ParseError(
                f"duplicate {kind} metadata '{key}'",
                line_number,
            )
        seen_keys.add(key)
        items.append((key, value))
    return items
