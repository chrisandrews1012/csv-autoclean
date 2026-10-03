# Statistical Checks and Repairs

This document is the technical reference for the Profiler's missingness
classification, the Validator's per-type rules, and the Repairer's
per-type fixes. See [`architecture.md`](architecture.md) for why the
pipeline is structured this way; this covers exactly what each check and
repair does.

## Missingness classification

For every column with at least one null value, the Profiler tests
whether the gaps correlate with another numeric column, using a
point-biserial correlation between the column's missingness indicator
(1 if null, 0 otherwise) and each numeric column's values:

- **MAR** (missing at random, conditional on an observed column): a
  correlation with p < 0.05 and |r| > 0.1 against at least one numeric
  column. Safe to impute, and imputation is more accurate if it
  conditions on the correlated column.
- **MNAR** (missing not at random): no such correlation found, and the
  column is more than 20% null. The gap may depend on the value itself
  (e.g. a sensitive field under-reported for certain respondents), so
  imputation would introduce systematic bias. **Not safe to impute.**
- **MCAR** (missing completely at random): no correlation found, and
  the null rate is 20% or below. Safe to impute.

Independently, the Profiler also runs a dataset-level Little's MCAR
test: a chi-square statistic comparing each missingness-pattern group's
column means against the dataset's overall means. A low p-value (≤0.05)
rejects the null hypothesis that missingness is completely random across
the whole dataset, even if no single column shows a strong pairwise
correlation.

The per-column `safe_to_impute` flag this produces is what the Repairer
checks before touching any column: an MNAR classification is a hard stop
on automatic repair, regardless of semantic type.

## Validation rules by semantic type

The Validator applies one of the following rule sets per column, based
on the Profiler's inferred semantic type:

| Type | Rule |
|---|---|
| `id` | Zero nulls expected; uniqueness should be ~100% |
| `email` | Zero nulls expected; all non-null values must match email format |
| `phone` | Flag high null rates; check formatting consistency |
| `age` | Must be numeric; flag values outside 0-120 |
| `date` | Flag inconsistent formats; all values should be parseable |
| `currency` | Must be numeric; flag currency symbols or commas |
| `categorical` | Flag high null rates; flag inconsistent casing; note low cardinality |
| `numeric` | Flag outliers beyond 3 standard deviations; flag high null rates |
| `boolean` | Should contain exactly 2 distinct values; flag nulls |
| `text` | Flag only very high null rates |
| `unknown` | Flag high null rates; no other rules apply |

Duplicate rows are always checked regardless of column types. Every
failure gets a severity: **critical** (data is unusable without fixing
this), **consideration** (worth knowing, data is still usable), or
**info** (minor observation). A column the Profiler classified as MNAR
is always escalated to critical when it has nulls, overriding the
type's normal severity, since imputing it would bias results.

## Repairs by semantic type

Before any per-column repair runs, exact duplicate rows are dropped.
Then, for each remaining column: if it's more than 50% null, or the
Profiler marked it unsafe to impute (MNAR), it's left untouched and
escalated to the unresolved list. Otherwise:

| Type | Repair |
|---|---|
| `currency` | Strip symbols/commas from values containing `$`, `£`, `€`, or `,`; median-impute remaining nulls |
| `age` | Null out values outside 0-120 (likely data entry errors), then median-impute all nulls |
| `email` | Never auto-repaired: nulls and malformed values are both escalated to unresolved |
| `date` | Standardize any value not already in `YYYY-MM-DD` format |
| `categorical` | Title-case values that don't already match their title-cased form; mode-impute nulls |
| `numeric` | Median-impute nulls |
| `id` | Never auto-repaired: null ids are escalated to unresolved, since an id can't be fabricated |
| `boolean` | Mode-impute nulls |

Median imputation is used over mean wherever a column can plausibly be
skewed by outliers (currency, age, numeric); mode imputation is used for
categorical and boolean columns, where a mean is meaningless.
