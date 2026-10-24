"""
Tests for A_Star and the heuristics.

Run from the project root (the folder that contains core/ and a_star.py):
    python -m unittest test_astar -v
    python test_astar.py            # also prints the Manhattan vs Euclidean table
"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from algorithms.astar import A_Star, print_solution
from core.heuristics import Heuristics, BOARD_SIZE
from core.puzzle import GOAL_STATE, get_neighbors, is_goal

GOAL_POS = {t: divmod(i, BOARD_SIZE) for i, t in enumerate(GOAL_STATE)}

EXAMPLE = (1, 2, 5, 3, 4, 0, 6, 7, 8)       # from the assignment PDF
HARD = (8, 6, 7, 2, 5, 4, 3, 0, 1)          # optimal cost is 27 with this goal
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)    # odd number of inversions


def replay(start, moves):
    """Apply a list of blank moves to start and return the final board."""
    state = tuple(start)
    for move in moves:
        nxt = dict(get_neighbors(state))
        assert move in nxt, f"illegal move {move} from {state}"
        state = nxt[move]
    return state


class TestHeuristics(unittest.TestCase):
    def test_goal_is_zero(self):
        self.assertEqual(Heuristics.manhattan(GOAL_STATE, GOAL_POS), 0)
        self.assertEqual(Heuristics.euclidean(GOAL_STATE, GOAL_POS), 0.0)

    def test_one_move_away(self):
        state = (1, 0, 2, 3, 4, 5, 6, 7, 8)
        self.assertEqual(Heuristics.manhattan(state, GOAL_POS), 1)
        self.assertEqual(Heuristics.euclidean(state, GOAL_POS), 1.0)

    def test_assignment_example(self):
        self.assertEqual(Heuristics.manhattan(EXAMPLE, GOAL_POS), 3)
        self.assertEqual(Heuristics.euclidean(EXAMPLE, GOAL_POS), 3.0)

    def test_blank_is_ignored(self):
        # Only the blank is displaced from a solved-looking board: h must be 0 for tile 0
        # Swap blank with tile 8 -> tile 8 is 1 away, blank adds nothing.
        state = (8, 1, 2, 3, 4, 5, 6, 7, 0)
        self.assertEqual(Heuristics.manhattan(state, GOAL_POS), 4)  # tile 8: 2 rows + 2 cols

    def test_euclidean_never_exceeds_manhattan(self):
        for state in (EXAMPLE, HARD, (3, 1, 2, 0, 4, 5, 6, 7, 8)):
            self.assertLessEqual(
                Heuristics.euclidean(state, GOAL_POS),
                Heuristics.manhattan(state, GOAL_POS),
            )


class TestAStar(unittest.TestCase):
    def test_assignment_example(self):
        for h in ("manhattan", "euclidean"):
            r = A_Star(h).solve(EXAMPLE)
            self.assertTrue(r["solvable"])
            self.assertEqual(r["path"], ["Up", "Left", "Left"])
            self.assertEqual(r["cost"], 3)
            self.assertEqual(r["depth"], 3)
            self.assertEqual(len(r["states"]), 4)
            self.assertEqual(r["states"][0], EXAMPLE)
            self.assertEqual(r["states"][-1], GOAL_STATE)

    def test_start_is_goal(self):
        r = A_Star("manhattan").solve(GOAL_STATE)
        self.assertTrue(r["solvable"])
        self.assertEqual(r["path"], [])
        self.assertEqual(r["cost"], 0)
        self.assertEqual(r["states"], [GOAL_STATE])
        self.assertEqual(r["nodes_expanded"], 0)

    def test_unsolvable(self):
        for h in ("manhattan", "euclidean"):
            self.assertEqual(A_Star(h).solve(UNSOLVABLE), {"solvable": False})

    def test_list_input_is_accepted(self):
        r = A_Star("manhattan").solve(list(EXAMPLE))
        self.assertEqual(r["path"], ["Up", "Left", "Left"])

    def test_invalid_state_raises(self):
        with self.assertRaises(ValueError):
            A_Star("manhattan").solve((1, 1, 2, 3, 4, 5, 6, 7, 8))
        with self.assertRaises(ValueError):
            A_Star("manhattan").solve((1, 2, 3))

    def test_unknown_heuristic_raises(self):
        with self.assertRaises(ValueError):
            A_Star("manhatan")

    def test_heuristic_name_is_case_insensitive(self):
        self.assertEqual(A_Star("MANHATTAN").solve(EXAMPLE)["cost"], 3)

    def test_path_actually_reaches_goal(self):
        for h in ("manhattan", "euclidean"):
            r = A_Star(h).solve(HARD)
            self.assertTrue(is_goal(replay(HARD, r["path"])))
            self.assertEqual(len(r["path"]), r["cost"])
            self.assertEqual(len(r["states"]), r["cost"] + 1)

    def test_states_are_consecutive_legal_boards(self):
        r = A_Star("manhattan").solve(HARD)
        for (a, b, move) in zip(r["states"], r["states"][1:], r["path"]):
            self.assertEqual(dict(get_neighbors(a))[move], b)

    def test_both_heuristics_find_optimal_cost(self):
        m = A_Star("manhattan").solve(HARD)
        e = A_Star("euclidean").solve(HARD)
        self.assertEqual(m["cost"], 27)
        self.assertEqual(e["cost"], 27)

    def test_manhattan_expands_no_more_than_euclidean(self):
        m = A_Star("manhattan").solve(HARD)
        e = A_Star("euclidean").solve(HARD)
        self.assertLessEqual(m["nodes_expanded"], e["nodes_expanded"])

    def test_heuristic_is_admissible_along_solution(self):
        # h(state) must never exceed the true remaining cost on the optimal path.
        r = A_Star("manhattan").solve(HARD)
        total = r["cost"]
        for i, board in enumerate(r["states"]):
            remaining = total - i
            self.assertLessEqual(Heuristics.manhattan(board, GOAL_POS), remaining)
            self.assertLessEqual(Heuristics.euclidean(board, GOAL_POS), remaining)

    def test_result_keys(self):
        r = A_Star("manhattan").solve(EXAMPLE)
        for key in ("solvable", "path", "states", "cost", "depth",
                    "nodes_expanded", "max_frontier", "max_depth", "time"):
            self.assertIn(key, r)


def comparison_table(starts):
    """Print Manhattan vs Euclidean stats for the report."""
    print(f"{'start':<28}{'heuristic':<11}{'cost':>5}{'expanded':>10}"
          f"{'frontier':>10}{'time(s)':>10}")
    for name, state in starts:
        for h in ("manhattan", "euclidean"):
            r = A_Star(h).solve(state)
            if not r["solvable"]:
                print(f"{name:<28}{h:<11}{'unsolvable':>35}")
                continue
            print(f"{name:<28}{h:<11}{r['cost']:>5}{r['nodes_expanded']:>10}"
                  f"{r['max_frontier']:>10}{r['time']:>10.4f}")


if __name__ == "__main__":
    unittest.main(exit=False, verbosity=1)
    print("\nSample run (assignment example):\n")
    print_solution(A_Star("manhattan").solve(EXAMPLE))
    print("\nHeuristic comparison:\n")
    comparison_table([
        ("assignment example", EXAMPLE),
        ("hard (27 moves)", HARD),
        ("unsolvable", UNSOLVABLE),
    ])