from pathlib import Path

import pandas as pd
import pytest

from csv_autoclean.agents.repairer import build_repairer_prompt, run_repairer
from csv_autoclean.models import (
    ColumnMissingness,
    ColumnProfile,
    DataProfile,
    MissingnessReport,
    ValidationFailure,
    ValidationReport,
    ValidationRule,
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


def _profile(
    columns: list[ColumnProfile], missingness: MissingnessReport | None = None
) -> DataProfile:
    return DataProfile(
        dataset_name="test",
        row_count=4,
        column_count=len(columns),
        duplicate_row_count=0,
        total_null_count=0,
        columns=columns,
        summary="test profile",
        missingness=missingness,
    )


def _validation(failures: list[ValidationFailure]) -> ValidationReport:
    return ValidationReport(
        passed=len(failures) == 0,
        rules_applied=[
            ValidationRule(column="age", rule_description="test rule", severity="info")
        ],
        failure_count=len(failures),
        failures=failures,
        summary="test validation summary",
    )


def test_build_repairer_prompt_includes_validation_summary() -> None:
    """The prompt restates the upstream validator's summary."""
    df = pd.DataFrame({"age": [25.0, 30.0, None]})
    profile = _profile([_column_profile("age", "age")])
    validation = _validation([])
    prompt = build_repairer_prompt("people", df, profile, validation)
    assert "test validation summary" in prompt


def test_build_repairer_prompt_includes_validation_failures() -> None:
    """A validation failure is listed in the prompt for the agent to act on."""
    df = pd.DataFrame({"patient_id": ["p1", "p1", "p2"]})
    profile = _profile([_column_profile("patient_id", "id")])
    failure = ValidationFailure(
        column="patient_id",
        rule="no duplicate ids",
        severity="critical",
        affected_rows=1,
        description="duplicate id found",
        suggested_fix="drop the duplicate row",
    )
    validation = _validation([failure])
    prompt = build_repairer_prompt("people", df, profile, validation)
    assert "patient_id" in prompt
    assert "duplicate id found" in prompt


def test_build_repairer_prompt_includes_repair_candidate_evidence() -> None:
    """Deterministic repair-candidate evidence (mean/median) is included."""
    df = pd.DataFrame({"age": [10.0, 20.0, None, 30.0]})
    missingness = MissingnessReport(
        dataset_mcar_conclusion="test",
        columns_analyzed=[
            ColumnMissingness(
                column="age",
                null_count=1,
                null_pct=25.0,
                mechanism="MCAR",
                confidence="high",
                evidence="test evidence",
                safe_to_impute=True,
            )
        ],
        summary="test missingness",
    )
    profile = _profile([_column_profile("age", "age")], missingness)
    validation = _validation([])
    prompt = build_repairer_prompt("people", df, profile, validation)
    assert "Repair candidate evidence" in prompt
    assert "mean" in prompt


@pytest.mark.llm
def test_run_repairer_drops_duplicate_rows_and_writes_output(tmp_path: Path) -> None:
    """Against a dataset with a known duplicate id, the agent decides to
    drop it, the repaired CSV is written, and rows_dropped reflects the
    real count, not whatever the agent claims."""
    df = pd.DataFrame({"patient_id": ["p1", "p1", "p2"], "age": [25.0, 25.0, 30.0]})
    profile = _profile(
        [_column_profile("patient_id", "id"), _column_profile("age", "age")]
    )
    failure = ValidationFailure(
        column="patient_id",
        rule="no duplicate ids",
        severity="critical",
        affected_rows=1,
        description="duplicate id found",
        suggested_fix="drop the duplicate row",
    )
    validation = _validation([failure])
    output_path = str(tmp_path / "repaired.csv")

    report = run_repairer("people", df, profile, validation, output_path)

    assert report.total_repairs == len(report.actions)
    assert report.rows_dropped == 1
    repaired = pd.read_csv(output_path)
    assert len(repaired) == 2
