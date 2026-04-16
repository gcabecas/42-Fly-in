class ZoneLoad:
    """Stores the current occupancy state of a zone."""

    def __init__(
        self,
        zone_name: str,
        current_occupancy: int,
        max_capacity: int,
    ) -> None:
        """Initializes a zone load snapshot.

        Args:
            zone_name: Name of the tracked zone.
            current_occupancy: Number of drones currently in the zone.
            max_capacity: Maximum number of drones allowed in the zone.

        Returns:
            None.
        """
        self.zone_name = zone_name
        self.current_occupancy = current_occupancy
        self.max_capacity = max_capacity

    def to_state_text(self) -> str:
        """Formats the zone load as a compact state fragment.

        Returns:
            Compact ``name=current/max`` description for one zone.
        """
        return (
            f"{self.zone_name}="
            f"{self.current_occupancy}/{self.max_capacity}"
        )


class ConnectionLoad:
    """Stores the current usage state of a connection."""

    def __init__(
        self,
        start_name: str,
        end_name: str,
        current_usage: int,
        max_capacity: int,
    ) -> None:
        """Initializes a connection load snapshot.

        Args:
            start_name: First zone name of the connection.
            end_name: Second zone name of the connection.
            current_usage: Number of drones currently using the connection.
            max_capacity: Maximum simultaneous usage of the connection.

        Returns:
            None.
        """
        self.start_name = start_name
        self.end_name = end_name
        self.current_usage = current_usage
        self.max_capacity = max_capacity


class MapLoad:
    """Aggregates current zone occupancy and connection usage."""

    def __init__(self) -> None:
        """Initializes an empty map load snapshot.

        Returns:
            None.
        """
        self.zones: list[ZoneLoad] = []
        self.connections: list[ConnectionLoad] = []

    def clear(self) -> None:
        """Clears all stored load entries.

        Returns:
            None.
        """
        self.zones.clear()
        self.connections.clear()

    def add_zone(
        self,
        zone_name: str,
        current_occupancy: int,
        max_capacity: int,
    ) -> None:
        """Appends a zone load entry.

        Args:
            zone_name: Name of the tracked zone.
            current_occupancy: Number of drones currently in the zone.
            max_capacity: Maximum number of drones allowed in the zone.

        Returns:
            None.
        """
        self.zones.append(
            ZoneLoad(
                zone_name,
                current_occupancy,
                max_capacity,
            )
        )

    def add_connection(
        self,
        start_name: str,
        end_name: str,
        current_usage: int,
        max_capacity: int,
    ) -> None:
        """Appends a connection load entry.

        Args:
            start_name: First zone name of the connection.
            end_name: Second zone name of the connection.
            current_usage: Number of drones currently using the connection.
            max_capacity: Maximum simultaneous usage of the connection.

        Returns:
            None.
        """
        self.connections.append(
            ConnectionLoad(
                start_name,
                end_name,
                current_usage,
                max_capacity,
            )
        )

    def get_zone(self, zone_name: str) -> ZoneLoad:
        """Returns the stored load for a zone.

        Args:
            zone_name: Name of the zone to resolve.

        Returns:
            Matching zone load entry.

        Raises:
            ValueError: If the zone load does not exist.
        """
        for zone_load in self.zones:
            if zone_load.zone_name == zone_name:
                return zone_load
        raise ValueError("unknown zone load")

    def get_connection(
        self,
        start_name: str,
        end_name: str,
    ) -> ConnectionLoad:
        """Returns the stored load for a connection.

        Args:
            start_name: First zone name of the connection.
            end_name: Second zone name of the connection.

        Returns:
            Matching connection load entry.

        Raises:
            ValueError: If the connection load does not exist.
        """
        for connection_load in self.connections:
            if connection_load.start_name == start_name:
                if connection_load.end_name == end_name:
                    return connection_load
            if connection_load.start_name == end_name:
                if connection_load.end_name == start_name:
                    return connection_load
        raise ValueError("unknown connection load")

    def format_zone_states(self) -> str:
        """Formats all zone occupancy states on a single line.

        Returns:
            Human-readable summary of every tracked zone occupancy.
        """
        zone_states = ", ".join(
            zone_load.to_state_text()
            for zone_load in self.zones
        )
        return f"Zone states: {zone_states}"
