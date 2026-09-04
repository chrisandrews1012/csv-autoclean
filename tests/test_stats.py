import pandas as pd

from csv_autoclean.stats import (
    compute_column_stats,
    compute_dataset_stats,
    compute_missingness_evidence,
)


def test_compute_column_stats_numeric_column() -> None:
    """Numeric columns get min/max/mean/std alongside the shared stats."""
    series = pd.Series([10, 20, 30, None], name="age")
    stats = compute_column_stats(series)
    assert stats["null_count"] == 1
    assert stats["unique_count"] == 3
    assert stats["mean_value"] == 20.0
    assert stats["min_value"] == "10.0"
    assert stats["max_value"] == "30.0"


def test_compute_column_stats_non_numeric_column() -> None:
    """Non-numeric columns leave min/max/mean/std as None."""
    series = pd.Series(["a", "b", "a", None], name="category")
    stats = compute_column_stats(series)
    assert stats["null_count"] == 1
    assert stats["min_value"] is None
    assert stats["mean_value"] is None
    sample_values = stats["sample_values"]
    assert isinstance(sample_values, list)
    assert set(sample_values) <= {"a", "b"}


def test_compute_dataset_stats() -> None:
    """Dataset stats report row/column counts, duplicates, and total nulls."""
    df = pd.DataFrame(
        {
            "a": [1, 1, 2, None],
            "b": ["x", "x", "y", "z"],
        }
    )
    stats = compute_dataset_stats(df)
    assert stats["row_count"] == 4
    assert stats["column_count"] == 2
    assert stats["duplicate_row_count"] == 1
    assert stats["total_null_count"] == 1


def test_compute_missingness_evidence_detects_categorical_correlation() -> None:
    """A column whose nulls concentrate in one group of another column
    is flagged with that association, not a random-missingness message."""
    df = pd.DataFrame(
        {
            "insurance": ["Aetna"] * 20 + ["Self-Pay"] * 20,
            "diagnosis": ["Flu"] * 20 + [None] * 15 + ["Flu"] * 5,
        }
    )
    evidence = compute_missingness_evidence(df)
    assert "diagnosis" in evidence
    assert "insurance" in evidence["diagnosis"]


def test_compute_missingness_evidence_reports_no_correlation_when_random() -> None:
    """A column with no detectable association gets a plain no-correlation message."""
    groups = ["A", "B", "C", "D"] * 10
    values: list[int | None] = [1] * 40
    for i in range(0, 40, 5):
        values[i] = None
    df = pd.DataFrame({"group": groups, "value": values})
    evidence = compute_missingness_evidence(df)
    assert "value" in evidence
    assert "No strong correlation" in evidence["value"]
