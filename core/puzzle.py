"""
Shared 8-puzzle logic used by all search algorithms.
"""

GOAL_STATE = (0, 1, 2, 3, 4, 5, 6, 7, 8)

MOVE_ORDER = ("Up", "Down", "Left", "Right")


def is_valid_state(state):
    """Return True if the board contains each tile 0-8 once."""
    return (
        isinstance(state, (tuple, list))
        and len(state) == 9
        and all(type(tile) is int for tile in state)
        and set(state) == set(range(9))
    )


def validate_state(state):
    """Validate the state and return its tuple representation."""
    if not is_valid_state(state):
        raise ValueError(
            "Invalid puzzle state: enter each integer 0-8 exactly once."
        )

    return tuple(state)


def is_goal(state):
    """Check whether the puzzle has reached its target state."""
    return tuple(state) == GOAL_STATE


def get_neighbors(state):
    """
    Generate all legal moves from a state.

    Returns:
        List of (move, next_state) tuples.
        Moves describe the direction of the blank tile.
    """
    state = validate_state(state)

    zero_index = state.index(0)     #index of blank tile
    row, col = divmod(zero_index, 3)    #row w col of blank tile

    directions = (
        ("Up", -1, 0),
        ("Down", 1, 0),
        ("Left", 0, -1),
        ("Right", 0, 1),
    )

    neighbors = []

    for move, dr, dc in directions:     # try all moves(up,down, left,right)
        new_row = row + dr
        new_col = col + dc

        # The blank must stay inside the 3x3 grid.
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_index = new_row * 3 + new_col

            new_state = list(state)

            new_state[zero_index], new_state[new_index] = (     #switch blank with element
                new_state[new_index],
                new_state[zero_index],
            )

            neighbors.append((move, tuple(new_state)))

    return neighbors


def is_solvable(state):
    """
    Check whether a 3x3 puzzle can reach the goal.

    For an odd-width board, the number of inversions
    must be even.
    """
    state = validate_state(state)

    tiles = [tile for tile in state if tile != 0]       # ignore 0

    inversions = 0
    # ex: (1,3,2) : (2,3) inversion pair


    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i] > tiles[j]:
                inversions += 1

    return inversions % 2 == 0