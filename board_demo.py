import streamlit as st

from frontend.board import render_puzzle_input

st.set_page_config(
    page_title="8-Puzzle Board Demo",
    layout="centered",
)

st.title("8-Puzzle Board Demo")

state = render_puzzle_input()

if state is not None:
    st.success(f"Valid puzzle: {state}")