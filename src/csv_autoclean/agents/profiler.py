import pandas as pd
from pydantic_ai import Agent

from csv_autoclean.models import DataProfile
from csv_autoclean.stats import (
    compute_column_stats,
    compute_dataset_stats,
    compute_missingness_evidence,
)

SYSTEM_PROMPT = """You are the Profiler stage of a data quality pipeline.

You are given deterministic statistics computed directly from a dataset
(exact, not estimates) plus a sample of raw values per column. Restate
those numbers accurately in your structured output, and add the judgment
the numbers can't provide on their own:

- inferred_type per column: a short semantic label (id, email, age, date,
  currency, categorical, numeric, text, boolean, unknown) based on the
  column name and sample values.
- For every column with nulls, decide the missingness mechanism (MCAR,
  MAR, or MNAR), a confidence level (high, medium, low), and an evidence
  string. You are given a deterministic correlation check for each such
  column; use it as your primary evidence. If it found a correlation with
  an observed column, the mechanism is MAR, not MNAR: missingness
  explained by something you can see isn't MNAR by definition, however
  suggestive it looks. Reserve MNAR for missingness you have reason to
  think depends on the hidden value itself, e.g. a sensitive category
  being systematically under-recorded, with no observed-column
  explanation. If there is no strong correlation and nothing suggests the
  missingness depends on the hidden value, call it MCAR. Set
  safe_to_impute to false for anything classified as MNAR.
- summary: 2-3 sentences of plain-English data quality assessment.
"""

profiler_agent = Agent(
    "anthropic:claude-opus-5",
    output_type=DataProfile,
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
)


def build_profiler_prompt(dataset_name: str, df: pd.DataFrame) -> str:
    dataset_stats = compute_dataset_stats(df)
    missingness_evidence = compute_missingness_evidence(df)

    lines = [
        f"Dataset: {dataset_name}",
        f"Dataset stats (ground truth, restate exactly): {dataset_stats}",
        "",
        "Columns:",
    ]
    for column in df.columns:
        column_stats = compute_column_stats(df[column])
        lines.append(f"- {column}: {column_stats}")

    if missingness_evidence:
        lines.append("")
        lines.append("Missingness evidence (deterministic, use as primary signal):")
        for text in missingness_evidence.values():
            lines.append(f"- {text}")

    return "\n".join(lines)


def run_profiler(dataset_name: str, df: pd.DataFrame) -> DataProfile:
    prompt = build_profiler_prompt(dataset_name, df)
    result = profiler_agent.run_sync(prompt)
    return result.output
