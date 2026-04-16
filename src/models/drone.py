class Drone:
    """Stores the mutable state of a drone during simulation."""

    def __init__(
        self,
        drone_id: int,
        start_zone_name: str,
        end_zone_name: str,
    ) -> None:
        """Initializes a drone at the start zone.

        Args:
            drone_id: Unique positive drone identifier.
            start_zone_name: Name of the initial zone.
            end_zone_name: Name of the destination zone.

        Returns:
            None.

        Raises:
            ValueError: If the drone definition is invalid.
        """
        if drone_id <= 0:
            raise ValueError("invalid drone")
        if not start_zone_name:
            raise ValueError("invalid drone")
        if not end_zone_name:
            raise ValueError("invalid drone")

        self.drone_id = drone_id
        self.current_zone_name: str | None = start_zone_name
        self.end_zone_name = end_zone_name
        self.restricted_origin_name: str | None = None
        self.restricted_destination_name: str | None = None

    def move_to(self, zone_name: str) -> None:
        """Moves the drone directly into a zone.

        Args:
            zone_name: Destination zone name.

        Returns:
            None.

        Raises:
            ValueError: If the destination is invalid.
        """
        if not zone_name:
            raise ValueError("invalid drone")
        self.current_zone_name = zone_name

    def start_restricted_move(self, destination_name: str) -> None:
        """Starts a restricted multi-turn move.

        Args:
            destination_name: Restricted destination zone name.

        Returns:
            None.

        Raises:
            ValueError: If the drone is not in a movable state.
        """
        if self.current_zone_name is None:
            raise ValueError("invalid drone")
        if not destination_name:
            raise ValueError("invalid drone")
        self.restricted_origin_name = self.current_zone_name
        self.restricted_destination_name = destination_name
        self.current_zone_name = None

    def finish_restricted_move(self) -> None:
        """Completes the current restricted move.

        Returns:
            None.

        Raises:
            ValueError: If no restricted move is in progress.
        """
        if self.restricted_destination_name is None:
            raise ValueError("invalid drone")
        self.current_zone_name = self.restricted_destination_name
        self.restricted_origin_name = None
        self.restricted_destination_name = None

    def is_in_restricted_move(self) -> bool:
        """Checks whether the drone is inside a restricted move.

        Returns:
            ``True`` if the drone is in a restricted move, else ``False``.
        """
        return self.restricted_destination_name is not None

    def is_arrived(self) -> bool:
        """Checks whether the drone has reached the end zone.

        Returns:
            ``True`` if the drone is delivered, else ``False``.
        """
        if self.is_in_restricted_move():
            return False
        return self.current_zone_name == self.end_zone_name
