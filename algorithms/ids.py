"""
Iterative Deepening Search (IDS) for the 8-puzzle.  (Student 2)

IDS runs Depth-Limited Search with limits 0, 1, 2, ... until a goal appears.
It combines DFS's small memory (O(depth)) with BFS's optimality: with unit
move costs the first limit that succeeds equals the shortest solution length.

IDS does NOT re-implement the search: every iteration calls dls() from
algorithms/dls.py.  Each call builds its own path set, so path-based
"visited" information is reset at every iteration automatically.

Definitions (same as dls.py)
----------------------------
* nodes_expanded : SUM over all iterations (re-expansion of shallow nodes in
                   later iterations is counted -- that is the real cost).
* running_time   : SUM of the running times of all dls() calls.
* search_depth   : depth of the goal found == path_cost == the winning limit.

Status handling
---------------
* "success" : solution found (optimal number of moves).
* "failure" : proven unsolvable (or a DLS iteration was exhausted without
              hitting its limit).  Never produced just because a limit ended.
* "cutoff"  : max_depth (or max_expansions) was reached first.  The puzzle
              may still be solvable -- the caller must NOT treat this as
              "unsolvable".
"""

from dataclasses import dataclass
from time import perf_counter

from core.puzzle import validate_state, is_solvable
from core.metrics import SearchResult
from algorithms.dls import dls, _validate_limit, _validate_budget

# The hardest 8-puzzle positions need exactly 31 moves, so every solvable
# board is solved by depth 31.  Using it as the default max_depth means a
# "cutoff" can only appear if the caller deliberately chose a smaller value.
DEFAULT_MAX_DEPTH = 31


@dataclass
class IterationRecord:
    """Statistics of one DLS iteration inside IDS (used for reports/UI)."""
    depth_limit: int
    status: str
    nodes_expanded: int
    running_time: float


def ids_with_iterations(initial_state, max_depth=DEFAULT_MAX_DEPTH,
                        max_expansions=None):
    """
    Run IDS and also return the per-iteration statistics.

    Args:
        initial_state:  9 tiles (tuple or list), 0 = blank.
        max_depth:      last depth limit to try (inclusive).
        max_expansions: optional budget for the TOTAL expansions of all
                        iterations; exceeding it gives "cutoff".

    Returns:
        (SearchResult with algorithm "IDS", list[IterationRecord])
    """
    start_time = perf_counter()
    initial_state = validate_state(initial_state)
    _validate_limit(max_depth)
    _validate_budget(max_expansions)

    iterations = []

    # Unsolvable boards: report failure immediately (no iterations).
    if not is_solvable(initial_state):
        result = SearchResult(
            algorithm="IDS",
            status="failure",
            running_time=perf_counter() - start_time,
        )
        return result, iterations

    total_nodes = 0
    total_time = 0.0

    for limit in range(max_depth + 1):
        # Give this iteration only what is left of the shared budget.
        remaining = None
        if max_expansions is not None:
            remaining = max_expansions - total_nodes

        run = dls(initial_state, limit, max_expansions=remaining)

        total_nodes += run.nodes_expanded
        total_time += run.running_time
        iterations.append(
            IterationRecord(limit, run.status, run.nodes_expanded,
                            run.running_time)
        )

        if run.status == "success":
            result = SearchResult(
                algorithm="IDS",
                status="success",
                path=run.path,
                moves=run.moves,
                path_cost=run.path_cost,
                nodes_expanded=total_nodes,
                search_depth=run.search_depth,
                running_time=total_time,
            )
            return result, iterations

        if run.status == "failure":
            # This DLS was never cut off, so deeper limits cannot help.
            break

        # Budget used up: stop and report it honestly as a cutoff.
        if max_expansions is not None and total_nodes >= max_expansions:
            break

    # Not solved.  "failure" only if a DLS iteration proved it; otherwise we
    # simply ran out of depth/budget, which is a cutoff.
    status = "failure" if iterations and iterations[-1].status == "failure" \
        else "cutoff"
    result = SearchResult(
        algorithm="IDS",
        status=status,
        nodes_expanded=total_nodes,
        running_time=total_time,
    )
    return result, iterations


def ids(initial_state, max_depth=DEFAULT_MAX_DEPTH, max_expansions=None):
    """Solve the 8-puzzle with Iterative Deepening Search (SearchResult)."""
    result, _ = ids_with_iterations(initial_state, max_depth, max_expansions)
    return result