"""
Module 03: Multi-Strategy Quantitative Backtester & CSV Paper Portfolio Ledger
Applies exact NEPSE fee tiers (Broker, SEBON, CDSC DP on Sell side per Kharchapatra),
simulates multiple quantitative trading strategies across all securities,
and maintains the user-driven paper-trading portfolio ledger with CDSC-compliant WACC.
"""

import os
import sqlite3
import argparse
import time
import pandas as pd
import numpy as np

DB_PATH = "nepse.db"
PAPER_CSV_PATH = os.path.join("data", "paper_trades.csv")


def compute_nepse_fees(gross_amount: float, is_buy: bool = True) -> tuple[float, float, float]:
    """
    Computes exact NEPSE transaction friction per official SEBON & CDSC rules:
    (Reference: Kharchapatra NEPSE Share Trading Costs)
    - Tiered Broker Commission (May 2024 SEBON schedule) with Rs. 10 minimum floor:
        <= Rs 50,000      : 0.36%
        <= Rs 500,000     : 0.33%
        <= Rs 2,000,000   : 0.31%
        <= Rs 10,000,000  : 0.27%
        >  Rs 10,000,000  : 0.24%
    - SEBON Regulatory Fee: 0.015% (applied on both Buy and Sell)
    - CDSC DP Charge: Rs. 25 flat per scrip per settlement day (applied on SELL side ONLY)
    """
    if gross_amount <= 0:
        return 0.0, 0.0, 0.0

    # Tiered broker commission
    if gross_amount <= 50000:
        comm_rate = 0.0036
    elif gross_amount <= 500000:
        comm_rate = 0.0033
    elif gross_amount <= 2000000:
        comm_rate = 0.0031
    elif gross_amount <= 10000000:
        comm_rate = 0.0027
    else:
        comm_rate = 0.0024

    broker_comm = max(10.0, round(gross_amount * comm_rate, 2))
    sebon_fee = round(gross_amount * 0.00015, 2)
    # DP charge is levied ONLY when selling/transferring shares out of Demat (Sell side)
    dp_fee = 0.0 if is_buy else 25.0

    return broker_comm, sebon_fee, dp_fee


def run_multi_strategy_backtest(sample_symbols: list[str] = None):
    """
    Simulates walk-forward quantitative execution across 4 distinct strategies:
      1. Composite Multi-Factor (Confluence of Candlestick + RSI + MACD + Trend)
      2. MACD Trend Crossover (Bullish histogram crossing 0 filtered by SMA 50)
      3. RSI Mean Reversion (Oversold bounce < 35 with green candle confirmation)
      4. Candlestick Price Action (Bullish Engulfing & Bullish Hammer)
    Records both pure price return (capital-agnostic) and fee-inclusive returns.
    """
    conn = sqlite3.connect(DB_PATH)
    t0 = time.time()

    query = """
        SELECT 
            o.trade_date, o.symbol, o.open_price, o.high_price, o.low_price, o.close_price,
            s.sma_20, s.sma_50, s.bb_upper, s.bb_lower, s.rsi_14, 
            s.macd_line, s.macd_signal, s.macd_hist,
            s.candle_pattern, s.signal_decision
        FROM fact_daily_ohlcv o
        JOIN fact_technical_signals s 
          ON o.trade_date = s.trade_date AND o.symbol = s.symbol
        ORDER BY o.symbol, o.trade_date ASC
    """
    df = pd.read_sql_query(query, conn)

    if sample_symbols:
        df = df[df["symbol"].isin(sample_symbols)].copy()

    total_rows = len(df)
    symbols_count = df["symbol"].nunique()
    print(f"\n[BACKTEST] Loaded {total_rows:,} daily records across {symbols_count} symbols.")

    # 1. Vectorized indicator condition preparation
    df["prev_macd_hist"] = df.groupby("symbol")["macd_hist"].shift(1).fillna(0)

    # Strategy 1: Composite Multi-Factor (Engine Confluence)
    df["buy_composite"] = df["signal_decision"] == "BUY"
    df["sell_composite"] = df["signal_decision"] == "SELL"

    # Strategy 2: MACD Trend Crossover (MACD Histogram crosses > 0 with Close > SMA 50)
    df["buy_macd"] = (
        (df["macd_hist"] > 0)
        & (df["prev_macd_hist"] <= 0)
        & (df["close_price"] > df["sma_50"])
    )
    df["sell_macd"] = (df["macd_hist"] < 0) & (df["prev_macd_hist"] >= 0)

    # Strategy 3: RSI Mean Reversion (Oversold < 35 bouncing with green candle)
    df["buy_rsi"] = (df["rsi_14"] < 35) & (df["close_price"] > df["open_price"])
    df["sell_rsi"] = df["rsi_14"] > 70

    # Strategy 4: Candlestick Price Action (Bullish Hammer / Bullish Engulfing)
    df["buy_candle"] = df["candle_pattern"].isin(["Bullish Engulfing", "Bullish Hammer"])
    df["sell_candle"] = df["candle_pattern"].isin(["Bearish Engulfing", "Shooting Star"])

    strategy_configs = [
        ("Composite Multi-Factor", "buy_composite", "sell_composite"),
        ("MACD Trend Crossover", "buy_macd", "sell_macd"),
        ("RSI Mean Reversion", "buy_rsi", "sell_rsi"),
        ("Candlestick Price Action", "buy_candle", "sell_candle"),
    ]

    all_trades = []
    summary_stats = []

    print("[BACKTEST] Running multi-strategy walk-forward simulation...")

    for strat_name, buy_col, sell_col in strategy_configs:
        strat_trades = []

        for symbol, group in df.groupby("symbol"):
            group = group.reset_index(drop=True)
            in_position = False
            entry_price = 0.0
            entry_date = None
            qty = 0

            open_arr = group["open_price"].values
            close_arr = group["close_price"].values
            date_arr = group["trade_date"].values
            buy_arr = group[buy_col].values
            sell_arr = group[sell_col].values
            n = len(group)

            for i in range(n - 1):
                if not in_position:
                    # Enter next day on buy trigger
                    if buy_arr[i] and open_arr[i + 1] > 0:
                        in_position = True
                        entry_price = open_arr[i + 1]
                        entry_date = date_arr[i + 1]
                        # Nominal position sizing: ~Rs. 50,000 allocation (min 10 kitta)
                        qty = max(10, int(50000 // entry_price))
                else:
                    current_pnl_pct = (close_arr[i] - entry_price) / entry_price
                    should_exit = (
                        sell_arr[i]
                        or current_pnl_pct >= 0.10   # +10% Take Profit
                        or current_pnl_pct <= -0.05  # -5% Stop Loss
                    )

                    if should_exit and open_arr[i + 1] > 0:
                        exit_price = open_arr[i + 1]
                        exit_date = date_arr[i + 1]

                        # Pure price-action return % (capital-agnostic)
                        price_return_pct = round(((exit_price - entry_price) / entry_price) * 100, 2)

                        # Friction & fee-inclusive cash P&L
                        buy_gross = qty * entry_price
                        b_comm, b_sebon, b_dp = compute_nepse_fees(buy_gross, is_buy=True)
                        total_buy_cost = buy_gross + b_comm + b_sebon + b_dp

                        sell_gross = qty * exit_price
                        s_comm, s_sebon, s_dp = compute_nepse_fees(sell_gross, is_buy=False)
                        net_sell_proceeds = sell_gross - s_comm - s_sebon - s_dp

                        net_pnl = round(net_sell_proceeds - total_buy_cost, 2)
                        net_return_pct = round((net_pnl / total_buy_cost) * 100, 2)
                        holding_days = (pd.to_datetime(exit_date) - pd.to_datetime(entry_date)).days

                        # NEPSE CGT: 5% short-term capital gains tax on profitable sales (<= 365 days)
                        cgt_tax = round(net_pnl * 0.05, 2) if (net_pnl > 0 and holding_days <= 365) else 0.0

                        # A trade is a WIN if price return is positive
                        is_win = 1 if price_return_pct > 0 else 0

                        strat_trades.append({
                            "strategy_name": strat_name,
                            "symbol": symbol,
                            "entry_date": entry_date,
                            "exit_date": exit_date,
                            "holding_days": holding_days,
                            "qty": qty,
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "price_return_pct": price_return_pct,
                            "total_fees": round(b_comm + b_sebon + b_dp + s_comm + s_sebon + s_dp, 2),
                            "cgt_tax": cgt_tax,
                            "net_pnl": net_pnl,
                            "net_return_pct": net_return_pct,
                            "is_win": is_win,
                        })
                        in_position = False

        strat_df = pd.DataFrame(strat_trades)
        if not strat_df.empty:
            tot_trades = len(strat_df)
            wins = strat_df["is_win"].sum()
            win_rate = round((wins / tot_trades) * 100, 2)
            tot_pnl = round(strat_df["net_pnl"].sum(), 2)
            tot_friction = round(strat_df["total_fees"].sum(), 2)
            avg_price_ret = round(strat_df["price_return_pct"].mean(), 2)
            avg_days = round(strat_df["holding_days"].mean(), 1)

            summary_stats.append({
                "Strategy": strat_name,
                "Trades": tot_trades,
                "Wins": wins,
                "Losses": tot_trades - wins,
                "Win Rate %": f"{win_rate}%",
                "Avg Price Ret %": f"{avg_price_ret}%",
                "Avg Hold Days": avg_days,
                "Net PnL (NPR)": f"{tot_pnl:,.2f}",
                "Total Friction": f"{tot_friction:,.2f}"
            })
            all_trades.extend(strat_trades)

    all_trades_df = pd.DataFrame(all_trades)
    if all_trades_df.empty:
        print("[BACKTEST] No trades generated.")
        conn.close()
        return

    # Store backtest results in SQLite for Power BI
    print(f"\n[LOAD] Saving {len(all_trades_df):,} trades across 4 strategies into fact_backtest_trades...")
    all_trades_df.to_sql("fact_backtest_trades", conn, if_exists="replace", index=False)

    # Recreate the analytical view vw_backtest_performance with price_return_pct
    cursor = conn.cursor()
    cursor.execute("DROP VIEW IF EXISTS vw_backtest_performance;")
    cursor.execute("""
        CREATE VIEW vw_backtest_performance AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY exit_date ASC, strategy_name ASC, symbol ASC) AS trade_id,
            strategy_name,
            symbol,
            entry_date,
            exit_date,
            holding_days,
            qty,
            entry_price,
            exit_price,
            price_return_pct,
            total_fees,
            cgt_tax,
            net_pnl,
            net_return_pct,
            is_win,
            -- Running Cumulative Net PnL partitioned by Strategy
            SUM(net_pnl) OVER (PARTITION BY strategy_name ORDER BY exit_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_net_pnl,
            SUM(total_fees) OVER (PARTITION BY strategy_name ORDER BY exit_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_fees_paid
        FROM fact_backtest_trades;
    """)
    conn.commit()
    conn.close()

    # Print clean benchmark leaderboard
    print("=" * 105)
    print("QUANTITATIVE STRATEGY BENCHMARK LEADERBOARD (Pure Price Action & Metrics)")
    print("=" * 105)
    summary_df = pd.DataFrame(summary_stats)
    print(summary_df.to_string(index=False))
    print("=" * 105)
    print(f"Total walk-forward simulation finished in {time.time()-t0:.2f}s.\n")


def sync_paper_portfolio(csv_path: str = PAPER_CSV_PATH):
    """
    Ingests user's paper trading buys from data/paper_trades.csv (trade_date, symbol, quantity).
    Auto-fetches historical close price from fact_daily_ohlcv as execution price,
    applies exact NEPSE broker commission & SEBON fee,
    calculates CDSC WACC, fetches latest LTP, and tracks live unrealized P&L.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not os.path.exists(csv_path):
        template_df = pd.DataFrame([
            {"trade_date": "2024-05-15", "symbol": "NABIL", "quantity": 100},
            {"trade_date": "2024-06-20", "symbol": "HATHY", "quantity": 200},
            {"trade_date": "2024-07-10", "symbol": "GLBSL", "quantity": 80},
            {"trade_date": "2024-09-12", "symbol": "ENL", "quantity": 120},
            {"trade_date": "2024-10-15", "symbol": "SHIVM", "quantity": 150},
        ])
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        template_df.to_csv(csv_path, index=False)
        print(f"[PAPER] Created default template at '{csv_path}'")

    try:
        user_trades = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[PAPER ERROR] Failed to read {csv_path}: {e}")
        conn.close()
        return

    # Normalize column names
    user_trades.columns = [c.strip().lower() for c in user_trades.columns]
    if "qty" in user_trades.columns and "quantity" not in user_trades.columns:
        user_trades = user_trades.rename(columns={"qty": "quantity"})

    req_cols = {"trade_date", "symbol", "quantity"}
    if not req_cols.issubset(set(user_trades.columns)):
        print(f"[PAPER ERROR] CSV missing required columns (trade_date, symbol, quantity). Found: {list(user_trades.columns)}")
        conn.close()
        return

    # Clear fact_paper_portfolio for clean ingestion
    cursor.execute("DELETE FROM fact_paper_portfolio;")

    records = []
    print(f"[PAPER] Processing {len(user_trades)} paper trade entries from {csv_path}...")

    for _, row in user_trades.iterrows():
        t_date = str(row["trade_date"]).strip()
        sym = str(row["symbol"]).strip().upper()
        try:
            qty = int(row["quantity"])
        except (ValueError, TypeError):
            continue

        if qty <= 0:
            continue

        # Look up execution price (close_price on or nearest prior to trade_date)
        price_row = cursor.execute("""
            SELECT close_price, trade_date 
            FROM fact_daily_ohlcv 
            WHERE symbol = ? AND trade_date <= ? 
            ORDER BY trade_date DESC LIMIT 1
        """, (sym, t_date)).fetchone()

        if price_row and price_row[0] > 0:
            exec_price = float(price_row[0])
            actual_date = price_row[1]
        else:
            # Fallback to earliest available price for symbol
            fallback = cursor.execute("""
                SELECT close_price, trade_date 
                FROM fact_daily_ohlcv 
                WHERE symbol = ? 
                ORDER BY trade_date ASC LIMIT 1
            """, (sym,)).fetchone()
            if fallback:
                exec_price = float(fallback[0])
                actual_date = fallback[1]
            else:
                print(f"[PAPER WARNING] No price data found for '{sym}'. Skipping.")
                continue

        gross = qty * exec_price
        comm, sebon, dp = compute_nepse_fees(gross, is_buy=True)  # DP = 0 on Buy
        records.append((actual_date, sym, "BUY", qty, exec_price, comm, sebon, dp, "PAPER_TRADING"))

    cursor.executemany("""
        INSERT INTO fact_paper_portfolio (
            trade_date, symbol, trade_type, quantity, execution_price,
            broker_comm, sebon_fee, dp_fee, portfolio_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()
    print(f"[PAPER] Successfully inserted {len(records)} BUY records into fact_paper_portfolio.")

    # Calculate Holdings Summary (CDSC WACC Basis & Live LTP)
    holdings_query = """
        SELECT symbol, SUM(quantity) as open_kitta,
               SUM((quantity * execution_price) + broker_comm + sebon_fee + dp_fee) as total_cost
        FROM fact_paper_portfolio
        GROUP BY symbol
    """
    holdings_df = pd.read_sql_query(holdings_query, conn)

    latest_prices = pd.read_sql_query("""
        SELECT symbol, close_price as ltp, trade_date as ltp_date
        FROM fact_daily_ohlcv
        WHERE (symbol, trade_date) IN (
            SELECT symbol, MAX(trade_date) FROM fact_daily_ohlcv GROUP BY symbol
        )
    """, conn)

    price_map = dict(zip(latest_prices["symbol"], latest_prices["ltp"]))

    summary_rows = []
    for _, row in holdings_df.iterrows():
        sym = row["symbol"]
        kitta = int(row["open_kitta"])
        cost = float(row["total_cost"])
        wacc = round(cost / kitta, 2)
        ltp = float(price_map.get(sym, wacc))
        cur_val = round(kitta * ltp, 2)
        unrealized_pnl = round(cur_val - cost, 2)
        ret_pct = round((unrealized_pnl / cost) * 100, 2)

        summary_rows.append({
            "symbol": sym,
            "open_kitta": kitta,
            "wacc": wacc,
            "ltp": ltp,
            "cost_basis": round(cost, 2),
            "current_value": cur_val,
            "unrealized_pnl": unrealized_pnl,
            "return_pct": ret_pct,
        })

    summary_df = pd.DataFrame(summary_rows)
    if not summary_df.empty:
        # Save to SQLite table and create view
        summary_df.to_sql("fact_paper_holdings", conn, if_exists="replace", index=False)
        cursor.execute("DROP VIEW IF EXISTS vw_paper_portfolio_holdings;")
        cursor.execute("CREATE VIEW vw_paper_portfolio_holdings AS SELECT * FROM fact_paper_holdings;")
        conn.commit()

        print("\n" + "=" * 80)
        print("CURRENT PAPER PORTFOLIO HOLDINGS (CDSC WACC Basis & Live LTP)")
        print("=" * 80)
        print(summary_df.to_string(index=False))
        tot_cost = summary_df["cost_basis"].sum()
        tot_val = summary_df["current_value"].sum()
        tot_pnl = summary_df["unrealized_pnl"].sum()
        tot_ret = (tot_pnl / tot_cost) * 100 if tot_cost > 0 else 0
        print("-" * 80)
        print(f"PORTFOLIO TOTALS: Cost: NPR {tot_cost:,.2f} | Market Value: NPR {tot_val:,.2f} | Unrealized PnL: NPR {tot_pnl:,.2f} ({tot_ret:+.2f}%)")
        print("=" * 80 + "\n")
    else:
        print("[PAPER] No active holdings calculated.")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEPSE Multi-Strategy Backtester & Paper Portfolio Ledger")
    parser.add_argument("--backtest", action="store_true", help="Run multi-strategy backtests")
    parser.add_argument("--sync-paper", action="store_true", help="Sync paper portfolio from CSV")
    parser.add_argument("--summary", action="store_true", help="Show current paper portfolio summary")
    args = parser.parse_args()

    # Default flow if no flags are passed: sync CSV paper portfolio and run backtest
    if not any([args.backtest, args.sync_paper, args.summary]):
        sync_paper_portfolio()
        run_multi_strategy_backtest()
    else:
        if args.sync_paper:
            sync_paper_portfolio()
        if args.backtest:
            run_multi_strategy_backtest()
        if args.summary:
            sync_paper_portfolio()
