import pandas as pd


def compute_column_stats(series: pd.Series) -> dict[str, object]:
    non_null = series.dropna()
    stats: dict[str, object] = {
        "dtype": str(series.dtype),
        "null_count": int(series.isna().sum()),
        "null_pct": round(float(series.isna().mean() * 100), 2),
        "unique_count": int(series.nunique()),
        "unique_pct": round(float(series.nunique() / max(len(series), 1) * 100), 2),
        "sample_values": [str(v) for v in non_null.head(5).tolist()],
        "min_value": None,
        "max_value": None,
        "mean_value": None,
        "std_value": None,
    }

    numeric = pd.to_numeric(non_null, errors="coerce").dropna()
    if len(numeric) > 0:
        stats["min_value"] = str(numeric.min())
        stats["max_value"] = str(numeric.max())
        stats["mean_value"] = round(float(numeric.mean()), 2)
        stats["std_value"] = round(float(numeric.std()), 2) if len(numeric) > 1 else 0.0

    return stats


def compute_dataset_stats(df: pd.DataFrame) -> dict[str, int]:
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_row_count": int(df.duplicated().sum()),
        "total_null_count": int(df.isna().sum().sum()),
    }


def compute_missingness_evidence(df: pd.DataFrame) -> dict[str, str]:
    evidence: dict[str, str] = {}
    columns_with_nulls = [column for column in df.columns if df[column].isna().any()]

    for column in columns_with_nulls:
        is_null = df[column].isna()
        best_association: str | None = None
        best_strength = 0.0

        for other in df.columns:
            if other == column or df[other].isna().any():
                continue
            other_series = df[other]

            if pd.api.types.is_numeric_dtype(other_series):
                if is_null.nunique() < 2:
                    continue
                correlation = other_series.astype(float).corr(is_null.astype(float))
                if pd.notna(correlation) and abs(correlation) > best_strength:
                    best_strength = abs(correlation)
                    best_association = (
                        f"correlates with '{other}' (r={correlation:.2f})"
                    )
            else:
                rates = df.groupby(other)[column].apply(lambda s: s.isna().mean())
                if len(rates) < 2:
                    continue
                spread = float(rates.max() - rates.min())
                if spread > best_strength:
                    best_strength = spread
                    top_group = rates.idxmax()
                    best_association = (
                        f"is higher when '{other}' = '{top_group}' "
                        f"({rates.max():.0%} vs {rates.min():.0%} elsewhere)"
                    )

        if best_association and best_strength > 0.3:
            evidence[column] = f"Missingness in '{column}' {best_association}."
        else:
            evidence[column] = (
                f"No strong correlation found between missingness in "
                f"'{column}' and other observed columns."
            )

    return evidence
