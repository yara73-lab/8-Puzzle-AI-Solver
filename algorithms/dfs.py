
"""
Depth-First Search (DFS) for the 8-puzzle.

Uses an explicit LIFO stack and graph-search visited tracking.
Does not guarantee a shortest solution.
"""

from time import perf_counter

from core.puzzle import (
    validate_state,
    is_goal,
    is_solvable,
    get_neighbors,
)
from core.metrics import SearchResult


def dfs(initial_state, max_expansions=None):
    """
    Solve the 8-puzzle using iterative DFS.

    max_expansions:
        Optional safeguard against expensive searches.
        None means no expansion limit.
    """

    start_time = perf_counter()
    initial_state = validate_state(initial_state)

    if max_expansions is not None:
     if type(max_expansions) is not int or max_expansions < 0:
        raise ValueError(
            "max_expansions must be a non-negative integer or None."
        )

    if not is_solvable(initial_state):
        return SearchResult(
            algorithm="DFS",
            status="failure",
            running_time=perf_counter() - start_time,
        )

    # LIFO stack: last state added is explored first
    frontier = [initial_state]

    visited = {initial_state}
    parent = {initial_state: None}
    move_taken = {}

    nodes_expanded = 0

    while frontier:
        current = frontier.pop()

        if is_goal(current):    # Reconstruct path and return success
            path = []
            moves = []
            state = current

            while state is not None:
                path.append(state)

                if state in move_taken:
                    moves.append(move_taken[state])

                state = parent[state]

            path.reverse()
            moves.reverse()

            return SearchResult(
                algorithm="DFS",
                status="success",
                path=path,
                moves=moves,
                path_cost=len(moves),
                nodes_expanded=nodes_expanded,
                search_depth=len(moves),
                running_time=perf_counter() - start_time,
            )

        if (
            max_expansions is not None
            and nodes_expanded >= max_expansions
        ):
            return SearchResult(
                algorithm="DFS",
                status="cutoff",
                nodes_expanded=nodes_expanded,
                running_time=perf_counter() - start_time,
            )

        nodes_expanded += 1

        # Reverse insertion because a stack is LIFO.
        neighbors = get_neighbors(current)

        for move, neighbor in reversed(neighbors):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                move_taken[neighbor] = move
                frontier.append(neighbor)

    return SearchResult(
        algorithm="DFS",
        status="failure",
        nodes_expanded=nodes_expanded,
        running_time=perf_counter() - start_time,
    )
