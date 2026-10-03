from pathlib import Path

import pandas as pd

from data._generators import build_medical_rows, corrupt_medical_rows

OUTPUT_PATH = Path(__file__).parent / "raw" / "medical_messy.csv"


def main() -> None:
    clean_rows = build_medical_rows()
    messy_rows = corrupt_medical_rows(clean_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(messy_rows).to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(messy_rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
