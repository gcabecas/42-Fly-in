*This project has been created as part of the 42 curriculum by gcabecas.*

# Fly-in

## Description

Fly-in is a Python simulation project about routing a fleet of drones through a graph of
connected zones. Each drone must travel from a unique `start_hub` to a unique
`end_hub` while respecting movement costs, zone capacities, and connection capacities.

The goal is not only to find a valid route, but to minimize the total number of
simulation turns. The project includes:

- a modular parser for the subject map format,
- a pathfinding system that takes weighted zones into account,
- a path assignment strategy for multiple drones,
- a turn-by-turn simulation engine with conflict resolution,
- a colored terminal output for visual feedback.

## Instructions

### Requirements

- Python 3.10 or newer
- `uv` for dependency management

### Installation

```bash
make install
```

This command installs the project dependencies defined in `pyproject.toml`.

### Execution

Run the default map:

```bash
make run
```

Run a specific map:

```bash
make run MAP=maps/medium/03_priority_puzzle.txt
```

You can also run the program directly:

```bash
uv run python -m src.main maps/easy/01_linear_path.txt
```

Show per-turn zone occupancy states:

```bash
uv run python -m src.main --show-zone maps/easy/01_linear_path.txt
```

### Debug

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

### Lint and Type Checking

```bash
make lint
```

Optional stricter check:

```bash
make lint-strict
```

### Clean

```bash
make clean
```

### Compilation

This project is written in Python, so there is no compilation step.

## Example Input

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

## Example Output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each output line represents one simulation turn. Drones that do not move during a turn
are omitted from that line.

## Algorithm Explanation

### Global Strategy

The implementation is split into three main stages:

1. Parse the map into an object-oriented graph representation.
2. Compute a set of candidate paths from start to end.
3. Assign drones to paths, then simulate all turns while enforcing every constraint.

More explicitly, the routing layer combines:

- a Dijkstra-like weighted shortest-path search,
- an alternative path generation heuristic based on successive node exclusions,
- a greedy load-aware path assignment strategy.

### Parsing Strategy

`MapParser` reads the file line by line, ignores valid comments, and validates every
declaration before building the final `MapData` object.

The parser is intentionally split into small focused modules:

- `src/parser/common.py` handles source lines, line classification, positive integer
  parsing, and metadata splitting.
- `src/parser/zones.py` handles zone declarations, zone metadata, and duplicate zone
  registration.
- `src/parser/connections.py` handles connection declarations, connection metadata, and
  canonical connection keys.
- `src/parser/map.py` keeps the high-level orchestration and assembles the final
  `MapData` object.

The parser checks:

- the `nb_drones` declaration,
- unique `start_hub` and `end_hub`,
- unique zone names,
- valid coordinates,
- duplicate zone coordinates,
- valid zone types,
- valid metadata blocks,
- positive capacities,
- duplicate connections,
- connections that reference only previously declared zones.

Any parsing error stops execution and returns a clear error message with the line number.

### Pathfinding Strategy

`PathFinder` computes weighted shortest paths with a Dijkstra-like exploration strategy.
The destination zone determines the movement cost:

- `normal`: 1 turn
- `priority`: 1 turn
- `restricted`: 2 turns
- `blocked`: forbidden

Priority zones are favored through a secondary score, so two paths with the same total
cost do not behave identically if one path contains more priority zones.

The pathfinder does not stop at a single path. It also generates a ranked set of
candidate paths by re-running the search with exclusions on intermediate nodes. This
gives the assignment phase several useful alternatives on maps with bottlenecks or
parallel routes.

In other words, the pathfinding step is not a single shortest-path query only: it is a
Dijkstra-like shortest-path search followed by a successive-exclusion heuristic to
discover several useful alternatives.

### Path Assignment Strategy

`PathAssigner` distributes drones over the candidate paths instead of pushing every
drone through the exact same route.

For each candidate path, the assigner estimates a pressure score based on:

- the path weighted cost,
- the current load on every traversed connection,
- the current load on every traversed zone,
- the capacity of those resources.

The best-scored path is assigned to the current drone, then the resource loads are
updated before assigning the next one. This greedy strategy is simple, deterministic,
and performs well on the provided maps.

This makes the assignment step a greedy load-aware path distribution algorithm rather
than a globally optimal solver.

### Simulation Strategy

`SimulationEngine` executes the simulation turn by turn using `SimulationState`.
Assigned drone routes are validated and tracked separately through `AssignedPaths`,
which keeps path validation and path progress out of the engine itself.

`SimulationState` is rebuilt at the start of each turn from the current drone states.
It computes zone occupancy, ongoing restricted moves, and connection usage in a single
pass, then applies accepted moves while enforcing all capacity rules.

The engine also refreshes a `MapLoad` snapshot that stores the current zone occupancy
and connection usage for the simulated map.

The simulation enforces:

- simultaneous moves,
- start and end zone special capacity rules,
- `max_drones` on regular zones,
- `max_link_capacity` on connections,
- two-turn restricted movement,
- no waiting on a restricted connection,
- turn-by-turn resolution of arrivals and departures.

If no drone can move and the simulation is not finished, the engine raises a simulation
error instead of looping forever.

### Complexity and Trade-offs

The project favors clarity and determinism over aggressive micro-optimization.

- The shortest-path search uses a simple frontier list instead of a heap, so the search
  is closer to a straightforward Dijkstra implementation than to a highly optimized one.
- Candidate path generation increases work compared to single-path routing, but it
  improves throughput for multi-drone maps.
- Path assignment is greedy, not globally optimal, but it is easier to explain, easy to
  test, and good enough to beat the reference targets on the provided maps.

## Visual Representation

The visual representation is terminal-based.

When the output stream is a TTY, the program colors each movement token according to the
destination zone metadata. Color names are resolved through `colorbrew`, then converted
to ANSI 256-color escape codes. If a color name is unknown, the program falls back to
white. If the output is redirected to a file or a non-interactive stream, the output
stays plain and keeps the exact required format.

An optional `--show-zone` flag adds a compact `Zone states: ...` line after each turn.
This line is built from the `MapLoad` snapshot maintained by the simulation engine and
shows the current occupancy of every tracked zone as `name=current/max`. When the
output stream is a TTY, each zone fragment reuses the same color metadata as the move
tokens.

This improves the user experience because it makes route reading faster during manual
tests:

- repeated routes are easier to distinguish,
- transitions toward the goal are easier to spot,
- restricted, priority, and visually important zones are easier to follow in live runs,
- optional zone-state summaries make capacity checks easier during manual reviews,
- the required subject output format is preserved.

## Project Structure

- `src/parser/common.py`: shared parsing helpers
- `src/parser/zones.py`: zone parsing and validation
- `src/parser/connections.py`: connection parsing and validation
- `src/parser/map.py`: parser orchestration and `MapData` assembly
- `src/models`: object-oriented data model
- `src/models/map_load.py`: current zone occupancy and connection usage snapshot
- `src/routing`: path search and path assignment
- `src/simulation`: turn-by-turn simulation and rule enforcement
- `src/simulation/routes.py`: assigned path validation and per-drone path progress
- `src/display`: terminal rendering
- `maps/`: provided evaluation maps

## Performance Notes

On the provided maps, the current implementation produces the following turn counts:

- Easy 01: 4 turns
- Easy 02: 5 turns
- Easy 03: 6 turns
- Medium 01: 8 turns
- Medium 02: 16 turns
- Medium 03: 7 turns
- Hard 01: 14 turns
- Hard 02: 18 turns
- Hard 03: 26 turns
- Challenger 01: 43 turns

This means the implementation stays below the reference targets on all provided easy,
medium, and hard maps, and also solves the challenger map under the subject PDF target
of 45 turns.

## Resources

Classic references used to design and implement the project:

- Python documentation: object model, exceptions, type hints, file handling
- Dijkstra shortest path algorithm references and graph traversal tutorials
- ANSI terminal color references
- `colorbrew` documentation for color name resolution
- 42 Fly-in subject and provided maps

Useful starting points:

- https://docs.python.org/3/
- https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- https://pypi.org/project/colorbrew/

### AI Usage

AI was used as a support tool, not as a replacement for implementation or validation.
It was used for:

- drafting and normalizing docstrings,
- drafting this README.
