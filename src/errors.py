class FlyInError(Exception):
    """Base exception for Fly-in specific failures."""

    pass


class ParseError(FlyInError):
    """Represents a parsing failure, optionally tied to a source line."""

    def __init__(
        self,
        message: str,
        line_number: int | None = None,
    ) -> None:
        """Initializes a parse error.

        Args:
            message: Human-readable parsing error message.
            line_number: Source line number associated with the error.

        Returns:
            None.
        """
        self.message = message
        self.line_number = line_number
        super().__init__(str(self))

    def __str__(self) -> str:
        """Formats the parse error for display.

        Returns:
            The error message with an optional line prefix.
        """
        if self.line_number is None:
            return self.message
        return f"line {self.line_number}: {self.message}"


class RoutingError(FlyInError):
    """Represents a routing or path assignment failure."""

    pass


class SimulationError(FlyInError):
    """Represents an invalid or blocked simulation state."""

    pass
