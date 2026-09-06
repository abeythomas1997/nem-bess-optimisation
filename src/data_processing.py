from pathlib import Path
import csv
import pandas as pd


RAW_FILE = Path(
    "data/raw/PUBLIC_ARCHIVE#DISPATCHPRICE#FILE01#202507010000.CSV"
)

PROCESSED_FILE = Path(
    "data/processed/vic_spot_prices_2025_07.csv"
)


def load_aemo_dispatch_prices(file_path: Path) -> pd.DataFrame:
    rows = []
    columns = None

    with open(file_path, "r", newline="") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            if row[0] == "I" and row[1] == "DISPATCH" and row[2] == "PRICE":
                columns = row[4:]

            elif row[0] == "D" and row[1] == "DISPATCH" and row[2] == "PRICE":
                rows.append(row[4:])

    df = pd.DataFrame(rows, columns=columns)

    return df


def prepare_vic_prices(df: pd.DataFrame) -> pd.DataFrame:
    df = df[["SETTLEMENTDATE", "REGIONID", "RRP"]].copy()

    df = df[df["REGIONID"] == "VIC1"].copy()

    df["SETTLEMENTDATE"] = pd.to_datetime(df["SETTLEMENTDATE"])
    df["RRP"] = pd.to_numeric(df["RRP"])

    df = df.sort_values("SETTLEMENTDATE").reset_index(drop=True)

    return df

def main():
    df_raw = load_aemo_dispatch_prices(RAW_FILE)

    df_vic = prepare_vic_prices(df_raw)

    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)

    df_vic.to_csv(PROCESSED_FILE, index=False)

    print(f"Saved {len(df_vic)} rows to {PROCESSED_FILE}")


if __name__ == "__main__":
    main()