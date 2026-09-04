from pathlib import Path

import pandas as pd

from data._generators import build_hr_rows

OUTPUT_PATH = Path(__file__).parent / "raw" / "hr_clean.csv"


def main() -> None:
    rows = build_hr_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
