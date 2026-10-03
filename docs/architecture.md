# Architecture

## Why four agents instead of one prompt

A single prompt asked to "clean this CSV" conflates three different kinds of work: arithmetic (null counts, row counts), statistical inference (is this missingness random or systematic), and judgment calls with real consequences (is this repair safe to apply automatically). Treating all three the same way removes any seam to verify the result, and gives a repair mistake, which corrupts data in place, the same trust level as a profiling mistake, which doesn't.

The pipeline is split the way a human team would split it: a Profiler who understands the data, a Validator who checks it against rules, a Repairer who fixes what's safe to fix, and a Reporter who writes it up. Each stage returns a typed Pydantic model, so the contract between stages is enforced by the type system, and each handoff is a place to verify work before it propagates.

## Deterministic code computes; the model judges

Every agent follows the same rule: anything with one correct answer is computed in Python; anything requiring judgment goes to Claude. A model asked to compute a null percentage from a table it was shown can get it wrong; `len(df)` can't. So every statistic, format check, and repair operation is ordinary code, and the model only reasons over facts it's handed, never recomputes them.

- **Profiler**: Python computes every statistic and runs a real Little's MCAR test to classify missingness (random vs. systematic). The model's only job is semantic type inference, deciding a column named `dept` with values like `Engineering`/`engineering` is `categorical`, which doesn't reduce to a fixed rule table across arbitrary schemas.
- **Validator**: Receives only the Profiler's output, no raw data. Entirely judgment: given a column's semantic type, which rules apply and how severe is a violation. This is what lets the same code validate an HR dataset and a medical dataset with no schema-specific logic.
- **Repairer**: Inverts the pattern. Python decides and executes every repair, per semantic type, before the model is called; the model only narrates what already happened. This is deliberate: a wrong repair destroys data, so nothing here is left to the model's discretion. Anything unsafe to resolve automatically (a column flagged statistically unsafe to impute, one that's mostly null) is escalated for manual review instead of guessed at.
- **Reporter**: The only agent that sees the full picture (profile, validation, repair together). Pure synthesis, writing a document for both technical and non-technical readers.

See [`statistics-and-repairs.md`](statistics-and-repairs.md) for exactly what each statistical check and repair does.

## Invariants: verifying the model told the truth

Pydantic validates that an agent's output has the right shape, not that it's factually correct. After each of the first three stages, a deterministic check re-derives the same facts from the actual data and compares them against the agent's claims: row counts, column references, a `passed=True` next to a critical failure, a `rows_dropped` that doesn't match the real row delta. Any mismatch raises `InvariantViolation` and halts the run immediately, rather than letting a wrong answer reach the next stage.

## One pipeline, two front ends

The CLI and the web server both call the same `run_pipeline` function. The CLI runs it synchronously with a console UI and logs to `logs/pipeline.log`. The web server schedules it on a background thread per upload and streams the same progress over server-sent events. The orchestration logic lives in exactly one place, so the two front ends can't drift into behaving differently.
