"""Road deaths in France, 2020–2024 – a Streamlit data story.   Run: streamlit run app.py"""

import streamlit as st

st.set_page_config(page_title="Road deaths in France – a data story", page_icon="🛣️", layout="wide")

from sections import conclusions, data_quality, deep_dives, intro, overview, what_if  # noqa: E402
from utils import constants as K  # noqa: E402
from utils.about import AUTHOR, sidebar_logo  # noqa: E402
from utils.filters import sidebar_filters  # noqa: E402

sidebar_logo()
page = st.navigation({
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
}, expanded=True)
st.session_state["filters"] = sidebar_filters()
page.run()

st.divider()
st.caption(f"**Data:** [{K.DATASET_TITLE}]({K.DATASET_PAGE}) – ONISR, Ministère de l'Intérieur, data.gouv.fr, "
           "Licence Ouverte v2.0 · Department boundaries: IGN via france-geojson · "
           f"© 2026 {AUTHOR}, Efrei Paris · #EFREIDataStories2026")
