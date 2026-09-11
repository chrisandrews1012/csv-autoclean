from pathlib import Path

import pandas as pd
import pytest

from csv_autoclean.pipeline import compute_output_path, main, run_pipeline


def test_compute_output_path_derives_from_input_stem() -> None:
    """The output path lives under data/processed, named after the input stem."""
    result = compute_output_path("data/raw/hr_messy.csv")
    assert result == "data/processed/hr_messy_clean.csv"


def test_compute_output_path_ignores_input_directory() -> None:
    """Only the input filename's stem matters, not its directory."""
    result = compute_output_path("/tmp/whatever/ecommerce.csv")
    assert result == "data/processed/ecommerce_clean.csv"


def test_main_with_no_arguments_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running with no input path prints usage to stderr and exits non-zero."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0
    assert "Usage" in capsys.readouterr().err


def test_main_with_too_many_arguments_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running with more than one input path prints usage and exits non-zero."""
    with pytest.raises(SystemExit) as exc_info:
        main(["a.csv", "b.csv"])
    assert exc_info.value.code != 0
    assert "Usage" in capsys.readouterr().err


@pytest.mark.llm
def test_run_pipeline_produces_a_full_context(tmp_path: Path) -> None:
    """Against a small synthetic dataset, the pipeline runs all three
    stages and writes the repaired CSV to the computed output path."""
    input_path = str(tmp_path / "hr_messy.csv")
    df = pd.DataFrame(
        {
            "employee_id": ["e1", "e2", "e2", "e3"],
            "age": [25, 30, 30, None],
            "email": ["a@x.com", "b@x.com", "b@x.com", "not-an-email"],
        }
    )
    df.to_csv(input_path, index=False)

    context = run_pipeline(input_path)
    output_path = Path(context.output_path)

    try:
        assert context.input_path == input_path
        assert context.profile.dataset_name == "hr_messy"
        assert context.validation.failure_count == len(context.validation.failures)
        assert context.repair.total_repairs == len(context.repair.actions)

        repaired = pd.read_csv(output_path)
        assert len(repaired) <= len(df)
    finally:
        output_path.unlink(missing_ok=True)
