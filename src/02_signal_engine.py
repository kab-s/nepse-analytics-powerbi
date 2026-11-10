"""
Module 02: Vectorized Technical Indicator & Candlestick Signal Engine
Calculates moving averages, RSI, MACD, Bollinger Bands, and candlestick
patterns across all securities and writes to fact_technical_signals.
"""

import os
import sqlite3
import time
import numpy as np
import pandas as pd

DB_PATH = "nepse.db"


def calculate_indicators_for_group(df: pd.DataFrame) -> pd.DataFrame:
    """Computes technical indicators and candlestick patterns for a single symbol."""
    # Ensure chronological order
    df = df.sort_values("trade_date").copy()

    c = df["close_price"]
    o = df["open_price"]
    h = df["high_price"]
    l = df["low_price"]
    v = df["volume"]

    # 1. Moving Averages
    df["sma_20"] = c.rolling(window=20, min_periods=5).mean().round(2)
    df["sma_50"] = c.rolling(window=50, min_periods=10).mean().round(2)

    # 2. Bollinger Bands (20, 2.0)
    rolling_std = c.rolling(window=20, min_periods=5).std()
    df["bb_upper"] = (df["sma_20"] + (rolling_std * 2.0)).round(2)
    df["bb_lower"] = (df["sma_20"] - (rolling_std * 2.0)).round(2)

    # 3. MACD (12, 26, 9)
    ema_12 = c.ewm(span=12, adjust=False).mean()
    ema_26 = c.ewm(span=26, adjust=False).mean()
    df["macd_line"] = (ema_12 - ema_26).round(2)
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean().round(2)
    df["macd_hist"] = (df["macd_line"] - df["macd_signal"]).round(2)

    # 4. Wilder's RSI (14)
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = (100 - (100 / (1 + rs))).fillna(50.0).round(2)

    # 5. Candlestick Geometry
    body = (c - o).abs()
    candle_range = (h - l).replace(0, np.nan)
    upper_shadow = h - np.maximum(o, c)
    lower_shadow = np.minimum(o, c) - l

    # Prior day shifts
    c_prev = c.shift(1)
    o_prev = o.shift(1)
    b_prev = body.shift(1)
    ret_5d = c.pct_change(5)

    # Pattern Conditions
    # Bullish Hammer: Prior pullback, small body, lower shadow >= 2x body, tiny upper shadow
    bull_hammer = (
        (ret_5d < -0.02)
        & (lower_shadow >= 2.0 * body)
        & (upper_shadow <= 0.25 * body)
        & ((body / candle_range) >= 0.10)
    )

    # Shooting Star (Bearish): Prior rally, small body, upper shadow >= 2x body
    shooting_star = (
        (ret_5d > 0.02)
        & (upper_shadow >= 2.0 * body)
        & (lower_shadow <= 0.25 * body)
        & ((body / candle_range) >= 0.10)
    )

    # Bullish Engulfing: Prior day red, current green body completely engulfs prior body
    bull_engulf = (
        (ret_5d < -0.01)
        & (c_prev < o_prev)
        & (c > o)
        & (o <= c_prev)
        & (c >= o_prev)
        & (body > 1.05 * b_prev)
    )

    # Bearish Engulfing: Prior day green, current red body completely engulfs prior body
    bear_engulf = (
        (ret_5d > 0.01)
        & (c_prev > o_prev)
        & (c < o)
        & (o >= c_prev)
        & (c <= o_prev)
        & (body > 1.05 * b_prev)
    )

    patterns = [bull_engulf, bull_hammer, bear_engulf, shooting_star]
    pattern_labels = [
        "Bullish Engulfing",
        "Bullish Hammer",
        "Bearish Engulfing",
        "Shooting Star",
    ]
    df["candle_pattern"] = np.select(patterns, pattern_labels, default="None")

    # 6. Quantitative Signal Decision Logic
    # BUY: Bullish candle pattern OR (RSI oversold < 38 and bouncing above SMA_20)
    # SELL: Bearish candle pattern OR (RSI overbought > 72 and dropping below SMA_20)
    buy_rule = (
        (df["candle_pattern"].isin(["Bullish Engulfing", "Bullish Hammer"]))
        | ((df["rsi_14"] < 40) & (c > df["sma_20"]))
        | ((df["macd_hist"] > 0) & (df["macd_hist"].shift(1) <= 0) & (c > df["sma_50"]))
    )

    sell_rule = (
        (df["candle_pattern"].isin(["Bearish Engulfing", "Shooting Star"]))
        | ((df["rsi_14"] > 72) & (c < df["sma_20"]))
        | ((df["macd_hist"] < 0) & (df["macd_hist"].shift(1) >= 0) & (c < df["sma_50"]))
    )

    df["signal_decision"] = np.select([buy_rule, sell_rule], ["BUY", "SELL"], default="HOLD")
    return df


def generate_all_signals():
    start_time = time.time()
    conn = sqlite3.connect(DB_PATH)

    print("[QUERY] Extracting raw OHLCV dataset from SQLite...")
    df = pd.read_sql_query(
        """
        SELECT trade_date, symbol, open_price, high_price, low_price, close_price, volume
        FROM fact_daily_ohlcv
        ORDER BY symbol, trade_date ASC
        """,
        conn,
    )

    total_rows = len(df)
    unique_symbols = df["symbol"].nunique()
    print(f"[PROCESS] Processing {total_rows:,} records across {unique_symbols} symbols...")

    # Process grouped by symbol
    processed_dfs = []
    for symbol, group in df.groupby("symbol"):
        # Skip symbols with insufficient history to prevent noise
        if len(group) < 5:
            continue
        processed_dfs.append(calculate_indicators_for_group(group))

    result_df = pd.concat(processed_dfs, ignore_index=True)

    # Fill any remaining NaNs with zeros or defaults for clean SQL storage
    fill_defaults = {
        "sma_20": result_df["close_price"],
        "sma_50": result_df["close_price"],
        "bb_upper": result_df["close_price"],
        "bb_lower": result_df["close_price"],
        "macd_line": 0.0,
        "macd_signal": 0.0,
        "macd_hist": 0.0,
        "rsi_14": 50.0,
    }
    result_df = result_df.fillna(value=fill_defaults)

    records = result_df[
        [
            "trade_date",
            "symbol",
            "close_price",
            "sma_20",
            "sma_50",
            "rsi_14",
            "macd_line",
            "macd_signal",
            "macd_hist",
            "bb_upper",
            "bb_lower",
            "candle_pattern",
            "signal_decision",
        ]
    ].values.tolist()

    print(f"[LOAD] Writing {len(records):,} rows into fact_technical_signals...")
    cursor = conn.cursor()

    # Clear existing to guarantee fresh, non-fragmented analytical facts
    cursor.execute("DELETE FROM fact_technical_signals;")

    # Chunked bulk insert
    chunk_size = 20000
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        cursor.executemany(
            """
            INSERT INTO fact_technical_signals (
                trade_date, symbol, close_price, sma_20, sma_50, rsi_14,
                macd_line, macd_signal, macd_hist, bb_upper, bb_lower,
                candle_pattern, signal_decision
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            chunk,
        )
        conn.commit()

    conn.close()
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"SIGNAL ENGINE FINISHED in {elapsed:.2f} seconds.")
    print(f" - Rows Processed : {len(records):,}")
    print(f" - Signal Decisions: BUY: {(result_df['signal_decision'] == 'BUY').sum():,} | "
          f"SELL: {(result_df['signal_decision'] == 'SELL').sum():,} | "
          f"HOLD: {(result_df['signal_decision'] == 'HOLD').sum():,}")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_signals()