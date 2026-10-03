from data._generators import (
    HR_COLUMNS,
    SENSITIVE_DIAGNOSES,
    build_ecommerce_rows,
    build_hr_rows,
    build_medical_rows,
    corrupt_hr_rows,
    corrupt_medical_rows,
)


def test_build_hr_rows_has_expected_shape() -> None:
    """build_hr_rows returns the requested row count with the HR schema."""
    rows = build_hr_rows(n=50, seed=1)
    assert len(rows) == 50
    assert set(rows[0].keys()) == set(HR_COLUMNS)


def test_build_hr_rows_is_reproducible_with_fixed_seed() -> None:
    """The same seed produces byte-identical rows across separate calls."""
    first = build_hr_rows(n=50, seed=1)
    second = build_hr_rows(n=50, seed=1)
    assert first == second


def test_clean_hr_rows_have_no_nulls_or_duplicates() -> None:
    """Uncorrupted rows (used for hr_clean.csv) contain no nulls or exact duplicates."""
    rows = build_hr_rows(n=200, seed=1)
    assert not any(value is None for row in rows for value in row.values())
    seen = {tuple(row.items()) for row in rows}
    assert len(seen) == len(rows)


def test_corrupt_hr_rows_introduces_duplicates() -> None:
    """corrupt_hr_rows appends rows that are exact matches of another row."""
    clean = build_hr_rows(n=200, seed=1)
    messy = corrupt_hr_rows(clean, seed=1)
    assert len(messy) > len(clean)

    seen = [tuple(row.items()) for row in messy]
    exact_duplicate_count = len(seen) - len(set(seen))
    assert exact_duplicate_count == len(messy) - len(clean)


def test_corrupt_hr_rows_introduces_nulls() -> None:
    """corrupt_hr_rows nulls out some salary and email values."""
    clean = build_hr_rows(n=200, seed=1)
    messy = corrupt_hr_rows(clean, seed=1)
    assert any(row["salary"] is None for row in messy)
    assert any(row["email"] is None for row in messy)


def test_corrupt_hr_rows_introduces_currency_formatting() -> None:
    """corrupt_hr_rows reformats some salary values as currency strings."""
    clean = build_hr_rows(n=200, seed=1)
    messy = corrupt_hr_rows(clean, seed=1)
    assert any(
        isinstance(row["salary"], str) and str(row["salary"]).startswith("$")
        for row in messy
    )


def test_corrupt_hr_rows_introduces_mixed_casing() -> None:
    """corrupt_hr_rows changes the casing of some department values."""
    clean = build_hr_rows(n=200, seed=1)
    messy = corrupt_hr_rows(clean, seed=1)
    departments = {str(row["department"]) for row in messy}
    assert len(departments) > len({str(row["department"]) for row in clean})


def test_build_ecommerce_rows_schema_differs_from_hr() -> None:
    """The ecommerce schema uses different column names than HR."""
    rows = build_ecommerce_rows(n=20, seed=1)
    assert set(rows[0].keys()).isdisjoint(HR_COLUMNS)


def test_corrupt_medical_rows_missingness_is_mnar_not_random() -> None:
    """Diagnosis nulls concentrate on sensitive diagnoses, not a random subset."""
    clean = build_medical_rows(n=300, seed=1)
    messy = corrupt_medical_rows(clean, seed=1)

    sensitive_total = 0
    sensitive_null = 0
    other_total = 0
    other_null = 0
    for clean_row, messy_row in zip(clean, messy, strict=True):
        if clean_row["diagnosis"] in SENSITIVE_DIAGNOSES:
            sensitive_total += 1
            sensitive_null += messy_row["diagnosis"] is None
        else:
            other_total += 1
            other_null += messy_row["diagnosis"] is None

    assert sensitive_total > 0
    assert other_total > 0
    sensitive_null_rate = sensitive_null / sensitive_total
    other_null_rate = other_null / other_total
    assert sensitive_null_rate > other_null_rate
