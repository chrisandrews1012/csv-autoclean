import pandas as pd

from csv_autoclean.models import DataProfile

_NUMERIC_SEMANTIC_TYPES = {"age", "currency", "numeric"}


def impute_column_mean(df: pd.DataFrame, column: str) -> pd.Series:
    numeric = pd.to_numeric(df[column], errors="coerce")
    return numeric.fillna(numeric.mean())


def impute_column_median(df: pd.DataFrame, column: str) -> pd.Series:
    numeric = pd.to_numeric(df[column], errors="coerce")
    return numeric.fillna(numeric.median())


def impute_column_mode(df: pd.DataFrame, column: str) -> pd.Series:
    modes = df[column].mode(dropna=True)
    fill_value = modes.iloc[0] if not modes.empty else None
    return df[column].fillna(fill_value)


def drop_duplicate_rows(
    df: pd.DataFrame, subset: list[str] | None = None
) -> pd.DataFrame:
    return df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)


def compute_repair_candidates(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    if profile.missingness is None:
        return []

    column_types = {column.name: column.inferred_type for column in profile.columns}
    evidence = []
    for column in profile.missingness.columns_analyzed:
        if column.null_count == 0:
            continue

        inferred_type = column_types.get(column.column, "unknown")
        series = df[column.column]

        if inferred_type in _NUMERIC_SEMANTIC_TYPES:
            numeric = pd.to_numeric(series, errors="coerce")
            mean = round(float(numeric.mean()), 2)
            median = round(float(numeric.median()), 2)
            evidence.append(
                f"'{column.column}' ({inferred_type}): mean={mean}, "
                f"median={median} (computed excluding nulls)."
            )
        else:
            modes = series.mode(dropna=True)
            mode_value = modes.iloc[0] if not modes.empty else None
            evidence.append(
                f"'{column.column}' ({inferred_type}): most frequent value "
                f"(mode) = {mode_value!r} (computed excluding nulls)."
            )

    return evidence
