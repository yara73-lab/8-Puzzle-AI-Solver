"""
Comparison dashboard: shows the results of running every algorithm
on the same board.
"""

import pandas as pd
import streamlit as st


def results_table(results):
    """One row per algorithm. Unsolved runs keep their status, numbers become None."""
    rows = []
    for r in results:
        rows.append({
            "Algorithm": r.algorithm,
            "Status": r.status,
            "Path cost": r.path_cost,
            "Nodes expanded": r.nodes_expanded,
            "Search depth": r.search_depth,
            "Time (s)": round(r.running_time, 6),
        })
    return pd.DataFrame(rows)


def render_dashboard(results, state):
    st.subheader("Comparison dashboard")
    st.caption(f"Board: {','.join(map(str, state))}")

    table = results_table(results)
    st.dataframe(table, hide_index=True)
    st.download_button("Download comparison (.csv)",
                       data=table.to_csv(index=False),
                       file_name="comparison.csv", mime="text/csv")

    solved = table[table["Status"] == "success"].set_index("Algorithm")
    if solved.empty:
        st.warning("No algorithm reached the goal, so there is nothing to plot.")
        return

    # quick summary
    best_cost = solved["Path cost"].min()
    optimal = ", ".join(solved.index[solved["Path cost"] == best_cost])
    c1, c2, c3 = st.columns(3)
    c1.metric("Shortest path", f"{int(best_cost)} moves")
    c2.metric("Fewest nodes", solved["Nodes expanded"].idxmin())
    c3.metric("Fastest", solved["Time (s)"].idxmin())
    st.caption(f"Algorithms that found the shortest path: {optimal}")

    # one chart per metric
    left, middle, right = st.columns(3)
    left.markdown("**Nodes expanded**")
    left.bar_chart(solved["Nodes expanded"])
    middle.markdown("**Running time (s)**")
    middle.bar_chart(solved["Time (s)"])
    right.markdown("**Path cost**")
    right.bar_chart(solved["Path cost"])

    unsolved = table[table["Status"] != "success"]
    if not unsolved.empty:
        names = ", ".join(f"{a} ({s})" for a, s in
                          zip(unsolved["Algorithm"], unsolved["Status"]))
        st.info(f"Not plotted, did not reach the goal: {names}. "
                "'cutoff' means the expansion limit was hit.")

    # Manhattan vs Euclidean
    if {"A* - Manhattan", "A* - Euclidean"} <= set(solved.index):
        man, euc = solved.loc["A* - Manhattan"], solved.loc["A* - Euclidean"]
        st.info(
            f"Manhattan expanded {int(man['Nodes expanded']):,} nodes and "
            f"Euclidean {int(euc['Nodes expanded']):,}. Both are admissible, "
            "but Manhattan is closer to the real cost, so it usually "
            "expands fewer nodes.")