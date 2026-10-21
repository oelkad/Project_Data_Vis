"""Author, school and course card (intro page) and Efrei logo (sidebar, every page)."""

from pathlib import Path

import streamlit as st

LOGO = str(Path(__file__).resolve().parents[1] / "assets" / "efrei_logo.png")
AUTHOR = "Othmane El Kadiri"


def sidebar_logo() -> None:
    st.logo(LOGO, size="large", link="https://www.efrei.fr")


def about_card() -> None:
    with st.container(border=True):
        logo, author, course = st.columns([1, 2, 2], vertical_alignment="center")
        logo.image(LOGO, width=170)
        author.markdown(
            f"**{AUTHOR}**  \n"
            "Data and AI · Efrei Paris · Promo 2028  \n"
            "[othmane.el-kadiri@efrei.net](mailto:othmane.el-kadiri@efrei.net)  \n"
            "[LinkedIn](https://www.linkedin.com/in/othmane-el-kadiri-59733b252/) · [GitHub](https://github.com/oelkad)")
        course.markdown(
            "**Course:** Data Analysis & Visualization  \n"
            "**Academic year:** 2026–2027  \n"
            "**Professor:** Mano Joseph MATHEW  \n"
            "[mano.mathew@efrei.fr](mailto:mano.mathew@efrei.fr)  \n"
            "[LinkedIn](https://www.linkedin.com/in/manomathew/)")
