import pytest

from core.puzzle import (
    GOAL_STATE,
    get_neighbors,
    is_goal,
    is_solvable,
    is_valid_state,
    validate_state,
)


def test_valid_state():
    assert is_valid_state(GOAL_STATE)
    assert not is_valid_state((0, 1, 2))


def test_duplicate_tiles():
    invalid = (0, 1, 1, 3, 4, 5, 6, 7, 8)

    with pytest.raises(ValueError):
        validate_state(invalid)


def test_goal():
    assert is_goal(GOAL_STATE)
    assert not is_goal((1, 0, 2, 3, 4, 5, 6, 7, 8))


def test_neighbors():
    neighbors = get_neighbors(GOAL_STATE)

    assert len(neighbors) == 2

    assert neighbors == [
        ("Down", (3, 1, 2, 0, 4, 5, 6, 7, 8)),
        ("Right", (1, 0, 2, 3, 4, 5, 6, 7, 8)),
    ]


def test_solvable():
    assert is_solvable(GOAL_STATE)
    assert is_solvable((1, 0, 2, 3, 4, 5, 6, 7, 8))


def test_unsolvable():
    assert not is_solvable((0, 2, 1, 3, 4, 5, 6, 7, 8))