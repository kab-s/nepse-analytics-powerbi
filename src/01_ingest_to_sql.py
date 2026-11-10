"""Module 01: Ingestion Engine for NEPSE Historical & Daily CSVs.

Handles both legacy bulk formats (oct27.csv) and official NEPSE daily exports
with unquoted comma repair in security names.
"""

from datetime import datetime
import glob
import io
import os
import re
import sqlite3
import pandas as pd

DB_PATH = "nepse.db"
DATA_DIR = "data"
DDL_PATH = os.path.join("sql", "01_schema_ddl.sql")
VIEWS_PATH = os.path.join("sql", "02_views_powerbi.sql")


def initialize_database():
    """Applies the SQL schema DDL to create tables and indexes."""
    conn = sqlite3.connect(DB_PATH)
    with open(DDL_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def clean_numeric(series: pd.Series) -> pd.Series:
    """Strips commas and whitespace, casting safely to float."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace(["", "None", "nan", "-"], "0")
        .astype(float)
    )


def load_csv_safely(file_path: str) -> pd.DataFrame:
    """Reads CSVs with automatic reconstruction of unquoted commas in company names."""
    try:
        # Standard fast load
        return pd.read_csv(file_path, low_memory=False)
    except Exception:
        # Fallback line-by-line repair for NEPSE daily exports
        cleaned_lines = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            header_line = f.readline().strip()
            headers = [h.strip() for h in header_line.split(",")]
            expected_cols = len(headers)
            cleaned_lines.append(headers)

            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) == expected_cols:
                    cleaned_lines.append(parts)
                elif len(parts) > expected_cols and expected_cols == 19:
                    # 4 leading fields (Id, Business Date, Security Id, Symbol)
                    # 14 trailing fields (Open..Market Capitalization)
                    # Everything in between is the comma-split Security Name
                    leading = parts[:4]
                    trailing = parts[-14:]
                    repaired_name = " ".join(parts[4:-14]).replace('"', "")
                    cleaned_lines.append(leading + [repaired_name] + trailing)
                else:
                    # Generic fallback: slice excess into the 5th field
                    overflow = len(parts) - expected_cols
                    leading = parts[:4]
                    repaired_name = " ".join(parts[4 : 5 + overflow]).replace('"', "")
                    trailing = parts[5 + overflow :]
                    cleaned_lines.append(leading + [repaired_name] + trailing)

        return pd.DataFrame(cleaned_lines[1:], columns=cleaned_lines[0])


def normalize_dataframe(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Normalizes both CSV structures into standard fact table fields."""
    clean_cols = {c: re.sub(r"[\s_]+", "", str(c)).lower() for c in df.columns}
    df = df.rename(columns=clean_cols)

    target_map = {
        "trade_date": ["businessdate", "date"],
        "symbol": ["symbol"],
        "security_name": ["securityname"],
        "open_price": ["openprice", "open"],
        "high_price": ["highprice", "high"],
        "low_price": ["lowprice", "low"],
        "close_price": ["closeprice", "close"],
        "volume": ["totaltradedquantity", "quantity", "volume", "totalqty"],
        "turnover": ["totaltradedvalue", "turnover", "totalvalue"],
        "transactions": ["totaltrades", "trades", "transactions"],
    }

    norm_df = pd.DataFrame()
    for target_col, aliases in target_map.items():
        matched = next((a for a in aliases if a in df.columns), None)
        if matched is not None:
            norm_df[target_col] = df[matched]
        else:
            raise KeyError(
                f"Missing field '{target_col}' in {source_file}. Present: {list(df.columns)}"
            )

    norm_df["trade_date"] = pd.to_datetime(norm_df["trade_date"]).dt.strftime(
        "%Y-%m-%d"
    )
    norm_df["symbol"] = norm_df["symbol"].astype(str).str.strip().str.upper()
    norm_df["security_name"] = norm_df["security_name"].astype(str).str.strip()

    for col in ["open_price", "high_price", "low_price", "close_price"]:
        norm_df[col] = clean_numeric(norm_df[col])

    norm_df["volume"] = clean_numeric(norm_df["volume"]).astype(int)
    norm_df["turnover"] = clean_numeric(norm_df["turnover"])
    norm_df["transactions"] = clean_numeric(norm_df["transactions"]).astype(int)

    valid_mask = (norm_df["close_price"] > 0) & (norm_df["symbol"] != "")
    return norm_df[valid_mask].copy()


def ingest_all():
    initialize_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not all_files:
        print(f"[ERROR] No CSV files found in '{DATA_DIR}/'.")
        return

    bulk_files = [
        f for f in all_files 
        if any(b in os.path.basename(f).lower() for b in ["oct27", "2026"])
    ]
    daily_files = [
        f for f in all_files 
        if not any(b in os.path.basename(f).lower() for b in ["oct27", "2026", "paper_trades"])
    ]
    file_queue = bulk_files + sorted(daily_files)

    print(f"[INFO] Ingesting {len(file_queue)} file(s): {[os.path.basename(f) for f in file_queue]}")

    total_rows = 0
    companies = {}
    dates = set()

    for file_path in file_queue:
        filename = os.path.basename(file_path)
        print(f"--> Ingesting {filename}...")

        try:
            raw_df = load_csv_safely(file_path)
            clean_df = normalize_dataframe(raw_df, filename)

            for _, row in (
                clean_df[["symbol", "security_name"]].drop_duplicates().iterrows()
            ):
                companies[row["symbol"]] = row["security_name"]

            dates.update(clean_df["trade_date"].unique().tolist())

            fact_rows = clean_df[
                [
                    "trade_date",
                    "symbol",
                    "open_price",
                    "high_price",
                    "low_price",
                    "close_price",
                    "volume",
                    "turnover",
                    "transactions",
                ]
            ].values.tolist()

            cursor.executemany(
                """
                INSERT INTO fact_daily_ohlcv (
                    trade_date, symbol, open_price, high_price, low_price,
                    close_price, volume, turnover, transactions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trade_date, symbol) DO UPDATE SET
                    open_price = excluded.open_price,
                    high_price = excluded.high_price,
                    low_price = excluded.low_price,
                    close_price = excluded.close_price,
                    volume = excluded.volume,
                    turnover = excluded.turnover,
                    transactions = excluded.transactions;
            """,
                fact_rows,
            )

            conn.commit()
            print(f"    Loaded {len(fact_rows):,} rows.")
            total_rows += len(fact_rows)

        except Exception as e:
            print(f"    [FAIL] Could not load {filename}: {e}")

    # Synchronize dim_company
    print(f"\n[SYNC] Updating dim_company ({len(companies)} securities)...")
    comp_rows = [(sym, name) for sym, name in companies.items()]
    cursor.executemany(
        """
        INSERT INTO dim_company (symbol, company_name)
        VALUES (?, ?)
        ON CONFLICT(symbol) DO UPDATE SET
            company_name = excluded.company_name;
    """,
        comp_rows,
    )

    # Synchronize dim_calendar
    print(f"[SYNC] Updating dim_calendar ({len(dates)} trading days)...")
    cal_rows = []
    for dt_str in dates:
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        cal_rows.append(
            (dt_str, dt.year, (dt.month - 1) // 3 + 1, dt.month, dt.strftime("%A"), 1)
        )

    cursor.executemany(
        """
        INSERT INTO dim_calendar (trade_date, year, quarter, month, day_name, is_trading_day)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(trade_date) DO NOTHING;
    """,
        cal_rows,
    )

    conn.commit()

    # Re-compile analytical views
    if os.path.exists(VIEWS_PATH):
        print("\n[VIEWS] Compiling analytical views from 02_views_powerbi.sql...")
        with open(VIEWS_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        conn.commit()

    conn.close()

    print("\n" + "=" * 55)
    print("INGESTION COMPLETE:")
    print(f" - Fact OHLCV Rows Loaded : {total_rows:,}")
    print(f" - Distinct Securities    : {len(companies):,}")
    print(f" - Distinct Trading Days  : {len(dates):,}")
    print("=" * 55)


if __name__ == "__main__":
    ingest_all()