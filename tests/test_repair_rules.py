import pandas as pd

from csv_autoclean.models import (
    ColumnMissingness,
    ColumnProfile,
    DataProfile,
    MissingnessReport,
)
from csv_autoclean.repair_rules import (
    compute_repair_candidates,
    drop_duplicate_rows,
    impute_column_mean,
    impute_column_median,
    impute_column_mode,
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
    columns: list[ColumnProfile], missingness: MissingnessReport | None
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


def _missingness(
    column: str, null_count: int, safe_to_impute: bool
) -> MissingnessReport:
    return MissingnessReport(
        dataset_mcar_conclusion="test",
        columns_analyzed=[
            ColumnMissingness(
                column=column,
                null_count=null_count,
                null_pct=0.0,
                mechanism="MCAR",
                confidence="high",
                evidence="test evidence",
                safe_to_impute=safe_to_impute,
            )
        ],
        summary="test missingness",
    )


def test_impute_column_mean_fills_nulls_with_column_mean() -> None:
    """Nulls in a numeric column are replaced with the column's own mean."""
    df = pd.DataFrame({"age": [10.0, 20.0, None, 30.0]})
    filled = impute_column_mean(df, "age")
    assert filled.isna().sum() == 0
    assert filled.iloc[2] == 20.0


def test_impute_column_median_fills_nulls_with_column_median() -> None:
    """Nulls in a numeric column are replaced with the column's own median."""
    df = pd.DataFrame({"age": [10.0, 20.0, None, 100.0]})
    filled = impute_column_median(df, "age")
    assert filled.isna().sum() == 0
    assert filled.iloc[2] == 20.0


def test_impute_column_mode_fills_nulls_with_most_frequent_value() -> None:
    """Nulls in a column are replaced with the column's most frequent value."""
    df = pd.DataFrame({"category": ["a", "a", "b", None]})
    filled = impute_column_mode(df, "category")
    assert filled.isna().sum() == 0
    assert filled.iloc[3] == "a"


def test_drop_duplicate_rows_keeps_first_occurrence() -> None:
    """Exact duplicate rows are dropped, keeping the first occurrence."""
    df = pd.DataFrame({"id": ["p1", "p2", "p1"], "value": [1, 2, 1]})
    result = drop_duplicate_rows(df)
    assert len(result) == 2
    assert list(result["id"]) == ["p1", "p2"]


def test_drop_duplicate_rows_respects_subset() -> None:
    """With a subset, rows duplicated only on that subset are dropped even
    if other columns differ."""
    df = pd.DataFrame({"id": ["p1", "p2", "p1"], "value": [1, 2, 999]})
    result = drop_duplicate_rows(df, subset=["id"])
    assert len(result) == 2
    assert list(result["id"]) == ["p1", "p2"]


def test_compute_repair_candidates_reports_mean_and_median_for_numeric_column() -> None:
    """A numeric-semantic column with nulls gets mean and median evidence."""
    df = pd.DataFrame({"age": [10.0, 20.0, None, 30.0]})
    missingness = _missingness("age", null_count=1, safe_to_impute=True)
    profile = _profile([_column_profile("age", "age")], missingness)
    evidence = compute_repair_candidates(df, profile)
    assert len(evidence) == 1
    assert "age" in evidence[0]
    assert "mean" in evidence[0]
    assert "median" in evidence[0]


def test_compute_repair_candidates_reports_mode_for_categorical_column() -> None:
    """A non-numeric-semantic column with nulls gets mode evidence."""
    df = pd.DataFrame({"category": ["a", "a", "b", None]})
    missingness = _missingness("category", null_count=1, safe_to_impute=True)
    profile = _profile([_column_profile("category", "categorical")], missingness)
    evidence = compute_repair_candidates(df, profile)
    assert len(evidence) == 1
    assert "category" in evidence[0]
    assert "mode" in evidence[0]


def test_compute_repair_candidates_skips_columns_without_nulls() -> None:
    """A column with zero nulls produces no repair-candidate evidence."""
    df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
    missingness = _missingness("age", null_count=0, safe_to_impute=True)
    profile = _profile([_column_profile("age", "age")], missingness)
    assert compute_repair_candidates(df, profile) == []


def test_compute_repair_candidates_returns_empty_when_no_missingness_report() -> None:
    """A profile with no missingness report at all produces no evidence."""
    df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
    profile = _profile([_column_profile("age", "age")], None)
    assert compute_repair_candidates(df, profile) == []
