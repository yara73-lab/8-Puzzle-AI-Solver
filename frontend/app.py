"""
Draft single-page Streamlit app for the 8-puzzle assignment.  (Student 2)

Run from the PROJECT ROOT:
    streamlit run frontend/app_draft.py

When the team agrees, copy this file over frontend/app.py (this draft never
touches app.py itself).

One page:
  1. choose / randomise a board          (frontend/board.py, Student 1)
  2. choose ONE algorithm and press Solve
  3. report data printed: path to goal, cost, nodes expanded, search depth,
     running time, IDS iterations, every step as text, downloadable trace
  4. step-by-step viewer                 (frontend/visualization.py)
  5. optional "run ALL algorithms" comparison table (CSV download)
"""

import sys
from pathlib import Path

# `streamlit run frontend/...` puts frontend/ on sys.path, not the project
# root, so core/ and algorithms/ would not be importable without this.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from algorithms.astar import A_Star
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.dls import dls
from algorithms.ids import ids_with_iterations
from core.metrics import SearchResult
from frontend.board import render_puzzle_input
from frontend.visualization import render_solution_viewer

SOLVERS = [
    "BFS",
    "DFS",
    "IDS (Iterative DFS)",
    "A* - Manhattan",
    "A* - Euclidean",
    "DLS (fixed depth limit)",
]

# Data structure + short explanation of every algorithm (report material).
# Keys equal SearchResult.algorithm.
ALGORITHM_NOTES = {
    "BFS": "Data structures: FIFO queue (collections.deque), visited set, "
           "parent/move dictionaries. Expands the shallowest node first, so "
           "with unit costs the first goal found is a shortest path.",
    "DFS": "Data structures: LIFO stack (list), visited set, parent/move "
           "dictionaries. Always expands the most recently generated node. "
           "Memory-light in theory but NOT optimal: paths can be very long.",
    "IDS": "Data structures: explicit stack of lazy child "
           "iterators, current-path list and a path set (O(depth) memory). "
           "Runs depth-limited DFS with limits 0, 1, 2, ... and sums the "
           "work of all iterations. Complete and optimal for unit costs.",
    "A* - Manhattan": "Data structures: min-heap (heapq) ordered by "
           "f = g + h, best-g dictionary, parent dictionary, expanded set. "
           "h = sum of tile row+column distances to the goal (admissible).",
    "A* - Euclidean": "Same A* as above with h = sum of straight-line tile "
           "distances to the goal. Admissible but never larger than "
           "Manhattan, so it is less informed.",
    "DLS": "Data structures: same as IDS, one iteration. "
           "Returns success, cutoff (limit hid part of the tree) or failure.",
}

TRACE_DISPLAY_STEPS = 200        # steps printed on the page; full trace is downloadable


# ---------------------------------------------------------------------------
# Pure helpers (no Streamlit calls)
# ---------------------------------------------------------------------------

def astar_to_result(raw, label):
    """Convert A_Star.solve()'s dict into the shared SearchResult."""
    if not raw.get("solvable"):
        return SearchResult(algorithm=label, status="failure")
    return SearchResult(
        algorithm=label,
        status="success",
        path=list(raw["states"]),
        moves=list(raw["path"]),
        path_cost=raw["cost"],
        nodes_expanded=raw["nodes_expanded"],
        search_depth=raw["depth"],
        running_time=raw["time"],
    )


def run_solver(name, state, depth_limit=5, budget=0):
    """
    Run one algorithm.

    budget: maximum node expansions, 0 means unlimited.
    Returns (SearchResult, IDS iteration records or None).
    """
    budget = budget or None
    if name == "BFS":
        return bfs(state), None
    if name == "DFS":
        return dfs(state, max_expansions=budget), None
    if name.startswith("IDS"):
        return ids_with_iterations(state, max_expansions=budget)
    if name == "A* - Manhattan":
        return astar_to_result(A_Star("manhattan").solve(state), name), None
    if name == "A* - Euclidean":
        return astar_to_result(A_Star("euclidean").solve(state), name), None
    if name.startswith("DLS"):
        return dls(state, depth_limit, max_expansions=budget), None
    raise ValueError(f"Unknown algorithm: {name}")


def board_text(board):
    """Three text lines for a board, blank shown as '_'."""
    return [" ".join("_" if t == 0 else str(t) for t in board[r:r + 3])
            for r in range(0, 9, 3)]


def format_trace(result, max_steps=None):
    """Every step as text (traceable output). max_steps=None prints all."""
    lines = []
    for i, board in enumerate(result.path):
        if max_steps is not None and i > max_steps:
            lines.append(f"... {len(result.path) - 1 - max_steps} more steps "
                         "(download the full trace) ...")
            break
        lines.append("Start" if i == 0
                     else f"Step {i}: blank moves {result.moves[i - 1]}")
        lines.extend(board_text(board))
        lines.append("")
    return "\n".join(lines)


def result_row(result):
    """One comparison-table row. None becomes '-' so columns stay integers."""
    def show(value):
        return "-" if value is None else value

    if len(result.moves) <= 30:
        moves = " ".join(result.moves) if result.moves else "-"
    else:
        moves = f"{len(result.moves)} moves"
    return {
        "Algorithm": result.algorithm,
        "Status": result.status,
        "Path cost": show(result.path_cost),
        "Nodes expanded": result.nodes_expanded,
        "Search depth": show(result.search_depth),
        "Time (s)": round(result.running_time, 6),
        "Moves": moves,
    }


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def render_report(result, iterations, state):
    """Print every item the assignment asks for."""
    st.subheader(f"Report data - {result.algorithm}")
    st.caption(f"Initial state: {','.join(map(str, state))}")

    if result.solved:
        st.success(f"Goal reached in {result.path_cost} moves.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cost of path",
                "-" if result.path_cost is None else result.path_cost)
    col2.metric("Nodes expanded", f"{result.nodes_expanded:,}")
    col3.metric("Search depth",
                "-" if result.search_depth is None else result.search_depth)
    col4.metric("Running time", f"{result.running_time:.4f} s")

    st.markdown("**Path to goal**")
    if result.moves:
        st.text_area("Moves", value=" -> ".join(result.moves), height=100,
                     disabled=True, label_visibility="collapsed")
    elif result.solved:
        st.write("The puzzle is already at the goal (0 moves).")
    else:
        st.write(f"No path returned (status: {result.status}).")

    if iterations:
        st.markdown("**IDS iterations**")
        st.dataframe(
            pd.DataFrame([{
                "Depth limit": it.depth_limit,
                "DLS status": it.status,
                "Nodes expanded": it.nodes_expanded,
                "Time (s)": round(it.running_time, 6),
            } for it in iterations]),
            hide_index=True)

    with st.expander("Data structures and how this algorithm works"):
        st.write(ALGORITHM_NOTES.get(result.algorithm, ""))

    if result.path:
        with st.expander("Traceable output - every step printed"):
            st.code(format_trace(result, TRACE_DISPLAY_STEPS), language=None)
        st.download_button("Download full step trace (.txt)",
                           data=format_trace(result),
                           file_name="trace.txt", mime="text/plain")


def render_comparison(state, depth_limit, budget):
    """Run every main algorithm on the same board and tabulate the results."""
    st.subheader("Compare all algorithms on this board")
    st.caption("BFS, DFS, IDS, A* Manhattan and A* Euclidean. "
               "The expansion budget above applies to DFS and IDS.")

    if st.button("Run all algorithms", key="s2_run_all"):
        rows = []
        with st.spinner("Running all algorithms..."):
            for name in SOLVERS[:5]:
                result, _ = run_solver(name, state, depth_limit, budget)
                rows.append(result_row(result))
        st.session_state["s2_compare"] = (state, pd.DataFrame(rows))

    saved = st.session_state.get("s2_compare")
    if saved is None:
        return
    saved_state, table = saved
    st.caption(f"Board: {','.join(map(str, saved_state))}")
    st.dataframe(table, hide_index=True)
    st.download_button("Download comparison (.csv)",
                       data=table.to_csv(index=False),
                       file_name="comparison.csv", mime="text/csv")

    # Manhattan vs Euclidean, as the assignment asks.
    by_name = {row["Algorithm"]: row for row in table.to_dict("records")}
    man, euc = by_name.get("A* - Manhattan"), by_name.get("A* - Euclidean")
    if man and euc and man["Status"] == euc["Status"] == "success":
        st.info(
            f"Manhattan expanded {man['Nodes expanded']:,} nodes, Euclidean "
            f"{euc['Nodes expanded']:,}; path costs {man['Path cost']} and "
            f"{euc['Path cost']}. Both heuristics are admissible (Euclidean "
            "is never larger than Manhattan), but Manhattan is more "
            "informed, so it typically expands fewer nodes.")


def main():
    st.set_page_config(page_title="8-Puzzle AI Solver", layout="centered")
    st.title("8-Puzzle AI Solver")
    st.caption("Alexandria University - AI Assignment 1. "
               "Goal state: 0,1,2,3,4,5,6,7,8")

    state = render_puzzle_input(key="puzzle")
    if state is None:                    # invalid or unsolvable input
        st.stop()

    st.subheader("Algorithm")
    solver = st.selectbox("Choose the search algorithm", SOLVERS,
                          key="s2_solver")

    depth_limit = 5
    if solver.startswith("DLS"):
        depth_limit = int(st.number_input(
            "Depth limit", min_value=0, max_value=100, value=5, step=1,
            key="s2_limit"))

    budget = 0
    if solver in ("DFS", "DLS (fixed depth limit)") or solver.startswith("IDS"):
        budget = int(st.number_input(
            "Max node expansions (0 = unlimited)", min_value=0,
            value=2_000_000, step=100_000, key="s2_budget",
            help="Safety limit so a hard board cannot freeze the page. "
                 "Reaching it gives status 'cutoff', not 'unsolvable'."))

    if st.button("Solve", key="s2_solve"):
        with st.spinner(f"Running {solver}..."):
            result, iterations = run_solver(solver, state, depth_limit, budget)
        # Keep the result: every click on Next/Play reruns this whole script.
        st.session_state["s2_result"] = result
        st.session_state["s2_iters"] = iterations
        st.session_state["s2_state"] = state
        st.session_state["s2_solver_used"] = solver

    result = st.session_state.get("s2_result")
    if result is not None:
        shown_state = st.session_state["s2_state"]
        if shown_state != state:
            st.warning("The board changed since the last run - "
                       "press Solve to update the results.")
        render_report(result, st.session_state.get("s2_iters"), shown_state)
        st.subheader("Step-by-step viewer")
        render_solution_viewer(result, key="s2_view", initial_state=shown_state)

    st.divider()
    render_comparison(state, depth_limit, budget)


if __name__ == "__main__":
    main()