"""
Reusable puzzle input and board display for Streamlit.

"""

import random

import streamlit as st

from core.puzzle import (
    GOAL_STATE,
    validate_state,
    is_solvable,
    get_neighbors,
)

DEFAULT_STATE = (1, 2, 5, 3, 4, 0, 6, 7, 8)


def state_to_text(state):
    """Convert a puzzle state to comma-separated text."""
    return ",".join(str(tile) for tile in state)


def parse_state(text):
    """Parse comma-separated puzzle input."""
    try:
        state = tuple(
            int(value.strip())
            for value in text.split(",")
        )
    except ValueError as exc:
        raise ValueError(
            "Enter nine integers separated by commas."
        ) from exc

    return validate_state(state)


def random_solvable_state(steps=30):
    """
    Generate a solvable state by making legal random moves
    starting from the goal.

    This is not a uniform random sample of all solvable states.
    """
    state = GOAL_STATE
    previous_state = None

    for _ in range(steps):
        options = [
            neighbor
            for _, neighbor in get_neighbors(state)
            if neighbor != previous_state
        ]

        next_state = random.choice(options)

        previous_state = state
        state = next_state

    return state


def render_board(state):
    """Draw a 3x3 puzzle board using Streamlit HTML."""
    state = validate_state(state)

    tiles_html = ""

    for tile in state:
        if tile == 0:
            tiles_html += '<div class="puzzle-tile blank"></div>'
        else:
            tiles_html += (
                f'<div class="puzzle-tile">{tile}</div>'
            )

    html = f"""
    <style>
    .puzzle-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        max-width: 240px;
        margin: 12px auto;
    }}

    .puzzle-tile {{
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        background: #273449;
        color: #ffffff;
        border: 1px solid #46566e;
        font-size: 28px;
        font-weight: 700;
    }}

    .puzzle-tile.blank {{
        background: rgba(110, 130, 160, 0.08);
        border: 2px dashed #64748b;
    }}
    </style>
    <div class="puzzle-grid">
        {tiles_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_puzzle_input(key="puzzle"):
    """
    Render puzzle input controls (comma list OR one box per tile).

    Returns:
        Valid tuple state, or None for invalid input.
    """
    text_key = f"{key}_text"
    mode_key = f"{key}_mode"
    tile_keys = [f"{key}_tile{i}" for i in range(9)]

    def set_board(state):
        # keep both input styles in sync
        st.session_state[text_key] = state_to_text(state)
        for k, tile in zip(tile_keys, state):
            st.session_state[k] = tile

    if text_key not in st.session_state:
        set_board(DEFAULT_STATE)

    def reset_board():
        set_board(DEFAULT_STATE)

    def randomize_board():
        set_board(random_solvable_state())

    def mode_changed():
        # carry the board over when the person switches input style
        if st.session_state[mode_key] == "One by one":
            try:
                set_board(parse_state(st.session_state[text_key]))
            except ValueError:
                pass
        else:
            st.session_state[text_key] = state_to_text(
                [st.session_state[k] for k in tile_keys])

    st.subheader("Puzzle Configuration")

    mode = st.radio("Input style", ["List", "One by one"], key=mode_key,
                    horizontal=True, on_change=mode_changed)

    if mode == "List":
        st.text_input(
            "Enter the nine tiles (0 represents the blank)",
            key=text_key,
            help="Example: 1,2,5,3,4,0,6,7,8",
        )
    else:
        st.caption("Enter the tiles row by row (0 represents the blank)")
        for r in range(3):
            cols = st.columns(3)
            for c in range(3):
                i = r * 3 + c
                cols[c].number_input(f"Row {r + 1}, col {c + 1}", 0, 8,
                                     key=tile_keys[i], step=1)

    col1, col2 = st.columns(2)

    with col1:
        st.button(
            "Randomize",
            on_click=randomize_board,
            key=f"{key}_randomize",
            use_container_width=True,
        )

    with col2:
        st.button(
            "Reset",
            on_click=reset_board,
            key=f"{key}_reset",
            use_container_width=True,
        )

    try:
        if mode == "List":
            state = parse_state(st.session_state[text_key])
        else:
            state = validate_state(tuple(
                int(st.session_state[k]) for k in tile_keys))
    except ValueError as exc:
        st.error(str(exc))
        return None

    if not is_solvable(state):
        st.warning(
            "This puzzle is unsolvable. "
            "Enter a different state."
        )
        return None

    st.write("Current state:")
    render_board(state)

    return state