from src.models import MapData
from src.models import Zone
from src.models import ZoneType

PathNames = tuple[str, ...]
PathScore = tuple[int, int]


class PathFinder:
    """Finds candidate paths through the zone graph."""

    def __init__(self, map_data: MapData) -> None:
        """Initializes a path finder for a parsed map.

        Args:
            map_data: Parsed map graph and metadata.

        Returns:
            None.
        """
        self.map_data = map_data

    def pop_best_frontier_item(
        self,
        frontier: list[tuple[int, int, str]],
    ) -> tuple[int, int, str]:
        """Removes the best item from a simple frontier list.

        Args:
            frontier: Candidate nodes with their scores.

        Returns:
            The frontier item with the smallest score tuple.
        """
        best_index = 0
        for index in range(1, len(frontier)):
            if frontier[index] < frontier[best_index]:
                best_index = index
        return frontier.pop(best_index)

    def rebuild_path(
        self,
        previous_by_name: dict[str, str | None],
        end_name: str,
    ) -> list[Zone]:
        """Rebuilds a path from predecessor links.

        Args:
            previous_by_name: Previous zone map built during search.
            end_name: Name of the destination zone.

        Returns:
            Ordered path from start to end.
        """
        path_names = []
        current_name: str | None = end_name
        while current_name is not None:
            path_names.append(current_name)
            current_name = previous_by_name[current_name]
        path_names.reverse()
        return [self.map_data.get_zone(name) for name in path_names]

    def get_path_names(self, path: list[Zone]) -> PathNames:
        """Converts a zone path into a tuple of names.

        Args:
            path: Ordered list of zones.

        Returns:
            Tuple of zone names.
        """
        return tuple(zone.name for zone in path)

    def get_path_cost(self, path: list[Zone]) -> int:
        """Computes the weighted traversal cost of a path.

        Args:
            path: Ordered list of zones.

        Returns:
            Total zone entry cost excluding the start zone.
        """
        return sum(
            self.map_data.get_zone_entry_cost(zone.name)
            for zone in path[1:]
        )

    def get_path_priority_score(self, path: list[Zone]) -> int:
        """Scores a path by how many priority zones it uses.

        Args:
            path: Ordered list of zones.

        Returns:
            Negative count of priority zones to favor them in sorting.
        """
        return -sum(
            zone.zone_type == ZoneType.PRIORITY
            for zone in path[1:]
        )

    def find_shortest_path(
        self,
        excluded_names: set[str] | None = None,
    ) -> list[Zone]:
        """Finds the best path while excluding selected zone names.

        Args:
            excluded_names: Zone names temporarily forbidden during search.

        Returns:
            Best path from start to end under the current exclusions.

        Raises:
            ValueError: If no valid path can be found.
        """
        start_name = self.map_data.start_hub.name
        end_name = self.map_data.end_hub.name
        best_scores: dict[str, PathScore] = {start_name: (0, 0)}
        previous_by_name: dict[str, str | None] = {start_name: None}
        frontier = [(0, 0, start_name)]
        forbidden_names = (
            excluded_names if excluded_names is not None else set()
        )

        while frontier:
            current_cost, current_priority_score, current_name = (
                self.pop_best_frontier_item(frontier)
            )
            current_score: PathScore = (
                current_cost,
                current_priority_score,
            )
            if current_score != best_scores.get(current_name):
                continue
            if current_name == end_name:
                return self.rebuild_path(previous_by_name, end_name)

            for neighbor in self.map_data.get_neighbors(current_name):
                if neighbor.name in forbidden_names:
                    continue
                try:
                    step_cost = self.map_data.get_zone_entry_cost(
                        neighbor.name
                    )
                except ValueError:
                    continue

                new_score = (
                    current_cost + step_cost,
                    current_priority_score
                    - int(
                        neighbor.zone_type == ZoneType.PRIORITY
                    ),
                )
                best_neighbor_score = best_scores.get(neighbor.name)
                if (
                    best_neighbor_score is not None
                    and new_score >= best_neighbor_score
                ):
                    continue
                best_scores[neighbor.name] = new_score
                previous_by_name[neighbor.name] = current_name
                frontier.append(
                    (new_score[0], new_score[1], neighbor.name)
                )

        raise ValueError("no path found")

    def find_candidate_paths(self) -> list[list[Zone]]:
        """Generates a ranked set of useful candidate paths.

        Returns:
            Candidate paths sorted by cost, priority usage, and shape.
        """
        limit = min(
            max(3, self.map_data.drone_count),
            len(self.map_data.hubs) + 2,
        )
        explore_limit = max(limit * 4, limit + 4)
        candidates: dict[PathNames, list[Zone]] = {}
        pending_exclusions: list[frozenset[str]] = [frozenset()]
        seen_exclusions: set[frozenset[str]] = {frozenset()}
        index = 0

        while (
            index < len(pending_exclusions)
            and len(candidates) < explore_limit
        ):
            excluded_names = pending_exclusions[index]
            index += 1
            try:
                candidate = self.find_shortest_path(
                    excluded_names=set(excluded_names),
                )
            except ValueError:
                continue

            candidate_names = self.get_path_names(candidate)
            if candidate_names in candidates:
                continue
            candidates[candidate_names] = candidate

            for zone in candidate[1:-1]:
                next_exclusions = frozenset(
                    set(excluded_names) | {zone.name}
                )
                if next_exclusions in seen_exclusions:
                    continue
                seen_exclusions.add(next_exclusions)
                pending_exclusions.append(next_exclusions)

        return sorted(
            candidates.values(),
            key=lambda path: (
                self.get_path_cost(path),
                self.get_path_priority_score(path),
                len(path),
                self.get_path_names(path),
            ),
        )[:limit]
