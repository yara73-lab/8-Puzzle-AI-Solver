# 8-Puzzle AI Solver

An interactive 8-puzzle solver that compares uninformed and informed search
algorithms. Enter or randomize a board, pick an algorithm, and watch the
solution step by step, or run every algorithm on the same board and compare them.

## Algorithms

| Algorithm | Type | Optimal path? | Notes |
|---|---|---|---|
| BFS | uninformed | yes | FIFO queue, visited set |
| DFS | uninformed | **no** | LIFO stack, visited set; paths can be tens of thousands of moves long |
| IDS (Iterative DFS) | uninformed | yes | Depth-limited DFS with limits 0, 1, 2, ...; low memory, many re-expansions |
| DLS | uninformed | no | Depth-limited search with a fixed limit; building block of IDS |
| A* (Manhattan) | informed | yes | Priority queue ordered by f = g + h |
| A* (Euclidean) | informed | yes | Same A*, straight-line heuristic (weaker than Manhattan) |

## Setup and run

Python 3.10+ is recommended. Run everything from the project root.

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

Using the app:

1. Enter the nine tiles (`0` is the blank, e.g. `1,2,5,3,4,0,6,7,8`) or randomize. Unsolvable boards are rejected.
2. Choose an algorithm and press **Solve**. The page shows the path, cost, nodes expanded, search depth and running time, then a step-by-step viewer (Previous / Next / Play).
3. Press **Solve with all** to run BFS, DFS, IDS and both A* variants on the same board. The dashboard shows a comparison table, charts and a CSV download.

DFS, IDS and DLS have a *max node expansions* safety limit (default 2,000,000). Reaching it returns status `cutoff`, which means "stopped early", not "unsolvable".

## Tests

```bash
python -m pytest
```

Use `python -m pytest` (not plain `pytest`) so the project root is on the import path.

## Conventions

- A state is a tuple of nine ints in row-major order; `0` is the blank. Goal: `(0, 1, 2, 3, 4, 5, 6, 7, 8)`.
- Move names (`Up`, `Down`, `Left`, `Right`) are the direction the **blank** moves. Every move costs 1, so path cost = number of moves.
- Every solver returns a `core.metrics.SearchResult` with `status` = `success`, `failure` (no solution exists) or `cutoff` (stopped by a limit).
- **Nodes expanded** counts non-goal nodes whose successors were generated. For IDS it is the total over all iterations. **Search depth** is the depth of the goal found, which equals the path cost.
- Unsolvable boards (odd number of inversions) are detected up front by every algorithm and reported as `failure`.

## Project structure

```
core/         puzzle rules (puzzle.py), SearchResult (metrics.py), heuristics
algorithms/   bfs.py  dfs.py  dls.py  ids.py  astar.py
frontend/     app.py (page), board.py (input + board), visualization.py (step viewer), dashboard.py (comparison)
tests/        unit tests for the core and every algorithm
scripts/      collect_report_data.py (statistics used in the report)
```

## Reproducing the report statistics

```bash
python scripts/collect_report_data.py --json report_data.json
```

Node counts are deterministic; running times depend on your machine. A full run takes a few minutes because it includes IDS on a 27-move board.