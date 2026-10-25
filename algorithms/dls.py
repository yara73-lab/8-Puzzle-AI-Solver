"""
Depth-Limited Search (DLS) for the 8-puzzle.  (Student 2)

DLS is depth-first search that refuses to go deeper than ``depth_limit``.
It is the building block of Iterative Deepening Search (see ids.py).

Definitions used throughout this project
----------------------------------------
* depth of a node      : number of moves from the initial state. Root = 0.
* nodes_expanded       : number of NON-GOAL nodes whose successors were
                         generated.  A node sitting exactly at the depth
                         limit is NOT expanded, and the goal is never counted
                         (same convention as the BFS/DFS in this repo, so the
                         numbers are comparable).
* search_depth         : depth of the goal that was found (== path_cost).
                         It is None when no solution is returned.

Three possible outcomes (``SearchResult.status``)
-------------------------------------------------
* "success" : a goal was found within the limit.
* "cutoff"  : the limit (or the optional expansion budget) stopped the search
              while some branches were still unexplored.  A solution MAY exist
              deeper.  This is NOT a proof of unsolvability.
* "failure" : the search space inside the limit was exhausted WITHOUT being
              cut by the limit, or the puzzle is unsolvable.  No solution
              exists at any depth.

Cycle prevention
----------------
Only states on the CURRENT path (root -> current node) are forbidden, not
every state ever seen.  This keeps memory at O(depth) and, unlike a global
visited set, it never hides a shorter route to a state that was first reached
by a long route -- which is what makes IDS return an optimal-depth answer.
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
    """Depth limits must be non-negative integers (bool is rejected)."""
    if type(depth_limit) is not int or depth_limit < 0:
        raise ValueError("depth_limit must be a non-negative integer.")


def _validate_budget(max_expansions):
    """The optional expansion budget must be None or a non-negative int."""
    if max_expansions is not None and (
        type(max_expansions) is not int or max_expansions < 0
    ):
        raise ValueError("max_expansions must be None or a non-negative integer.")


def _dls_core(start, depth_limit, successors=get_neighbors,
              goal_test=is_goal, max_expansions=None):
    """
    Generic depth-limited DFS using an explicit stack (no recursion, so a
    large depth_limit can never hit Python's recursion limit).

    ``successors`` and ``goal_test`` are parameters only so the three-way
    success / cutoff / failure logic can be unit-tested on tiny hand-made
    graphs.  dls() always uses the real puzzle functions.

    Returns:
        (status, path, moves, nodes_expanded)
    """
    # The goal test is applied to a node as soon as it is reached; it is
    # never counted as expanded.
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
    Solve the 8-puzzle with Depth-Limited Search.

    Args:
        initial_state:  9 tiles (tuple or list), 0 = blank.
        depth_limit:    maximum depth (number of moves) that may be reached.
        max_expansions: optional safety budget; exceeding it gives "cutoff".

    Returns:
        SearchResult with algorithm "DLS".
        On success: path, moves, path_cost, search_depth are filled in.
        On cutoff / failure: path and moves are empty and path_cost and
        search_depth are None.
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