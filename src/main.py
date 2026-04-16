import sys
from pathlib import Path

from src.display import SimulationRenderer
from src.errors import FlyInError
from src.models import Drone
from src.parser import MapParser
from src.routing import PathAssigner
from src.simulation import SimulationEngine


def parse_cli_args(args: list[str]) -> tuple[Path, bool]:
    """Parses CLI arguments for the Fly-in entrypoint.

    Args:
        args: Full argument vector including the program name.

    Returns:
        Tuple containing the map path and whether zone states should be
        displayed after each turn.

    Raises:
        ValueError: If the CLI arguments are invalid.
    """
    show_zone = False
    map_paths = []
    for arg in args[1:]:
        if arg == "--show-zone":
            if show_zone:
                raise ValueError("duplicate --show-zone flag")
            show_zone = True
            continue
        if arg.startswith("-"):
            raise ValueError(f"unknown flag '{arg}'")
        map_paths.append(arg)

    if len(map_paths) != 1:
        raise ValueError(
            "expected exactly one map path and optional --show-zone flag"
        )

    return Path(map_paths[0]), show_zone


def main() -> int:
    """Runs the Fly-in command-line entrypoint.

    Returns:
        Exit status code for the process.
    """
    map_path = Path(".")

    try:
        map_path, show_zone = parse_cli_args(sys.argv)
        map_parser = MapParser()
        map_data = map_parser.parse(map_path)
        drones = [
            Drone(
                drone_id=drone_id,
                start_zone_name=map_data.start_hub.name,
                end_zone_name=map_data.end_hub.name,
            )
            for drone_id in range(1, map_data.drone_count + 1)
        ]
        path_assigner = PathAssigner(map_data)
        engine = SimulationEngine(
            map_data,
            drones,
            path_assigner.build_paths_by_drone_id(drones),
        )
        renderer = SimulationRenderer(engine, show_zone=show_zone)
        for line in renderer.render():
            print(line)
        return 0
    except OSError as error:
        print(
            f"Error: cannot read {map_path}: {error.strerror}",
            file=sys.stderr,
        )
        return 1
    except FlyInError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(
            f"Error: unexpected internal error: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
