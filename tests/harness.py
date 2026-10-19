"""Minimal host used by the tests: renders one section with the real sidebar."""

import importlib
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.filters import sidebar_filters  # noqa: E402

st.session_state["filters"] = sidebar_filters()
importlib.import_module(f"sections.{st.session_state['_section']}").render()
