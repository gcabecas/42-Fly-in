class Connection:
    """Represents a bidirectional connection between two zones."""

    def __init__(
        self,
        start_name: str,
        end_name: str,
        max_link_capacity: int = 1,
    ) -> None:
        """Initializes a connection.

        Args:
            start_name: First connected zone name.
            end_name: Second connected zone name.
            max_link_capacity: Maximum simultaneous drones on the link.

        Returns:
            None.
        """
        self.start_name = start_name
        self.end_name = end_name
        self.max_link_capacity = max_link_capacity
