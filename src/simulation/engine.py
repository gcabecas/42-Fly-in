from src.models import MapLoad
from src.models import Drone
from src.models import MapData
from src.models import Zone
from src.models import ZoneType
from src.simulation.routes import AssignedPaths
from src.simulation.state import SimulationState


class SimulationEngine:
    """Executes turn-by-turn drone movement on a parsed map."""

    def __init__(
        self,
        map_data: MapData,
        drones: list[Drone],
        paths_by_drone_id: dict[int, list[Zone]] | None = None,
    ) -> None:
        """Initializes a simulation engine.

        Args:
            map_data: Parsed map graph and metadata.
            drones: Drones to simulate.
            paths_by_drone_id: Precomputed path per drone.

        Returns:
            None.

        Raises:
            ValueError: If the drone list or assigned paths are invalid.
        """
        self.map_data = map_data
        drone_ids = set()
        for drone in drones:
            if drone.drone_id in drone_ids:
                raise ValueError("duplicate drone")
            drone_ids.add(drone.drone_id)
        self.drones = sorted(
            drones,
            key=lambda current_drone: current_drone.drone_id,
        )
        self.map_load = MapLoad()
        self.assigned_paths = AssignedPaths(
            self.map_data,
            self.drones,
            paths_by_drone_id,
        )
        self.update_map_load(SimulationState(self.map_data, self.drones))

    def update_map_load(
        self,
        simulation_state: SimulationState,
    ) -> None:
        """Refreshes the cached map load from the current simulation state.

        Args:
            simulation_state: Mutable state describing the current turn.

        Returns:
            None.
        """
        self.map_load.clear()

        zones = [
            self.map_data.start_hub,
            *self.map_data.hubs,
            self.map_data.end_hub,
        ]
        for zone in zones:
            self.map_load.add_zone(
                zone.name,
                simulation_state.zone_occupancy.get(zone.name, 0),
                simulation_state.get_zone_capacity(zone.name),
            )

        for connection in self.map_data.connections:
            self.map_load.add_connection(
                connection.start_name,
                connection.end_name,
                simulation_state.connection_usage.get(
                    simulation_state.get_connection_key(
                        connection.start_name,
                        connection.end_name,
                    ),
                    0,
                ),
                connection.max_link_capacity,
            )

    def all_drones_arrived(self) -> bool:
        """Checks whether the simulation is complete.

        Returns:
            ``True`` if every drone has reached the end zone.
        """
        end_hub_load = self.map_load.get_zone(self.map_data.end_hub.name)
        return end_hub_load.current_occupancy == len(self.drones)

    def apply_drone_movement(
        self,
        drone: Drone,
        destination_name: str,
        simulation_state: SimulationState,
        starts_restricted_move: bool,
    ) -> None:
        """Applies one accepted drone movement to drones and counters.

        Args:
            drone: Drone to move.
            destination_name: Destination zone being entered or targeted.
            simulation_state: Per-turn mutable simulation state.
            starts_restricted_move: Whether the move starts a restricted move.

        Returns:
            None.

        Raises:
            ValueError: If the drone state is invalid.
        """
        current_zone_name = drone.current_zone_name
        if current_zone_name is None:
            raise ValueError("invalid drone")
        if starts_restricted_move:
            drone.start_restricted_move(destination_name)
        else:
            drone.move_to(destination_name)
        simulation_state.apply_movement(
            current_zone_name,
            destination_name,
            starts_restricted_move,
        )
        self.assigned_paths.advance(drone.drone_id)

    def try_move_drone(
        self,
        drone: Drone,
        simulation_state: SimulationState,
    ) -> bool:
        """Attempts to move a drone according to its assigned path.

        Args:
            drone: Drone to move.
            simulation_state: Per-turn mutable simulation state.

        Returns:
            ``True`` if the drone moved, else ``False``.

        Raises:
            ValueError: If the drone state is invalid.
        """
        next_zone_name = self.assigned_paths.get_next_zone_name(drone)
        if next_zone_name is None:
            return False

        current_zone_name = drone.current_zone_name
        if current_zone_name is None:
            raise ValueError("invalid drone")
        if not simulation_state.can_use_connection(
            current_zone_name,
            next_zone_name,
        ):
            return False

        next_zone = self.map_data.get_zone(next_zone_name)
        starts_restricted_move = (
            next_zone.zone_type == ZoneType.RESTRICTED
        )
        if starts_restricted_move:
            if not simulation_state.can_start_restricted_move(
                next_zone_name,
            ):
                return False
        elif not simulation_state.can_enter_zone(
            next_zone_name,
            reserved_arrivals=(
                simulation_state.current_turn_restricted_arrivals
            ),
        ):
            return False

        self.apply_drone_movement(
            drone,
            next_zone_name,
            simulation_state,
            starts_restricted_move,
        )
        return True

    def run_turn(self) -> list[Drone]:
        """Runs a full simulation turn.

        Returns:
            Drones that moved during the turn, sorted by id.

        Raises:
            SimulationError: If a restricted move cannot finish.
            ValueError: If an internal drone state is invalid.
        """
        moved_drones: list[Drone] = []
        simulation_state = SimulationState(self.map_data, self.drones)

        for drone in self.drones:
            if drone.is_in_restricted_move() or drone.is_arrived():
                continue
            if self.try_move_drone(drone, simulation_state):
                moved_drones.append(drone)

        moved_drones.extend(
            simulation_state.resolve_restricted_arrivals(self.drones)
        )
        self.update_map_load(simulation_state)
        return sorted(
            moved_drones,
            key=lambda current_drone: current_drone.drone_id,
        )
