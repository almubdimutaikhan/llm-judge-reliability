.PHONY: reproduce verify figures

reproduce: verify figures

verify:
	python scripts/analyze.py
	python -m unittest discover -s tests -v

figures:
	python scripts/figures.py
