.PHONY: run serve test-fast test-llm eval data

run:
	uv run python -m csv_autoclean.pipeline data/raw/hr_messy.csv

serve:
	uv run uvicorn csv_autoclean.server:app --reload

test-fast:
	uv run pytest -m "not llm"

test-llm:
	uv run pytest -m llm

eval:
	uv run python -m evals.runner

data:
	uv run python data/generate_hr.py
	uv run python data/generate_hr_clean.py
	uv run python data/generate_ecommerce.py
	uv run python data/generate_medical.py
