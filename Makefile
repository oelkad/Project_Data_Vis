PY ?= python

install:
	$(PY) -m pip install -r requirements.txt

data:
	$(PY) -m scripts.build_data

refresh:
	$(PY) -m scripts.build_data --refresh

run:
	streamlit run app.py

test:
	$(PY) -m pytest

.PHONY: install data refresh run test
