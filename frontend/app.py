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
from frontend.dashboard import render_dashboard
from frontend.visualization import render_solution_viewer

SOLVERS = [
    "BFS",
    "DFS",
    "IDS (Iterative DFS)",
    "A* - Manhattan",
    "A* - Euclidean",
    "DLS (fixed depth limit)",
]

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


def main():
    st.set_page_config(page_title="8-Puzzle AI Solver", layout="wide")
    st.title("8-Puzzle AI Solver")
    st.caption("Goal state: 0,1,2,3,4,5,6,7,8"  )
               

    # puzzle on the left, solving controls on the right, reports below
    left, right = st.columns(2, gap="large")

    with left.container(border=True):
        state = render_puzzle_input(key="puzzle")

    with right.container(border=True):
        st.subheader("Algorithm")
        if state is None:                # invalid or unsolvable input
            st.info("Fix the board on the left to enable solving.")
            solve_clicked = all_clicked = False
        else:
            solver = st.selectbox("Choose the search algorithm", SOLVERS,
                                  key="s2_solver")

            depth_limit = 5
            if solver.startswith("DLS"):
                depth_limit = int(st.number_input(
                    "Depth limit", min_value=0, max_value=100, value=5,
                    step=1, key="s2_limit"))

            budget = int(st.number_input(
                "Max node expansions for DFS / IDS / DLS (0 = unlimited)",
                min_value=0, value=2_000_000, step=100_000, key="s2_budget",
                help="Safety limit so a hard board cannot freeze the page. "
                     "Reaching it gives status 'cutoff', not 'unsolvable'."))

            solve_col, all_col = st.columns(2)
            solve_clicked = solve_col.button(
                "Solve", key="s2_solve", use_container_width=True)
            all_clicked = all_col.button(
                "Solve with all", key="s2_run_all", use_container_width=True)

    if state is None:
        st.stop()

    if solve_clicked:
        with st.spinner(f"Running {solver}..."):
            result, iterations = run_solver(solver, state, depth_limit, budget)
        # Keep the result: every click on Next/Play reruns this whole script.
        st.session_state["s2_result"] = result
        st.session_state["s2_iters"] = iterations
        st.session_state["s2_state"] = state
        st.session_state["s2_solver_used"] = solver
        st.session_state.pop("s2_all", None)

    if all_clicked:
        with st.spinner("Running all algorithms..."):
            results = [run_solver(name, state, depth_limit, budget)[0]
                       for name in SOLVERS[:5]]
        st.session_state["s2_all"] = (state, results)
        st.session_state.pop("s2_result", None)

    result = st.session_state.get("s2_result")
    if result is not None:
        shown_state = st.session_state["s2_state"]
        if shown_state != state:
            st.warning("The board changed since the last run - "
                       "press Solve to update the results.")
        with st.container(border=True):
            render_report(result, st.session_state.get("s2_iters"), shown_state)
        with st.container(border=True):
            st.subheader("Step-by-step viewer")
            render_solution_viewer(result, key="s2_view",
                                   initial_state=shown_state)

    saved = st.session_state.get("s2_all")
    if saved is not None:
        saved_state, results = saved
        if saved_state != state:
            st.warning("The board changed since the last run - "
                       "press Solve with all to update the dashboard.")
        with st.container(border=True):
            render_dashboard(results, saved_state)


if __name__ == "__main__":
    main()