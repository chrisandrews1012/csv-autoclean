import sys
from pathlib import Path

import pandas as pd

from csv_autoclean.agents.profiler import run_profiler
from csv_autoclean.agents.repairer import run_repairer
from csv_autoclean.agents.validator import run_validator
from csv_autoclean.models import PipelineContext

USAGE = "Usage: python -m csv_autoclean.pipeline <input_csv>"


def compute_output_path(input_path: str) -> str:
    dataset_name = Path(input_path).stem
    return str(Path("data/processed") / f"{dataset_name}_clean.csv")


def run_pipeline(input_path: str) -> PipelineContext:
    dataset_name = Path(input_path).stem
    df = pd.read_csv(input_path)

    profile = run_profiler(input_path)
    validation = run_validator(profile)

    output_path = compute_output_path(input_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    repair = run_repairer(dataset_name, df, profile, validation, output_path)

    return PipelineContext(
        input_path=input_path,
        output_path=output_path,
        profile=profile,
        validation=validation,
        repair=repair,
    )


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        raise SystemExit(1)

    context = run_pipeline(args[0])
    print(context.profile.summary)
    print(context.validation.summary)
    print(context.repair.summary)
    print(f"Repaired dataset written to {context.output_path}")


if __name__ == "__main__":
    main()
