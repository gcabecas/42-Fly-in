from src.errors import SimulationError
from src.models import Drone
from src.models import MapData

ConnectionKey = tuple[str, str]
ConnectionUsage = dict[ConnectionKey, int]
RestrictedArrivals = dict[str, int]
ZoneOccupancy = dict[str, int]


class SimulationState:
    """Tracks mutable per-turn occupancy, arrivals, and link usage."""

    def __init__(
        self,
        map_data: MapData,
        drones: list[Drone],
    ) -> None:
        """Initializes per-turn simulation bookkeeping.

        Args:
            map_data: Parsed map graph and metadata.
            drones: Current drone states.

        Returns:
            None.
        """
        self.map_data = map_data
        self.zone_occupancy: ZoneOccupancy = {}
        self.arriving_restricted_drone_ids: set[int] = set()
        self.current_turn_restricted_arrivals: RestrictedArrivals = {}
        self.next_turn_restricted_arrivals: RestrictedArrivals = {}
        self.connection_usage: ConnectionUsage = {}
        self.load_drones(drones)

    def load_drones(self, drones: list[Drone]) -> None:
        """Builds all current occupancy, arrival, and link counters.

        Args:
            drones: Current drone states.

        Returns:
            None.
        """
        for drone in drones:
            zone_name = drone.current_zone_name
            if zone_name is not None:
                self.zone_occupancy[zone_name] = (
                    self.zone_occupancy.get(zone_name, 0) + 1
                )

            destination_name = drone.restricted_destination_name
            if destination_name is None:
                continue

            self.arriving_restricted_drone_ids.add(drone.drone_id)
            self.current_turn_restricted_arrivals[destination_name] = (
                self.current_turn_restricted_arrivals.get(
                    destination_name,
                    0,
                )
                + 1
            )

            origin_name = drone.restricted_origin_name
            if origin_name is None:
                continue
            connection_key = self.get_connection_key(
                origin_name,
                destination_name,
            )
            self.connection_usage[connection_key] = (
                self.connection_usage.get(connection_key, 0) + 1
            )

    def get_zone_capacity(self, zone_name: str) -> int:
        """Returns the effective capacity of a zone.

        Args:
            zone_name: Zone name to inspect.

        Returns:
            Maximum simultaneous drones allowed in the zone.
        """
        if zone_name == self.map_data.start_hub.name:
            return self.map_data.drone_count
        if zone_name == self.map_data.end_hub.name:
            return self.map_data.drone_count
        return self.map_data.get_zone(zone_name).max_drones

    def can_enter_zone(
        self,
        zone_name: str,
        reserved_arrivals: RestrictedArrivals | None = None,
    ) -> bool:
        """Checks whether a zone can accept another drone.

        Args:
            zone_name: Destination zone name.
            reserved_arrivals: Additional arrivals already reserved.

        Returns:
            ``True`` if the zone has room, else ``False``.
        """
        current_occupancy = self.zone_occupancy.get(zone_name, 0)
        pending_arrivals = 0
        if reserved_arrivals is not None:
            pending_arrivals = reserved_arrivals.get(zone_name, 0)
        return (
            current_occupancy + pending_arrivals
            < self.get_zone_capacity(zone_name)
        )

    def get_connection_key(
        self,
        first_zone_name: str,
        second_zone_name: str,
    ) -> ConnectionKey:
        """Builds a canonical key for connection usage tracking.

        Args:
            first_zone_name: First zone name.
            second_zone_name: Second zone name.

        Returns:
            Ordered connection key.
        """
        if first_zone_name <= second_zone_name:
            return (first_zone_name, second_zone_name)
        return (second_zone_name, first_zone_name)

    def can_use_connection(
        self,
        first_zone_name: str,
        second_zone_name: str,
    ) -> bool:
        """Checks whether a connection still has free capacity.

        Args:
            first_zone_name: First zone name.
            second_zone_name: Second zone name.

        Returns:
            ``True`` if the connection can be used this turn.
        """
        connection_key = self.get_connection_key(
            first_zone_name,
            second_zone_name,
        )
        current_usage = self.connection_usage.get(connection_key, 0)
        max_capacity = self.map_data.get_connection_capacity(
            first_zone_name,
            second_zone_name,
        )
        return current_usage < max_capacity

    def resolve_restricted_arrivals(
        self,
        drones: list[Drone],
    ) -> list[Drone]:
        """Finishes all restricted moves scheduled for this turn.

        Args:
            drones: Current drone states.

        Returns:
            Drones that completed their restricted move this turn.

        Raises:
            SimulationError: If a restricted move cannot be completed.
        """
        arrived_drones = []
        for drone in drones:
            if drone.drone_id not in self.arriving_restricted_drone_ids:
                continue
            destination_name = drone.restricted_destination_name
            if destination_name is None:
                continue
            if not self.can_enter_zone(destination_name):
                raise SimulationError(
                    "restricted move cannot reach its destination",
                )
            drone.finish_restricted_move()
            self.zone_occupancy[destination_name] = (
                self.zone_occupancy.get(destination_name, 0) + 1
            )
            self.current_turn_restricted_arrivals[destination_name] -= 1
            if self.current_turn_restricted_arrivals[destination_name] == 0:
                del self.current_turn_restricted_arrivals[
                    destination_name
                ]
            arrived_drones.append(drone)
        return arrived_drones

    def can_start_restricted_move(
        self,
        destination_name: str,
    ) -> bool:
        """Checks whether a restricted move can start safely.

        Args:
            destination_name: Restricted destination zone name.

        Returns:
            ``True`` if the drone can commit to the move.
        """
        current_turn_reserved = self.current_turn_restricted_arrivals.get(
            destination_name,
            0,
        )
        next_turn_reserved = self.next_turn_restricted_arrivals.get(
            destination_name,
            0,
        )
        projected_end_of_turn_occupancy = (
            self.zone_occupancy.get(destination_name, 0)
            + current_turn_reserved
        )
        max_capacity = self.get_zone_capacity(destination_name)
        return (
            projected_end_of_turn_occupancy + next_turn_reserved
            < max_capacity
        )

    def apply_movement(
        self,
        current_zone_name: str,
        destination_name: str,
        starts_restricted_move: bool,
    ) -> None:
        """Applies one accepted movement to zone and link counters.

        Args:
            current_zone_name: Zone being left.
            destination_name: Destination zone being entered or targeted.
            starts_restricted_move: Whether the move starts a restricted move.

        Returns:
            None.
        """
        self.zone_occupancy[current_zone_name] -= 1
        if starts_restricted_move:
            self.next_turn_restricted_arrivals[destination_name] = (
                self.next_turn_restricted_arrivals.get(
                    destination_name,
                    0,
                )
                + 1
            )
        else:
            self.zone_occupancy[destination_name] = (
                self.zone_occupancy.get(destination_name, 0) + 1
            )

        connection_key = self.get_connection_key(
            current_zone_name,
            destination_name,
        )
        self.connection_usage[connection_key] = (
            self.connection_usage.get(connection_key, 0) + 1
        )
