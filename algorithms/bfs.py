
"""
Breadth-First Search (BFS) for the 8-puzzle.

BFS uses a FIFO queue and guarantees a shortest path
when all moves have the same cost.
"""

from collections import deque
from time import perf_counter

from core.puzzle import (
    validate_state,
    is_goal,
    is_solvable,
    get_neighbors,
)
from core.metrics import SearchResult


def bfs(initial_state):
    """Solve the 8-puzzle using Breadth-First Search."""

    start_time = perf_counter()
    initial_state = validate_state(initial_state)

    if not is_solvable(initial_state):
        return SearchResult(
            algorithm="BFS",
            status="failure",
            running_time=perf_counter() - start_time,
        )

    # Queue stores states waiting to be explored.
    frontier = deque([initial_state])

    # Mark states visited when they enter the queue.
    visited = {initial_state}

    # Store parent and move information for path reconstruction.
    parent = {initial_state: None}
    move_taken = {}

    nodes_expanded = 0

    while frontier:
        current = frontier.popleft()

        # Test for the goal before expanding successors.
        if is_goal(current):
            path = []
            moves = []

            state = current

            # Trace backward from goal to initial state.
            while state is not None:
                path.append(state)

                if state in move_taken:
                    moves.append(move_taken[state])

                state = parent[state]

            # Reverse to obtain initial -> goal order.
            path.reverse()
            moves.reverse()

            return SearchResult(
                algorithm="BFS",
                status="success",
                path=path,
                moves=moves,
                path_cost=len(moves),
                nodes_expanded=nodes_expanded,
                search_depth=len(moves),
                running_time=perf_counter() - start_time,
            )

        # Expanding means generating the current state's successors.
        nodes_expanded += 1

        for move, neighbor in get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                move_taken[neighbor] = move
                frontier.append(neighbor)

    return SearchResult(
        algorithm="BFS",
        status="failure",
        nodes_expanded=nodes_expanded,
        running_time=perf_counter() - start_time,
    )
