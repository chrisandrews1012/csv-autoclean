from pathlib import Path

import pandas as pd

from data._generators import build_ecommerce_rows, corrupt_ecommerce_rows

OUTPUT_PATH = Path(__file__).parent / "raw" / "ecommerce_messy.csv"


def main() -> None:
    clean_rows = build_ecommerce_rows()
    messy_rows = corrupt_ecommerce_rows(clean_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(messy_rows).to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(messy_rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
