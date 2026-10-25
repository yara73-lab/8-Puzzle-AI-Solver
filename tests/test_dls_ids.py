"""
Tests for Depth-Limited Search (DLS) and Iterative Deepening Search (IDS).
(Student 2)

Run from the project root:
    python -m pytest tests/test_dls_ids.py -v
"""

import math

import pytest

from algorithms.bfs import bfs                      # used only as an oracle
from algorithms.dls import dls, _dls_core
from algorithms.ids import ids, ids_with_iterations
from core.puzzle import GOAL_STATE, get_neighbors

# Assignment example: solved by Up, Left, Left (optimal depth 3).
EXAMPLE = (1, 2, 5, 3, 4, 0, 6, 7, 8)
ONE_MOVE = (1, 0, 2, 3, 4, 5, 6, 7, 8)              # solved by "Left"
TWO_MOVES = (1, 4, 2, 3, 0, 5, 6, 7, 8)
UNSOLVABLE = (0, 2, 1, 3, 4, 5, 6, 7, 8)
# Optimal depth 2, but a deep DFS wanders and returns a longer path.
DFS_TRAP = (1, 2, 0, 3, 4, 5, 6, 7, 8)


def assert_valid_solution(initial_state, result):
    """A returned solution must be a legal path from start to goal."""
    assert result.solved
    assert result.path[0] == initial_state
    assert result.path[-1] == GOAL_STATE

    assert result.path_cost == len(result.moves)
    assert result.search_depth == len(result.moves)
    assert len(result.path) == len(result.moves) + 1

    # No state repeats on the path (path-based cycle prevention).
    assert len(set(result.path)) == len(result.path)

    # Every step must be a legal transition with the reported move name.
    for i, move in enumerate(result.moves):
        assert (move, result.path[i + 1]) in get_neighbors(result.path[i])


def assert_no_solution_returned(result):
    """Cutoff/failure results carry no path information."""
    assert not result.solved
    assert result.path == []
    assert result.moves == []
    assert result.path_cost is None
    assert result.search_depth is None


# --------------------------------------------------------------------------
# DLS
# --------------------------------------------------------------------------

def test_dls_limit_zero_on_non_goal_is_cutoff():
    result = dls(EXAMPLE, 0)

    assert result.algorithm == "DLS"
    assert result.status == "cutoff"
    assert_no_solution_returned(result)
    assert result.nodes_expanded == 0          # root may not be expanded


def test_dls_limit_zero_on_goal_succeeds():
    result = dls(GOAL_STATE, 0)

    assert_valid_solution(GOAL_STATE, result)
    assert result.path == [GOAL_STATE]
    assert result.path_cost == 0
    assert result.nodes_expanded == 0


@pytest.mark.parametrize("limit", [0, 1, 2])
def test_dls_limit_smaller_than_solution_depth_is_cutoff(limit):
    result = dls(EXAMPLE, limit)           # needs depth 3

    assert result.status == "cutoff"
    assert_no_solution_returned(result)


def test_dls_exact_solution_depth():
    result = dls(EXAMPLE, 3)

    assert_valid_solution(EXAMPLE, result)
    assert result.moves == ["Up", "Left", "Left"]
    assert result.search_depth == 3
    assert result.nodes_expanded == 3


@pytest.mark.parametrize("limit", [4, 5, 10])
def test_dls_limit_greater_than_solution_depth(limit):
    result = dls(EXAMPLE, limit)

    assert_valid_solution(EXAMPLE, result)
    assert result.search_depth <= limit        # depth limit is respected
    assert result.search_depth >= 3            # nothing shorter exists


def test_dls_is_not_guaranteed_optimal():
    """DLS with a generous limit may return a longer path (that is why IDS exists)."""
    result = dls(DFS_TRAP, 12)

    assert_valid_solution(DFS_TRAP, result)
    assert result.path_cost > bfs(DFS_TRAP).path_cost


def test_dls_never_exceeds_limit():
    for limit in range(1, 8):
        result = dls(TWO_MOVES, limit)
        if result.solved:
            assert result.path_cost <= limit


def test_dls_accepts_list_input():
    result = dls(list(EXAMPLE), 3)

    assert_valid_solution(EXAMPLE, result)


def test_dls_unsolvable_is_failure_not_cutoff():
    result = dls(UNSOLVABLE, 10)

    assert result.status == "failure"
    assert_no_solution_returned(result)
    assert result.nodes_expanded == 0


def test_dls_expansion_budget_gives_cutoff():
    result = dls(EXAMPLE, 3, max_expansions=0)
    assert result.status == "cutoff"
    assert result.nodes_expanded == 0

    result = dls((8, 6, 7, 2, 5, 4, 3, 0, 1), 31, max_expansions=50)
    assert result.status == "cutoff"
    assert result.nodes_expanded <= 50


@pytest.mark.parametrize("bad_limit", [-1, 1.5, "3", None, True])
def test_dls_rejects_invalid_depth_limit(bad_limit):
    with pytest.raises(ValueError):
        dls(EXAMPLE, bad_limit)


def test_dls_rejects_invalid_state():
    with pytest.raises(ValueError):
        dls((1, 1, 2, 3, 4, 5, 6, 7, 8), 3)


# --------------------------------------------------------------------------
# Cutoff versus failure, on tiny hand-made graphs (_dls_core is generic)
# --------------------------------------------------------------------------

def graph(edges, goal):
    """Build (successors, goal_test) for a small directed graph."""
    def successors(node):
        return [(f"{node}>{child}", child) for child in edges.get(node, [])]

    return successors, (lambda node: node == goal)


def test_core_failure_when_space_exhausted_inside_limit():
    # A -> B, A -> C, no goal anywhere, nothing deeper than depth 1.
    succ, goal = graph({"A": ["B", "C"]}, goal="Z")

    status, path, moves, _ = _dls_core("A", 5, succ, goal)

    assert status == "failure"
    assert path == [] and moves == []


def test_core_cutoff_when_limit_hides_part_of_the_space():
    # Chain A -> B -> C -> D, goal never present.
    succ, goal = graph({"A": ["B"], "B": ["C"], "C": ["D"]}, goal="Z")

    assert _dls_core("A", 1, succ, goal)[0] == "cutoff"
    assert _dls_core("A", 2, succ, goal)[0] == "cutoff"
    # D sits exactly at limit 3: it is a non-goal at the limit, so we cannot
    # tell whether it has children -> still a cutoff.
    assert _dls_core("A", 3, succ, goal)[0] == "cutoff"
    # Limit 4 lets D be expanded; it is a dead end -> nothing was hidden.
    assert _dls_core("A", 4, succ, goal)[0] == "failure"


def test_core_success_on_exact_depth_and_cutoff_just_below():
    succ, goal = graph({"A": ["B"], "B": ["C"], "C": ["D"]}, goal="D")

    assert _dls_core("A", 2, succ, goal)[0] == "cutoff"
    status, path, moves, _ = _dls_core("A", 3, succ, goal)
    assert status == "success"
    assert path == ["A", "B", "C", "D"]
    assert moves == ["A>B", "B>C", "C>D"]


def test_core_cycles_do_not_loop_forever():
    # A <-> B form a cycle; without cycle checking this would never end.
    succ, goal = graph({"A": ["B"], "B": ["A"]}, goal="Z")

    status, _, _, expanded = _dls_core("A", 100, succ, goal)

    assert status == "failure"
    assert expanded == 2


def test_core_path_based_check_allows_state_reached_by_another_branch():
    # D is reachable from A directly (depth 1) and via B (depth 2).
    # A global visited set could hide one of them; path-based must not.
    succ, goal = graph({"A": ["B", "D"], "B": ["D"]}, goal="Z")

    status, _, _, expanded = _dls_core("A", 5, succ, goal)

    assert status == "failure"
    # Expanded: A, B, D (reached through B) and D again (reached from A).
    # D is expanded once per route because only the current path is checked.
    assert expanded == 4


# --------------------------------------------------------------------------
# IDS
# --------------------------------------------------------------------------

def test_ids_already_solved():
    result = ids(GOAL_STATE)

    assert result.algorithm == "IDS"
    assert_valid_solution(GOAL_STATE, result)
    assert result.path_cost == 0
    assert result.nodes_expanded == 0


def test_ids_one_move():
    result = ids(ONE_MOVE)

    assert_valid_solution(ONE_MOVE, result)
    assert result.moves == ["Left"]
    assert result.path_cost == 1


def test_ids_multi_move_assignment_example():
    result = ids(EXAMPLE)

    assert_valid_solution(EXAMPLE, result)
    assert result.moves == ["Up", "Left", "Left"]
    assert result.search_depth == 3


def test_ids_returns_shortest_depth_where_dls_does_not():
    result = ids(DFS_TRAP)

    assert_valid_solution(DFS_TRAP, result)
    assert result.path_cost == 2
    assert result.path_cost < dls(DFS_TRAP, 12).path_cost


@pytest.mark.parametrize("state", [
    EXAMPLE,
    ONE_MOVE,
    TWO_MOVES,
    DFS_TRAP,
    (3, 1, 2, 7, 6, 5, 4, 8, 0),                 # depth 8
    (0, 3, 1, 7, 6, 2, 4, 8, 5),                 # depth 12
])
def test_ids_matches_bfs_optimal_depth(state):
    result = ids(state)

    assert_valid_solution(state, result)
    assert result.path_cost == bfs(state).path_cost


def test_ids_cumulative_expanded_nodes_and_iterations():
    result, iterations = ids_with_iterations(EXAMPLE)

    # One iteration per limit 0..solution depth, in order.
    assert [it.depth_limit for it in iterations] == [0, 1, 2, 3]
    assert [it.status for it in iterations] == [
        "cutoff", "cutoff", "cutoff", "success"]

    # Totals are the sum over all iterations ...
    assert result.nodes_expanded == sum(it.nodes_expanded for it in iterations)
    assert result.nodes_expanded == 0 + 1 + 4 + 3          # known real values
    assert math.isclose(
        result.running_time, sum(it.running_time for it in iterations))

    # ... and each iteration equals a standalone, fresh DLS run
    # (proves nothing is carried over between iterations).
    for it in iterations:
        standalone = dls(EXAMPLE, it.depth_limit)
        assert it.nodes_expanded == standalone.nodes_expanded
        assert it.status == standalone.status


def test_ids_cumulative_count_on_deeper_puzzle():
    state = (0, 3, 1, 7, 6, 2, 4, 8, 5)              # optimal depth 12
    result = ids(state)

    expected = sum(
        dls(state, limit).nodes_expanded for limit in range(result.path_cost + 1)
    )
    assert result.nodes_expanded == expected
    # Re-expansion makes IDS cost more than its final iteration alone.
    assert result.nodes_expanded > dls(state, result.path_cost).nodes_expanded


def test_ids_max_depth_too_small_is_cutoff_not_failure():
    result, iterations = ids_with_iterations(EXAMPLE, max_depth=2)

    assert result.status == "cutoff"        # NOT "failure"
    assert_no_solution_returned(result)
    assert [it.depth_limit for it in iterations] == [0, 1, 2]
    assert result.nodes_expanded == 0 + 1 + 4


def test_ids_max_depth_zero():
    assert ids(EXAMPLE, max_depth=0).status == "cutoff"
    assert ids(GOAL_STATE, max_depth=0).status == "success"


def test_ids_unsolvable_is_failure_without_iterations():
    result, iterations = ids_with_iterations(UNSOLVABLE)

    assert result.algorithm == "IDS"
    assert result.status == "failure"
    assert_no_solution_returned(result)
    assert iterations == []
    assert result.nodes_expanded == 0


def test_ids_total_expansion_budget_gives_cutoff():
    state = (0, 3, 1, 7, 6, 2, 4, 8, 5)
    result = ids(state, max_expansions=100)

    assert result.status == "cutoff"
    assert result.nodes_expanded <= 100
    assert_no_solution_returned(result)


def test_ids_default_max_depth_solves_every_tested_board():
    # 31 is the maximum optimal depth of any 8-puzzle, so the default can
    # only end in "success" or "failure" (unsolvable), never a silent cutoff.
    for state in (EXAMPLE, ONE_MOVE, GOAL_STATE, UNSOLVABLE):
        assert ids(state).status in ("success", "failure")


@pytest.mark.parametrize("bad_depth", [-1, 2.5, "5", None, True])
def test_ids_rejects_invalid_max_depth(bad_depth):
    with pytest.raises(ValueError):
        ids(EXAMPLE, max_depth=bad_depth)


def test_ids_rejects_invalid_state():
    with pytest.raises(ValueError):
        ids((1, 2, 3))