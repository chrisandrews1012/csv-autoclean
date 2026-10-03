# Evals

## What a golden dataset is

A golden dataset is a dataset whose correct answers are already known before the system is ever run against it. Here, that means the four synthetic CSVs in `data/raw/` aren't just test inputs, they're inputs paired with a ground-truth spec (`evals/expected/*.json`) stating exactly what a correct run should conclude: how many duplicate rows exist, what semantic type each column actually is, which columns have a genuine data-quality issue that must be fixed, and which column (if any) has missingness that must never be auto-imputed. Because the data was generated rather than collected, every one of those facts is known with certainty, not estimated.

## Why this is a vital piece of the project

Every other layer in this pipeline (Pydantic, invariants) can confirm an agent's output is well-formed and internally consistent with the data it was given. Neither one can confirm the agent reached the *right* conclusion. A `DataProfile` can have a perfectly accurate row count and still infer that a currency column is `categorical`. That's not a structural error or a factual contradiction; it's a wrong judgment call, and nothing before this layer is positioned to catch it.

A golden dataset is what makes that judgment checkable at all. Against a real-world CSV, there's no independent answer key to grade the Profiler's semantic-type calls or the Validator's severity decisions against, so a wrong judgment would simply look like a plausible one. Against a dataset you built yourself and know completely, "plausible" and "correct" are either the same thing or they aren't, and you can tell which.

This is what makes the eval harness (`evals/runner.py`) the third layer of the pipeline's trust strategy: Pydantic validates shape, invariants validate that claims match the data, evals validate that the judgment calls themselves are correct.

## What gets scored

Running `make eval` executes the pipeline against all four datasets and checks six things per dataset:

| Check | What it verifies |
|---|---|
| Factual accuracy | Row/duplicate/null counts match the known ground truth |
| Semantic type accuracy | Each column's inferred type matches what the dataset was actually built as |
| Repair coverage | Every known issue in the dataset was actually repaired |
| Unresolved coverage | Issues that should never be auto-repaired (e.g. a malformed email) were correctly escalated instead |
| MNAR safety | A column known to have systematic missingness was never imputed |
| No false positives | A dataset with zero injected issues received zero repairs |

A scorecard summarizing all four datasets is written to `evals/results/scorecard.md` after each run, so a change to a prompt or a model can be checked for regressions before it ships, the same way a test suite protects conventional code.
