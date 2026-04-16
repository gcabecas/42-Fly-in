from src.models import Drone
from src.models import MapData
from src.models import Zone


class AssignedPaths:
    """Stores validated per-drone paths and their current progress."""

    def __init__(
        self,
        map_data: MapData,
        drones: list[Drone],
        paths_by_drone_id: dict[int, list[Zone]] | None = None,
    ) -> None:
        """Initializes and validates the assigned paths for each drone.

        Args:
            map_data: Parsed map graph and metadata.
            drones: Drones that will consume the assigned paths.
            paths_by_drone_id: Precomputed path per drone.

        Returns:
            None.

        Raises:
            ValueError: If an assigned path is invalid.
        """
        self.paths_by_drone_id = (
            paths_by_drone_id if paths_by_drone_id is not None else {}
        )
        self.path_indexes_by_drone_id: dict[int, int] = {}
        self.validate_paths(map_data, drones)

    def validate_paths(
        self,
        map_data: MapData,
        drones: list[Drone],
    ) -> None:
        """Validates every assigned path and initializes its progress.

        Args:
            map_data: Parsed map graph and metadata.
            drones: Drones that will consume the assigned paths.

        Returns:
            None.

        Raises:
            ValueError: If an assigned path is invalid.
        """
        for drone in drones:
            path = self.paths_by_drone_id.get(drone.drone_id)
            if path is None:
                continue
            self.validate_path(map_data, drone, path)
            self.path_indexes_by_drone_id[drone.drone_id] = 0

    def validate_path(
        self,
        map_data: MapData,
        drone: Drone,
        path: list[Zone],
    ) -> None:
        """Validates a single assigned path for one drone.

        Args:
            map_data: Parsed map graph and metadata.
            drone: Drone receiving the path.
            path: Assigned path to validate.

        Returns:
            None.

        Raises:
            ValueError: If the path is invalid for the drone.
        """
        if not path:
            raise ValueError("invalid path")
        if path[0].name != drone.current_zone_name:
            raise ValueError("invalid path")
        if path[-1].name != drone.end_zone_name:
            raise ValueError("invalid path")

        previous_zone = path[0]
        for zone in path[1:]:
            if not map_data.are_connected(
                previous_zone.name,
                zone.name,
            ):
                raise ValueError("invalid path")
            try:
                map_data.get_zone_entry_cost(zone.name)
            except ValueError as error:
                raise ValueError("invalid path") from error
            previous_zone = zone

    def get_next_zone_name(self, drone: Drone) -> str | None:
        """Returns the next planned zone for a drone.

        Args:
            drone: Drone to inspect.

        Returns:
            Next zone name, or ``None`` if the path is finished.
        """
        path = self.paths_by_drone_id.get(drone.drone_id)
        if path is None:
            return None

        current_index = self.path_indexes_by_drone_id[drone.drone_id]
        next_index = current_index + 1
        if next_index >= len(path):
            return None
        return path[next_index].name

    def advance(self, drone_id: int) -> None:
        """Advances a drone path to its next step.

        Args:
            drone_id: Drone identifier to update.

        Returns:
            None.
        """
        self.path_indexes_by_drone_id[drone_id] += 1
