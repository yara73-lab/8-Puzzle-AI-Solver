
"""
Tests for BFS and DFS search algorithms.
"""

from algorithms.bfs import bfs
from algorithms.dfs import dfs
from core.puzzle import GOAL_STATE, get_neighbors
import pytest



def assert_valid_solution(initial_state, result):
    """Verify that a returned solution is a legal puzzle path."""

    assert result.solved
    assert result.path[0] == initial_state
    assert result.path[-1] == GOAL_STATE

    assert result.path_cost == len(result.moves)
    assert result.search_depth == len(result.moves)
    assert len(result.path) == len(result.moves) + 1

    for i, move in enumerate(result.moves):
        legal_transitions = get_neighbors(result.path[i])

        assert (move, result.path[i + 1]) in legal_transitions


def test_bfs_already_solved():
    result = bfs(GOAL_STATE)

    assert_valid_solution(GOAL_STATE, result)
    assert result.path_cost == 0
    assert result.nodes_expanded == 0


def test_dfs_already_solved():
    result = dfs(GOAL_STATE)

    assert_valid_solution(GOAL_STATE, result)
    assert result.path_cost == 0
    assert result.nodes_expanded == 0


def test_bfs_one_move():
    initial = (1, 0, 2, 3, 4, 5, 6, 7, 8)
    result = bfs(initial)

    assert_valid_solution(initial, result)
    assert result.path_cost == 1
    assert result.moves == ["Left"]


def test_bfs_two_moves():
    initial = (1, 4, 2, 3, 0, 5, 6, 7, 8)
    result = bfs(initial)

    assert_valid_solution(initial, result)
    assert result.path_cost == 2


def test_dfs_one_move():
    # The goal is reached through DFS's preferred Up move.
    initial = (3, 1, 2, 0, 4, 5, 6, 7, 8)
    result = dfs(initial, max_expansions=1000)

    assert_valid_solution(initial, result)
    assert result.path_cost == 1


def test_bfs_unsolvable():
    initial = (0, 2, 1, 3, 4, 5, 6, 7, 8)
    result = bfs(initial)

    assert result.status == "failure"
    assert result.path == []


def test_dfs_unsolvable():
    initial = (0, 2, 1, 3, 4, 5, 6, 7, 8)
    result = dfs(initial)

    assert result.status == "failure"
    assert result.path == []


def test_dfs_cutoff():
    initial = (3, 1, 2, 0, 4, 5, 6, 7, 8)
    result = dfs(initial, max_expansions=0)

    assert result.status == "cutoff"
    assert not result.solved
    assert result.nodes_expanded == 0

@pytest.mark.parametrize("limit", [-1, 1.5, True, "3", float("nan")])
def test_dfs_invalid_expansion_limit(limit):
    with pytest.raises(ValueError):
        dfs(GOAL_STATE, max_expansions=limit)
