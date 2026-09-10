import re

import pandas as pd

from csv_autoclean.models import DataProfile

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_NUMERIC_SEMANTIC_TYPES = {"age", "currency", "numeric"}


def check_unsafe_missingness(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    if profile.missingness is None:
        return []

    evidence = []
    for column in profile.missingness.columns_analyzed:
        if column.null_count > 0 and not column.safe_to_impute:
            evidence.append(
                f"'{column.column}' has {column.null_count} nulls "
                f"({column.null_pct}%) and was flagged not safe to impute "
                f"({column.mechanism}, {column.confidence} confidence): "
                f"do not silently drop or impute these rows."
            )
    return evidence


def check_duplicate_ids(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    evidence = []
    for column in profile.columns:
        if column.inferred_type != "id":
            continue
        duplicate_count = int(df[column.name].dropna().duplicated().sum())
        if duplicate_count > 0:
            evidence.append(
                f"'{column.name}' is inferred as an id column but has "
                f"{duplicate_count} duplicate non-null value(s)."
            )
    return evidence


def check_negative_numeric_values(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    evidence = []
    for column in profile.columns:
        if column.inferred_type not in _NUMERIC_SEMANTIC_TYPES:
            continue
        numeric = pd.to_numeric(df[column.name], errors="coerce")
        negative_count = int((numeric < 0).sum())
        if negative_count > 0:
            evidence.append(
                f"'{column.name}' ({column.inferred_type}) has "
                f"{negative_count} negative value(s), which is implausible "
                f"for this semantic type."
            )
    return evidence


def check_malformed_emails(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    evidence = []
    for column in profile.columns:
        if column.inferred_type != "email":
            continue
        values = df[column.name].dropna().astype(str)
        malformed_count = int((~values.str.match(_EMAIL_PATTERN)).sum())
        if malformed_count > 0:
            evidence.append(
                f"'{column.name}' is inferred as an email column but has "
                f"{malformed_count} value(s) that don't match a basic "
                f"email pattern."
            )
    return evidence


def compute_validation_evidence(df: pd.DataFrame, profile: DataProfile) -> list[str]:
    return [
        *check_unsafe_missingness(df, profile),
        *check_duplicate_ids(df, profile),
        *check_negative_numeric_values(df, profile),
        *check_malformed_emails(df, profile),
    ]
