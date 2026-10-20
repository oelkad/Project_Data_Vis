"""Smoke tests: every section renders without exception under various filters."""

import pytest
from streamlit.testing.v1 import AppTest

SECTIONS = ["intro", "overview", "deep_dives", "what_if", "conclusions", "data_quality"]
SCENARIOS = {
    "default": {},
    "rural": {"f_area": "Rural"},
    "overseas": {"f_territory": "Overseas"},
    "e-scooters": {"f_modes": ["E-scooter (EDP)"]},
    "single-year": {"f_years": (2020, 2020)},
    "region-urban": {"f_territory": "All of France", "f_regions": ["Bretagne"], "f_area": "Urban"},
    "one-small-dep": {"f_deps": ["23"], "f_metric": "Lethality (killed per 100 accidents)"},
}


@pytest.mark.parametrize("scenario", list(SCENARIOS))
@pytest.mark.parametrize("section", SECTIONS)
def test_section_renders(section, scenario):
    at = AppTest.from_file("harness.py", default_timeout=180)
    at.session_state["_section"] = section
    for key, value in SCENARIOS[scenario].items():
        at.session_state[key] = value
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_full_app_with_author_card():
    at = AppTest.from_file("../app.py", default_timeout=180)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    sidebar_text = " ".join(m.value for m in at.sidebar.markdown)
    assert "Othmane El Kadiri" in sidebar_text and "Data Analysis & Visualization" in sidebar_text
