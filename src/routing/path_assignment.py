from src.errors import RoutingError
from src.models import Drone
from src.models import MapData
from src.models import Zone

from .path_finder import PathFinder


class PathAssigner:
    """Assigns drones to candidate paths while balancing resource usage."""

    def __init__(
        self,
        map_data: MapData,
        path_finder: PathFinder | None = None,
    ) -> None:
        """Initializes a path assigner.

        Args:
            map_data: Parsed map graph and metadata.
            path_finder: Optional path finder to reuse.

        Returns:
            None.
        """
        self.map_data = map_data
        self.path_finder = (
            PathFinder(map_data)
            if path_finder is None
            else path_finder
        )

    def get_connection_key(
        self,
        first_zone_name: str,
        second_zone_name: str,
    ) -> tuple[str, ...]:
        """Builds a canonical resource key for a connection.

        Args:
            first_zone_name: First zone name.
            second_zone_name: Second zone name.

        Returns:
            Tuple key identifying the connection resource.
        """
        if first_zone_name <= second_zone_name:
            return ("connection", first_zone_name, second_zone_name)
        return ("connection", second_zone_name, first_zone_name)

    def get_path_resource_keys(
        self,
        path: list[Zone],
    ) -> list[tuple[str, ...]]:
        """Lists constrained resources touched by a path.

        Args:
            path: Ordered zone path.

        Returns:
            Resource keys for zones and connections used by the path.
        """
        resource_keys = []
        start_name = self.map_data.start_hub.name
        end_name = self.map_data.end_hub.name

        for previous_zone, zone in zip(path, path[1:]):
            resource_keys.append(
                self.get_connection_key(
                    previous_zone.name,
                    zone.name,
                )
            )
            if zone.name not in (start_name, end_name):
                resource_keys.append(("zone", zone.name))

        return resource_keys

    def get_resource_interval(
        self,
        resource_key: tuple[str, ...],
    ) -> float:
        """Computes the spacing pressure induced by a resource.

        Args:
            resource_key: Zone or connection resource key.

        Returns:
            Delay interval associated with the resource capacity.
        """
        if resource_key[0] == "zone":
            zone_name = resource_key[1]
            return self.map_data.get_zone_entry_cost(zone_name) / (
                self.map_data.get_zone(zone_name).max_drones
            )

        return 1.0 / self.map_data.get_connection_capacity(
            resource_key[1],
            resource_key[2],
        )

    def get_path_score(
        self,
        path: list[Zone],
        resource_loads: dict[tuple[str, ...], int],
    ) -> tuple[float, float, int, int, tuple[str, ...]]:
        """Scores a path for assignment using current resource loads.

        Args:
            path: Candidate path for a drone.
            resource_loads: Current estimated load per resource.

        Returns:
            Score tuple used to compare candidate paths.
        """
        delay = 0.0
        for resource_key in self.get_path_resource_keys(path):
            delay = max(
                delay,
                resource_loads.get(resource_key, 0)
                * self.get_resource_interval(resource_key),
            )

        return (
            self.path_finder.get_path_cost(path) + delay,
            delay,
            self.path_finder.get_path_priority_score(path),
            len(path),
            self.path_finder.get_path_names(path),
        )

    def build_paths_by_drone_id(
        self,
        drones: list[Drone],
    ) -> dict[int, list[Zone]]:
        """Assigns a path to each drone.

        Args:
            drones: Drones to route through the map.

        Returns:
            Mapping of drone ids to chosen paths.

        Raises:
            RoutingError: If no candidate path exists.
        """
        candidate_paths = self.path_finder.find_candidate_paths()
        if not candidate_paths:
            raise RoutingError(
                "no valid path from start_hub to end_hub"
            )

        paths_by_drone_id = {}
        resource_loads: dict[tuple[str, ...], int] = {}
        for drone in sorted(drones, key=lambda drone: drone.drone_id):
            best_path = min(
                candidate_paths,
                key=lambda path: self.get_path_score(
                    path,
                    resource_loads,
                ),
            )
            paths_by_drone_id[drone.drone_id] = best_path
            for resource_key in self.get_path_resource_keys(best_path):
                resource_loads[resource_key] = (
                    resource_loads.get(resource_key, 0) + 1
                )

        return paths_by_drone_id
