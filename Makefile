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
	uv run python -m data.generate_hr
	uv run python -m data.generate_hr_clean
	uv run python -m data.generate_ecommerce
	uv run python -m data.generate_medical
