"""Road deaths in France, 2020–2024 – a Streamlit data story.

Run:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Road deaths in France – a data story", page_icon="🛣️", layout="wide",
                   initial_sidebar_state="expanded")

from sections import conclusions, data_quality, deep_dives, intro, overview, what_if  # noqa: E402
from utils.about import AUTHOR, sidebar_about, sidebar_logo  # noqa: E402
from utils.filters import sidebar_filters  # noqa: E402
from utils.io import license_text  # noqa: E402

pages = {
    "The story": [
        st.Page(intro.render, title="1 · Why it matters", icon=":material/flag:", url_path="intro", default=True),
        st.Page(overview.render, title="2 · The big picture", icon=":material/monitoring:", url_path="overview"),
        st.Page(deep_dives.render, title="3 · Where, who, when", icon=":material/travel_explore:",
                url_path="deep-dives"),
        st.Page(what_if.render, title="4 · What would it take?", icon=":material/tune:", url_path="what-if"),
        st.Page(conclusions.render, title="5 · Takeaways", icon=":material/lightbulb:", url_path="takeaways"),
    ],
    "Behind the data": [
        st.Page(data_quality.render, title="Data quality & method", icon=":material/fact_check:",
                url_path="data-quality"),
    ],
}
sidebar_logo()
page = st.navigation(pages, expanded=True)

st.session_state["filters"] = sidebar_filters()
st.session_state.setdefault("describe_charts", True)
st.sidebar.toggle("Describe every chart in text", key="describe_charts",
                  help="Accessibility: prints a text description under each chart (also given as alt text).")
sidebar_about()

page.run()

st.divider()
st.caption(license_text() + f" · © 2026 {AUTHOR['name']}, Efrei Paris · Built with Streamlit · #EFREIDataStories2026")
