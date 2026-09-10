import pandas as pd
from pydantic_ai import Agent

from csv_autoclean.models import DataProfile, RepairReport, ValidationReport
from csv_autoclean.repair_rules import (
    compute_repair_candidates,
    drop_duplicate_rows,
    impute_column_mean,
    impute_column_median,
    impute_column_mode,
)

SYSTEM_PROMPT = """You are the Repairer stage of a data quality pipeline.

You are given the upstream Profiler's DataProfile, the Validator's
ValidationReport (its failures), and deterministic repair-candidate
evidence (exact mean/median/mode per column, not estimates). Decide, for
each failure that can be safely and mechanically fixed, a RepairAction:

- A failure whose column the Profiler's missingness analysis marked as
  NOT safe to impute must never be auto-imputed. Set action_taken to
  "flagged" and add a plain-English entry to `unresolved` explaining why
  it needs human review instead.
- A duplicate-id failure: action_taken "dropped_rows".
- A missing-value failure in a column safe to impute: action_taken
  "imputed_mean" or "imputed_median" for numeric columns (pick whichever
  the repair-candidate evidence suggests is more robust to outliers) or
  "imputed_mode" for non-numeric columns.
- An implausible-value failure (e.g. a negative value in a column that
  should never be negative): action_taken "capped".
- A malformed-value failure (e.g. a malformed email) has no single
  deterministic correct reformatting: action_taken "flagged", added to
  `unresolved`. Do not attempt "reformatted" in this version.
- Anything else you judge not worth auto-fixing: action_taken "skipped",
  with the reason explained and, if relevant, added to `unresolved`.

For every RepairAction, `before_example` and `after_example` should be
concrete representative values (cite the deterministic evidence given),
and `reason` should explain the choice, especially why an imputation
strategy was picked over the alternative.

`total_repairs` and `rows_dropped` are provided by you as a best estimate
but will be recalculated deterministically after your decisions are
applied, do not worry about getting the exact counts perfect.

summary: 2-3 sentences of plain-English repair assessment.
"""

repairer_agent = Agent(
    "anthropic:claude-opus-5",
    output_type=RepairReport,
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
)


def build_repairer_prompt(
    dataset_name: str,
    df: pd.DataFrame,
    profile: DataProfile,
    validation: ValidationReport,
) -> str:
    lines = [
        f"Dataset: {dataset_name}",
        f"Profile summary: {profile.summary}",
        f"Validation summary: {validation.summary}",
        "",
    ]

    if validation.failures:
        lines.append("Validation failures to address:")
        for failure in validation.failures:
            lines.append(
                f"- column={failure.column!r} rule={failure.rule!r} "
                f"severity={failure.severity} affected_rows="
                f"{failure.affected_rows} description={failure.description!r} "
                f"suggested_fix={failure.suggested_fix!r}"
            )
    else:
        lines.append("No validation failures to address.")

    evidence = compute_repair_candidates(df, profile)
    if evidence:
        lines.append("")
        lines.append("Repair candidate evidence (ground truth, restate accurately):")
        for line in evidence:
            lines.append(f"- {line}")

    return "\n".join(lines)


def _apply_repair_action(df: pd.DataFrame, action_taken: str, column: str) -> None:
    if action_taken == "imputed_mean":
        df[column] = impute_column_mean(df, column)
    elif action_taken == "imputed_median":
        df[column] = impute_column_median(df, column)
    elif action_taken == "imputed_mode":
        df[column] = impute_column_mode(df, column)
    elif action_taken == "capped":
        numeric = pd.to_numeric(df[column], errors="coerce")
        df[column] = numeric.clip(lower=0)


def run_repairer(
    dataset_name: str,
    df: pd.DataFrame,
    profile: DataProfile,
    validation: ValidationReport,
    output_path: str,
) -> RepairReport:
    prompt = build_repairer_prompt(dataset_name, df, profile, validation)
    result = repairer_agent.run_sync(prompt)
    report = result.output

    repaired = df.copy()
    original_row_count = len(repaired)

    dropped_columns = [
        action.column
        for action in report.actions
        if action.action_taken == "dropped_rows"
    ]
    if dropped_columns:
        repaired = drop_duplicate_rows(repaired, subset=dropped_columns)

    for action in report.actions:
        if action.action_taken != "dropped_rows":
            _apply_repair_action(repaired, action.action_taken, action.column)

    repaired.to_csv(output_path, index=False)

    report.rows_dropped = original_row_count - len(repaired)
    report.output_path = output_path
    return report
