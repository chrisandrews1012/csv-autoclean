import pandas as pd
from pydantic_ai import Agent

from csv_autoclean.models import DataProfile, ValidationReport
from csv_autoclean.validation_rules import compute_validation_evidence

SYSTEM_PROMPT = """You are the Validator stage of a data quality pipeline.

You are given the upstream Profiler's DataProfile plus a set of
deterministic rule violations computed directly from the data (exact, not
estimates). Restate that evidence accurately in your structured output,
and add the judgment it can't provide on its own:

- rules_applied: state each concrete rule you checked, including any
  additional rules you judge relevant given the profile beyond the
  deterministic evidence, each with a severity level.
- failures: one ValidationFailure per violation, with column, rule,
  severity, affected_rows, a plain-English description, and a concrete
  suggested_fix.
- Severity guide: "critical" for issues that would corrupt downstream
  analysis if repaired naively (duplicate ids, unsafe-to-impute nulls,
  implausible negative values); "consideration" for issues worth a human
  look but not blocking (malformed but recoverable formatting); "info"
  for observations that don't need action.
- passed: true only if there are zero critical failures.
- summary: 2-3 sentences of plain-English validation assessment.
"""

validator_agent = Agent(
    "anthropic:claude-opus-5",
    output_type=ValidationReport,
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
)


def build_validator_prompt(
    dataset_name: str, df: pd.DataFrame, profile: DataProfile
) -> str:
    evidence = compute_validation_evidence(df, profile)

    lines = [
        f"Dataset: {dataset_name}",
        f"Profile summary: {profile.summary}",
        "",
    ]
    if evidence:
        lines.append(
            "Deterministic rule violations (ground truth, restate accurately):"
        )
        for line in evidence:
            lines.append(f"- {line}")
    else:
        lines.append("No deterministic rule violations were detected.")

    return "\n".join(lines)


def run_validator(
    dataset_name: str, df: pd.DataFrame, profile: DataProfile
) -> ValidationReport:
    prompt = build_validator_prompt(dataset_name, df, profile)
    result = validator_agent.run_sync(prompt)
    return result.output
