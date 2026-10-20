"""Author, school and course information shown on every page (sidebar) and on the intro page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parents[1] / "assets" / "efrei_logo.png"
SCHOOL_URL = "https://www.efrei.fr"

AUTHOR = {
    "name": "Othmane El Kadiri",
    "programme": "Data and AI",
    "promo": "Promo 2028",
    "email": "othmane.el-kadiri@efrei.net",
    "linkedin": "https://www.linkedin.com/in/othmane-el-kadiri-59733b252/",
    "github": "https://github.com/oelkad",
}
COURSE = {
    "name": "Data Analysis & Visualization",
    "year": "2026–2027",
    "professor": "Mano Joseph MATHEW",
    "professor_linkedin": "https://www.linkedin.com/in/manomathew/",
    "professor_email": "mano.mathew@efrei.fr",
}


def sidebar_logo() -> None:
    """Efrei logo at the top of the sidebar (every page)."""
    if LOGO.exists():
        st.logo(str(LOGO), size="large", link=SCHOOL_URL)


def sidebar_about() -> None:
    """Author and course card at the bottom of the sidebar (every page)."""
    a, c = AUTHOR, COURSE
    with st.sidebar:
        st.divider()
        if LOGO.exists():
            st.image(str(LOGO), width=150)
        st.markdown(
            f"**{a['name']}**  \n"
            f"{a['programme']} · {a['promo']}  \n"
            f"[{a['email']}](mailto:{a['email']})  \n"
            f"[LinkedIn]({a['linkedin']}) · [GitHub]({a['github']})"
        )
        st.markdown(
            f"**Course:** {c['name']} ({c['year']})  \n"
            f"**Professor:** [{c['professor']}]({c['professor_linkedin']})  \n"
            f"[{c['professor_email']}](mailto:{c['professor_email']})"
        )


def about_card() -> None:
    """Author / course card shown under the intro title."""
    a, c = AUTHOR, COURSE
    with st.container(border=True):
        logo_col, author_col, course_col = st.columns([1, 2, 2], vertical_alignment="center")
        if LOGO.exists():
            logo_col.image(str(LOGO), width=170)
        author_col.markdown(
            f"**{a['name']}**  \n"
            f"{a['programme']} · Efrei Paris · {a['promo']}  \n"
            f"[{a['email']}](mailto:{a['email']})  \n"
            f"[LinkedIn]({a['linkedin']}) · [GitHub]({a['github']})"
        )
        course_col.markdown(
            f"**Course:** {c['name']}  \n"
            f"**Academic year:** {c['year']}  \n"
            f"**Professor:** {c['professor']}  \n"
            f"[{c['professor_email']}](mailto:{c['professor_email']})  \n"
            f"[LinkedIn]({c['professor_linkedin']})"
        )
