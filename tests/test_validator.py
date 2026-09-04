import pandas as pd
import pytest

from csv_autoclean.agents.validator import build_validator_prompt, run_validator
from csv_autoclean.models import ColumnProfile, DataProfile


def _profile(
    columns: list[ColumnProfile], summary: str = "test profile"
) -> DataProfile:
    return DataProfile(
        dataset_name="test",
        row_count=4,
        column_count=len(columns),
        duplicate_row_count=0,
        total_null_count=0,
        columns=columns,
        summary=summary,
    )


def _column_profile(name: str, inferred_type: str) -> ColumnProfile:
    return ColumnProfile(
        name=name,
        dtype="object",
        null_count=0,
        null_pct=0.0,
        unique_count=1,
        unique_pct=100.0,
        sample_values=[],
        inferred_type=inferred_type,
    )


def test_build_validator_prompt_includes_profile_summary() -> None:
    """The prompt restates the upstream profiler's summary."""
    df = pd.DataFrame({"patient_id": ["p1", "p2", "p3"]})
    profile = _profile(
        [_column_profile("patient_id", "id")], summary="looks clean overall"
    )
    prompt = build_validator_prompt("people", df, profile)
    assert "looks clean overall" in prompt


def test_build_validator_prompt_includes_deterministic_violations() -> None:
    """A deterministic rule violation (duplicate id) is included in the prompt."""
    df = pd.DataFrame({"patient_id": ["p1", "p1", "p2"]})
    profile = _profile([_column_profile("patient_id", "id")])
    prompt = build_validator_prompt("people", df, profile)
    assert "Deterministic rule violations" in prompt
    assert "patient_id" in prompt


def test_build_validator_prompt_reports_no_violations_when_clean() -> None:
    """A dataset with no deterministic violations says so explicitly."""
    df = pd.DataFrame({"patient_id": ["p1", "p2", "p3"]})
    profile = _profile([_column_profile("patient_id", "id")])
    prompt = build_validator_prompt("people", df, profile)
    assert "No deterministic rule violations were detected." in prompt


@pytest.mark.llm
def test_run_validator_produces_a_valid_validation_report() -> None:
    """Against a dataset with a known duplicate id, the agent's output
    matches the schema and flags the violation as a failure."""
    df = pd.DataFrame({"patient_id": ["p1", "p1", "p2"], "age": [25, 30, 45]})
    profile = _profile(
        [_column_profile("patient_id", "id"), _column_profile("age", "age")]
    )
    report = run_validator("people", df, profile)
    assert report.failure_count == len(report.failures)
    assert any(f.column == "patient_id" for f in report.failures)
