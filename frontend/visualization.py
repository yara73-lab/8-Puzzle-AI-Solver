import time

import streamlit as st

from core.puzzle import GOAL_STATE

# Direction of the BLANK for each move name, and the opposite direction that
# the neighbouring TILE travels (a blank moving Up means a tile slides Down).
_OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
PLAY_DELAY = 0.8     # seconds per move while playing
_ARROWS = {"Up": "⬆", "Down": "⬇", "Left": "⬅", "Right": "➡"}


# ---------------------------------------------------------------------------
# Pure helpers (no Streamlit calls -> easy to test)
# ---------------------------------------------------------------------------

def clamp_step(step, total_moves):
    """Keep a step index inside 0 .. total_moves."""
    return max(0, min(int(step), max(int(total_moves), 0)))


def moved_tile_index(previous_state, current_state):
    """
    Board index of the tile that moved between two consecutive states.

    The tile that moved now sits where the blank used to be, so it is the
    value of ``current_state`` at the blank's index in ``previous_state``.
    """
    return previous_state.index(0)


def describe_move(previous_state, current_state, move):
    """Human readable text for one transition, e.g. 'Blank moves Left (tile 5 slides Right)'."""
    tile = current_state[moved_tile_index(previous_state, current_state)]
    arrow = _ARROWS.get(move, "")
    return (
        f"{arrow} Blank moves **{move}** "
        f"(tile **{tile}** slides {_OPPOSITE.get(move, '?')})"
    )


def board_html(state, highlight_index=None, goal_reached=False):
    """
    HTML for one 3x3 board.

    highlight_index: board index (0-8) of the tile that just moved.
    goal_reached:    tint the board green when it is the final goal state.
    """
    cells = []
    for index, tile in enumerate(state):
        classes = ["s2-tile"]
        if tile == 0:
            classes.append("s2-blank")
        if index == highlight_index:
            classes.append("s2-moved")
        text = "" if tile == 0 else str(tile)
        cells.append(f'<div class="{" ".join(classes)}">{text}</div>')

    grid_class = "s2-grid s2-goal" if goal_reached else "s2-grid"

    css = """
    <style>
    .s2-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px;
               max-width:300px; margin:12px auto; padding:12px;
               border-radius:18px; border:2px solid transparent; }
    .s2-grid.s2-goal { border-color:#22c55e; background:rgba(34,197,94,0.10); }
    .s2-tile { aspect-ratio:1; display:flex; align-items:center;
               justify-content:center; border-radius:14px; background:#273449;
               color:#ffffff; border:1px solid #46566e;
               font-size:32px; font-weight:700; }
    .s2-tile.s2-blank { background:rgba(110,130,160,0.08);
                        border:2px dashed #64748b; }
    .s2-tile.s2-moved { background:#d97706; border-color:#fbbf24; }
    </style>
    """
    return f'{css}<div class="{grid_class}">{"".join(cells)}</div>'


def _result_signature(result):
    """Identify a result so the viewer can reset when a NEW one arrives."""
    return (result.algorithm, result.status, tuple(result.path), tuple(result.moves))


# ---------------------------------------------------------------------------
# Streamlit rendering
# ---------------------------------------------------------------------------

def render_board_grid(state, highlight_index=None, goal_reached=False):
    """Draw a single 3x3 board (reusable on its own)."""
    st.markdown(board_html(state, highlight_index, goal_reached),
                unsafe_allow_html=True)


def render_unsuccessful_result(result, initial_state=None):
    """Explain a non-success result and (optionally) show the start board."""
    if result.status == "failure":
        st.error(
            f"{result.algorithm}: no solution exists for this puzzle "
            "(it is unsolvable or the whole search space was exhausted)."
        )
    elif result.status == "cutoff":
        st.warning(
            f"{result.algorithm}: search stopped by its depth/expansion limit "
            "before reaching the goal. A solution may still exist - "
            "try a larger limit."
        )
    else:  # success but nothing to show
        st.info("The result contains no path to display.")

    if initial_state is not None:
        render_board_grid(tuple(initial_state))


def _rerun():
    """st.rerun on current Streamlit, st.experimental_rerun on old ones."""
    rerun = getattr(st, "rerun", None) or st.experimental_rerun
    rerun()


def render_solution_viewer(result, key="viewer", initial_state=None,
                           show_autoplay=True):
    """
    Step-by-step viewer for a SearchResult.

    Args:
        result:         SearchResult from any algorithm.
        key:            unique prefix for the session_state/widget keys.
        initial_state:  optional board shown when there is no path.
        show_autoplay:  show the Play/Pause button and speed control.
    """
    # -- unsuccessful or empty results ------------------------------------
    if result is None:
        st.info("Run a search to see the solution here.")
        return

    if not result.solved or not result.path:
        render_unsuccessful_result(result, initial_state)
        return

    path = result.path
    moves = result.moves
    total_moves = len(path) - 1          # a path of N states has N-1 moves

    step_key = f"{key}_step"
    play_key = f"{key}_playing"
    sig_key = f"{key}_sig"

    # -- (re)initialise state when a new result is shown -------------------
    signature = _result_signature(result)
    if st.session_state.get(sig_key) != signature:
        st.session_state[sig_key] = signature
        st.session_state[step_key] = 0
        st.session_state[play_key] = False

    step = clamp_step(st.session_state.get(step_key, 0), total_moves)
    st.session_state[step_key] = step

    # -- callbacks (run BEFORE the script reruns) ---------------------------
    def go_previous():
        st.session_state[step_key] = clamp_step(
            st.session_state[step_key] - 1, total_moves)
        st.session_state[play_key] = False

    def go_next():
        st.session_state[step_key] = clamp_step(
            st.session_state[step_key] + 1, total_moves)
        st.session_state[play_key] = False

    def toggle_play():
        if st.session_state[play_key]:
            st.session_state[play_key] = False
        else:
            if st.session_state[step_key] >= total_moves:
                st.session_state[step_key] = 0     # replay from the start
            st.session_state[play_key] = True

    playing = st.session_state[play_key]
    current = path[step]
    at_goal = (step == total_moves) and tuple(current) == GOAL_STATE

    # -- summary metrics ---------------------------------------------------
    col_step, col_total, col_goal = st.columns(3)
    col_step.metric("Current step", f"{step} / {total_moves}")
    col_total.metric("Total moves", total_moves)
    col_goal.metric("Goal reached", "Yes " if at_goal else "Not yet")

    # -- the board ---------------------------------------------------------
    highlight = moved_tile_index(path[step - 1], current) if step > 0 else None
    render_board_grid(current, highlight_index=highlight, goal_reached=at_goal)

    if step == 0:
        st.caption("Initial state"
                   + (" (already the goal)" if total_moves == 0 else ""))
    else:
        st.markdown(f"Move {step}: "
                    + describe_move(path[step - 1], current, moves[step - 1]))

    # -- controls ----------------------------------------------------------
    if total_moves > 0:
        col_prev, col_play, col_next = st.columns(3)
        col_prev.button("◀ Previous", key=f"{key}_prev", on_click=go_previous,
                        disabled=step <= 0)
        col_next.button("Next ▶", key=f"{key}_next", on_click=go_next,
                        disabled=step >= total_moves)
        if show_autoplay:
            col_play.button("⏸ Pause" if playing else "▶ Play",
                            key=f"{key}_play", on_click=toggle_play)

    # -- autoplay: draw, wait, advance, rerun ------------------------------
    if playing and show_autoplay:
        if step < total_moves:
            time.sleep(PLAY_DELAY)
            st.session_state[step_key] = step + 1
            _rerun()
        else:
            st.session_state[play_key] = False     # reached the end
            _rerun()                               # refresh the button label