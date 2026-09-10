import pandas as pd

from csv_autoclean.models import (
    ColumnMissingness,
    ColumnProfile,
    DataProfile,
    MissingnessReport,
)
from csv_autoclean.validation_rules import (
    check_duplicate_ids,
    check_malformed_emails,
    check_negative_numeric_values,
    check_unsafe_missingness,
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


def test_check_unsafe_missingness_flags_columns_not_safe_to_impute() -> None:
    """A null-containing column the profiler marked unsafe to impute is flagged."""
    df = pd.DataFrame({"prescription_notes": ["a", None, "b", None]})
    missingness = MissingnessReport(
        dataset_mcar_conclusion="likely MNAR",
        columns_analyzed=[
            ColumnMissingness(
                column="prescription_notes",
                null_count=2,
                null_pct=50.0,
                mechanism="MNAR",
                confidence="high",
                evidence="no correlated column found",
                safe_to_impute=False,
            )
        ],
        summary="one unsafe column",
    )
    profile = _profile([_column_profile("prescription_notes", "text")], missingness)
    evidence = check_unsafe_missingness(df, profile)
    assert len(evidence) == 1
    assert "prescription_notes" in evidence[0]


def test_check_unsafe_missingness_skips_columns_safe_to_impute() -> None:
    """A null-containing column marked safe to impute is not flagged."""
    df = pd.DataFrame({"age": [25, None, 30, 40]})
    missingness = MissingnessReport(
        dataset_mcar_conclusion="likely MCAR",
        columns_analyzed=[
            ColumnMissingness(
                column="age",
                null_count=1,
                null_pct=25.0,
                mechanism="MCAR",
                confidence="high",
                evidence="no pattern found",
                safe_to_impute=True,
            )
        ],
        summary="one safe column",
    )
    profile = _profile([_column_profile("age", "age")], missingness)
    assert check_unsafe_missingness(df, profile) == []


def test_check_duplicate_ids_detects_duplicate_values() -> None:
    """A column inferred as an id with a repeated non-null value is flagged."""
    df = pd.DataFrame({"patient_id": ["p1", "p2", "p2", "p3"]})
    profile = _profile([_column_profile("patient_id", "id")])
    evidence = check_duplicate_ids(df, profile)
    assert len(evidence) == 1
    assert "patient_id" in evidence[0]


def test_check_duplicate_ids_ignores_non_id_columns() -> None:
    """A repeated value in a non-id column is not flagged."""
    df = pd.DataFrame({"category": ["a", "a", "b", "c"]})
    profile = _profile([_column_profile("category", "categorical")])
    assert check_duplicate_ids(df, profile) == []


def test_check_negative_numeric_values_detects_negative_ages() -> None:
    """A column inferred as age with a negative value is flagged."""
    df = pd.DataFrame({"age": [25, -5, 30, 40]})
    profile = _profile([_column_profile("age", "age")])
    evidence = check_negative_numeric_values(df, profile)
    assert len(evidence) == 1
    assert "age" in evidence[0]


def test_check_negative_numeric_values_ignores_non_numeric_semantic_types() -> None:
    """Negative-looking values in a non-numeric-semantic column are not flagged."""
    df = pd.DataFrame({"notes": ["-5 apples", "fine", "ok", "-1 issue"]})
    profile = _profile([_column_profile("notes", "text")])
    assert check_negative_numeric_values(df, profile) == []


def test_check_malformed_emails_detects_bad_format() -> None:
    """A column inferred as email with a value missing an '@' is flagged."""
    df = pd.DataFrame({"email": ["a@x.com", "not-an-email", "b@x.com"]})
    profile = _profile([_column_profile("email", "email")])
    evidence = check_malformed_emails(df, profile)
    assert len(evidence) == 1
    assert "email" in evidence[0]


def test_check_malformed_emails_passes_when_all_valid() -> None:
    """A column of well-formed emails produces no evidence."""
    df = pd.DataFrame({"email": ["a@x.com", "b@y.com"]})
    profile = _profile([_column_profile("email", "email")])
    assert check_malformed_emails(df, profile) == []
