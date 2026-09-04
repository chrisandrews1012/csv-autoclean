import pandas as pd
import pytest

from csv_autoclean.agents.profiler import build_profiler_prompt, run_profiler


def test_build_profiler_prompt_includes_ground_truth_stats() -> None:
    """The prompt states the deterministic row/column counts explicitly."""
    df = pd.DataFrame({"age": [25, 30, None], "name": ["Al", "Bo", "Cy"]})
    prompt = build_profiler_prompt("people", df)
    assert "row_count" in prompt
    assert "'row_count': 3" in prompt


def test_build_profiler_prompt_includes_missingness_evidence() -> None:
    """A column with nulls gets its missingness evidence line included."""
    df = pd.DataFrame({"age": [25, 30, None], "name": ["Al", "Bo", "Cy"]})
    prompt = build_profiler_prompt("people", df)
    assert "Missingness evidence" in prompt
    assert "age" in prompt


def test_build_profiler_prompt_omits_missingness_section_when_no_nulls() -> None:
    """A dataset with no nulls at all skips the missingness evidence section."""
    df = pd.DataFrame({"age": [25, 30, 35], "name": ["Al", "Bo", "Cy"]})
    prompt = build_profiler_prompt("people", df)
    assert "Missingness evidence" not in prompt


@pytest.mark.llm
def test_run_profiler_produces_a_valid_data_profile() -> None:
    """Against a real small dataset, the agent's output matches the schema
    and its restated numbers agree with ground truth."""
    df = pd.DataFrame(
        {
            "age": [25, 30, None, 45],
            "email": ["a@x.com", "b@x.com", "c@x.com", None],
        }
    )
    profile = run_profiler("people", df)
    assert profile.row_count == 4
    assert profile.column_count == 2
    assert {c.name for c in profile.columns} == {"age", "email"}
    assert profile.missingness is not None
