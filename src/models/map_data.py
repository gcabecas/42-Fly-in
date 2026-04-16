from .connection import Connection
from .zone import Zone
from .zone_type import ZoneType


class MapData:
    """Holds the parsed graph, hubs, and movement metadata."""

    def __init__(
        self,
        drone_count: int,
        start_hub: Zone,
        end_hub: Zone,
        hubs: list[Zone],
        connections: list[Connection],
    ) -> None:
        """Initializes parsed map data.

        Args:
            drone_count: Number of drones to simulate.
            start_hub: Unique start zone.
            end_hub: Unique end zone.
            hubs: Non-terminal zones.
            connections: Bidirectional graph edges.

        Returns:
            None.
        """
        self.drone_count = drone_count
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.hubs = hubs
        self.connections = connections

    def get_zone(self, name: str) -> Zone:
        """Returns a zone by name.

        Args:
            name: Zone name to resolve.

        Returns:
            Matching zone instance.

        Raises:
            ValueError: If the zone does not exist.
        """
        if self.start_hub.name == name:
            return self.start_hub
        if self.end_hub.name == name:
            return self.end_hub
        for hub in self.hubs:
            if hub.name == name:
                return hub
        raise ValueError("unknown zone")

    def get_neighbors(self, name: str) -> list[Zone]:
        """Lists adjacent zones for a given zone name.

        Args:
            name: Zone name to inspect.

        Returns:
            Neighboring zones connected to the given zone.
        """
        neighbors = []
        for connection in self.connections:
            if connection.start_name == name:
                neighbors.append(self.get_zone(connection.end_name))
                continue
            if connection.end_name == name:
                neighbors.append(self.get_zone(connection.start_name))
        return neighbors

    def are_connected(self, first_name: str, second_name: str) -> bool:
        """Checks whether two zones share a direct connection.

        Args:
            first_name: First zone name.
            second_name: Second zone name.

        Returns:
            ``True`` if the zones are directly connected, else ``False``.
        """
        for connection in self.connections:
            if connection.start_name == first_name:
                if connection.end_name == second_name:
                    return True
            if connection.start_name == second_name:
                if connection.end_name == first_name:
                    return True
        return False

    def get_connection_capacity(
        self,
        first_name: str,
        second_name: str,
    ) -> int:
        """Returns the capacity of a connection.

        Args:
            first_name: First connected zone name.
            second_name: Second connected zone name.

        Returns:
            Maximum simultaneous drones allowed on the connection.

        Raises:
            ValueError: If the connection does not exist.
        """
        for connection in self.connections:
            if connection.start_name == first_name:
                if connection.end_name == second_name:
                    return connection.max_link_capacity
            if connection.start_name == second_name:
                if connection.end_name == first_name:
                    return connection.max_link_capacity
        raise ValueError("unknown connection")

    def get_zone_entry_cost(self, name: str) -> int:
        """Returns the turn cost to enter a zone.

        Args:
            name: Destination zone name.

        Returns:
            Entry cost in turns.

        Raises:
            ValueError: If the zone is blocked.
        """
        zone = self.get_zone(name)
        if zone.zone_type == ZoneType.RESTRICTED:
            return 2
        if zone.zone_type == ZoneType.BLOCKED:
            raise ValueError("blocked zone")
        return 1
