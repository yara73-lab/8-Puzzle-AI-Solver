from heapq import heappush,heappop
from core.heuristics import Heuristics,BOARD_SIZE
from core.puzzle import GOAL_STATE, get_neighbors,is_goal,is_solvable,validate_state
from itertools import count
import time 

HEURISTICS = {
    "manhattan": Heuristics.manhattan,
    "euclidean": Heuristics.euclidean,
}

class A_Star:
    """A* search using f(n) = g(n) + h(n) with a selectable heuristic."""
    
    def __init__(self, heuristic: str):
        key = heuristic.lower()
        if key not in HEURISTICS:
            raise ValueError(
                f"Unknown heuristic: {heuristic!r} (choose from {list(HEURISTICS)})"
            )
        self.heuristic = HEURISTICS[key]
        # tile -> (row, col) in the goal, computed once and reused for every h call
        self.goal_pos = {
            tile: divmod(idx, BOARD_SIZE) for idx, tile in enumerate(GOAL_STATE)
        }

    def solve(self, initial_state):
        initial_state = validate_state(initial_state)  # also makes it a hashable tuple
        start_time = time.perf_counter()

        # Half of all boards can never reach the goal; detect that up front
        # instead of exhausting the whole reachable space.
        if not is_solvable(initial_state):
            return {"solvable": False}

        tie_break = count()          # unique, ever-increasing id for each heap entry
        heap = []                    
        best_g = {initial_state: 0}  # cheapest g found so far for each state
        parent = {initial_state: None}  # state -> (previous_state, move)
        expanded = set()
        max_frontier = 1

        h0 = self.heuristic(initial_state, self.goal_pos)
        heappush(heap, (h0, next(tie_break), initial_state, 0))

        while heap:
            _, _, current, g = heappop(heap)

            if is_goal(current):
                path, states = self.trace_path(parent)
                return {
                    "solvable": True,
                    "path": path,
                    "states": states,
                    "cost": g,
                    "depth": g,
                    "nodes_expanded": len(expanded),
                    "max_frontier": max_frontier,
                    "max_depth": max(best_g.values()),
                    "time": time.perf_counter() - start_time,
                }

            # A state can sit in the heap several times; only expand it once.
            if current in expanded:
                continue
            expanded.add(current)

            for move, child in get_neighbors(current):
                new_g = g + 1
                # Push only if this is a new board or a cheaper route to a known one.
                if child not in best_g or new_g < best_g[child]:
                    best_g[child] = new_g
                    parent[child] = (current, move) # type: ignore
                    h = self.heuristic(child, self.goal_pos)
                    heappush(heap, (new_g + h, next(tie_break), child, new_g))

            max_frontier = max(max_frontier, len(heap))

        raise RuntimeError("Search ended without reaching the goal on a solvable board.")

    def trace_path(self, parent: dict):
        state = GOAL_STATE
        moves = []
        boards = [GOAL_STATE]
        while parent[state] is not None:
            state, move = parent[state]
            moves.append(move)
            boards.append(state)
        return moves[::-1], boards[::-1]

def print_solution(result):
    """Print every step of a solved result as a small 3x3 grid."""
    if not result["solvable"]:
        print("Puzzle is unsolvable.")
        return
    states, moves = result["states"], result["path"]
    for step, board in enumerate(states):
        label = "Start" if step == 0 else f"Step {step}: blank moves {moves[step - 1]}"
        print(label)
        for r in range(0, 9, 3):
            print(" ".join("_" if t == 0 else str(t) for t in board[r:r + 3]))
        print()
    print(f"Cost: {result['cost']}  Depth: {result['depth']}  "
          f"Expanded: {result['nodes_expanded']}  Time: {result['time']:.4f}s")