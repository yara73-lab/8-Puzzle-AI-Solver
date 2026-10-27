"""
Depth-Limited Search (DLS) for the 8-puzzle.  
It is the building block of IDS
"""

from time import perf_counter

from core.puzzle import (
    validate_state,
    is_goal,
    is_solvable,
    get_neighbors,
)
from core.metrics import SearchResult


def _validate_limit(depth_limit):
    if type(depth_limit) is not int or depth_limit < 0:
        raise ValueError("depth_limit must be a non-negative integer.")


def _validate_budget(max_expansions):
    if max_expansions is not None and (
        type(max_expansions) is not int or max_expansions < 0
    ):
        raise ValueError("max_expansions must be None or a non-negative integer.")


def _dls_core(start, depth_limit, successors=get_neighbors,
              goal_test=is_goal, max_expansions=None):
    """
    Generic depth-limited DFS using an explicit stack 
    Returns:
        (status, path, moves, nodes_expanded)
    """
    # The goal test is applied to a node as soon as it is reached; it is never counted as expanded.
    if goal_test(start):
        return "success", [start], [], 0

    # Depth 0: the root is at the limit, so it may not be expanded.
    if depth_limit == 0:
        return "cutoff", [], [], 0

    # Budget of zero: not even the root may be expanded.
    if max_expansions is not None and max_expansions <= 0:
        return "cutoff", [], [], 0

    nodes_expanded = 1                    # the root is expanded below

    # Current root -> node path.  moves[i] leads from path[i] to path[i+1].
    path = [start]
    moves = []
    on_path = {start}                     # O(1) cycle check

    # One lazy iterator of children per node on the path.  Laziness gives
    # true depth-first order: a child is generated only when needed.
    stack = [iter(successors(start))]

    limit_hit = False                     # did the limit prune anything?

    while stack:
        try:
            move, child = next(stack[-1])
        except StopIteration:
            # All children of the top node are done: backtrack.
            stack.pop()
            on_path.discard(path.pop())
            if moves:                     # the root has no incoming move
                moves.pop()
            continue

        if child in on_path:              # path-based cycle prevention
            continue

        if goal_test(child):
            return "success", path + [child], moves + [move], nodes_expanded

        child_depth = len(path)           # depth of `child`

        if child_depth == depth_limit:
            limit_hit = True              # would need to go deeper
            continue

        # Budget check BEFORE expanding, so the count never exceeds it.
        if max_expansions is not None and nodes_expanded >= max_expansions:
            return "cutoff", [], [], nodes_expanded

        nodes_expanded += 1
        path.append(child)
        moves.append(move)
        on_path.add(child)
        stack.append(iter(successors(child)))

    # Whole tree inside the limit explored.
    status = "cutoff" if limit_hit else "failure"
    return status, [], [], nodes_expanded


def dls(initial_state, depth_limit, max_expansions=None):
    """
    Depth-limited search for the 8-puzzle:
    Returns a SearchResult object with the following fields:
        algorithm, status, path, moves, path_cost, nodes_expanded,
        search_depth, running_time
    """
    start_time = perf_counter()
    initial_state = validate_state(initial_state)
    _validate_limit(depth_limit)
    _validate_budget(max_expansions)

    # Half of all boards can never reach the goal.  Report that as a real
    # failure up front instead of burning time and returning "cutoff".
    if not is_solvable(initial_state):
        return SearchResult(
            algorithm="DLS",
            status="failure",
            running_time=perf_counter() - start_time,
        )

    status, path, moves, nodes_expanded = _dls_core(
        initial_state, depth_limit, max_expansions=max_expansions
    )

    if status == "success":
        return SearchResult(
            algorithm="DLS",
            status="success",
            path=path,
            moves=moves,
            path_cost=len(moves),
            nodes_expanded=nodes_expanded,
            search_depth=len(moves),
            running_time=perf_counter() - start_time,
        )

    return SearchResult(
        algorithm="DLS",
        status=status,
        nodes_expanded=nodes_expanded,
        running_time=perf_counter() - start_time,
    )