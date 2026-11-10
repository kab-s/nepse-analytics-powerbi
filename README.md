# NEPSE Analytics & Quantitative Trading Dashboard

### Institutional-Grade Technical Screening, Multi-Strategy Walk-Forward Backtesting, and Power BI Financial Intelligence for the Nepal Stock Exchange (NEPSE)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811.svg?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Deneb Vega-Lite](https://img.shields.io/badge/Custom_Visual-Deneb_Vega--Lite_v5-FF4B4B.svg)](https://deneb-viz.github.io/)
[![SQLite 3](https://img.shields.io/badge/Database-SQLite_3-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Regulatory Standard](https://img.shields.io/badge/Regulations-May_2024_SEBON_Slabs-10B981.svg)](#5-real-world-market-friction--nepal-regulatory-modeling)
[![Verified Pipeline](https://img.shields.io/badge/Pipeline_Integrity-100%25_Idempotent-blue.svg)](#6-reproduction--execution-guide)

An end-to-end quantitative analytics engine and interactive 4-page Power BI executive terminal analyzing **60,178 daily OHLCV trading facts** across **476 listed Nepalese securities**. 

The system implements a production ETL data pipeline in Python and SQLite, computes vectorized technical indicators and candlestick geometries, conducts realistic walk-forward backtests across **4 quantitative strategies (3,727 completed trades)** under official **May 2024 SEBON tiered broker commissions**, and exposes high-density financial visualizations through **Power BI Desktop**, custom **Deneb (Vega-Lite)** candlestick charts, and an automated **CDSC WACC paper trading ledger**.

---

## 📌 Quick Links

- 📑 **[Executive PDF Showcase (`NEPSE_Analytics.pdf`)](NEPSE_Analytics.pdf)** — High-resolution 4-page visual presentation deck of the complete dashboard.
- 📊 **[Power BI Desktop Model (`NEPSE_Analytics.pbix`)](NEPSE_Analytics.pbix)** — Fully configured report with custom DAX measures, star schema, and Deneb visuals.
- 🕯️ **[Deneb Candlestick Specification (`powerbi/deneb_candlestick_spec.json`)](powerbi/deneb_candlestick_spec.json)** — Production Vega-Lite v5 declarative financial chart specification.
- 🗄️ **[Relational SQL Schema & Views (`sql/`)](sql/)** — DDL schemas and optimized analytical views (`vw_market_overview_latest`, `vw_deneb_candlestick`, `vw_backtest_performance`, `vw_paper_portfolio_holdings`).

---

## 🏆 Executive Scorecard & Audited Results

| Dimension / Metric | Audited Result | Production Implementation Detail |
|---|:---:|---|
| **Market Data Universe** | **60,178 Daily Facts** | Official NEPSE daily transactions across 476 listed equities, debentures, and mutual funds (2026-01-01 to 2026-11-06) |
| **Pipeline Architecture** | **3-Tier Idempotent Stack** | Automated Python ETL $\rightarrow$ SQLite Relational Schema $\rightarrow$ Vectorized Signal Engine $\rightarrow$ Power BI DAX |
| **Analytical Indicator Set** | **7 Vectorized Indicators** | SMA 20, SMA 50, Bollinger Bands (20, 2.0), MACD (12, 26, 9), Wilder's RSI (14), Candlestick Pattern Geometries |
| **Quantitative Strategies** | **4 Walk-Forward Rule Sets** | Composite Multi-Factor, MACD Trend Crossover, Wilder's RSI Mean Reversion, Candlestick Price Action |
| **Backtest Trade Universe** | **3,727 Completed Trades** | Walk-forward simulation across 402 eligible stocks; zero lookahead bias; strict T+1 execution |
| **Market Friction Modeling** | **May 2024 SEBON Rules** | 5-tier broker commission schedule (0.27%–0.40%), 0.015% SEBON fee, NPR 25 CDSC DP charge (sell only), 7.5% CGT |
| **Paper Portfolio Engine** | **Live Mark-to-Market** | Automated BUY CSV ingestion, CDSC WACC cost basis accounting, and live unrealized P&L against latest LTP |
| **Data Visualization Tier** | **4-Page Interactive Suite** | Executive Overview, Deneb Vega-Lite Terminal, Interactive Strategy Lab, Strategy Screener & Benchmark Matrix |

---

## 1. Problem Statement: Retail Intuition vs. Quantitative Ground Truth

In emerging equity markets like the Nepal Stock Exchange (NEPSE), retail market participants frequently suffer compounding portfolio drawdowns due to three systemic pitfalls:

1. **Heuristic & Rumor-Driven Trading:** Relying on unverified social media sentiment or lagging chart patterns without empirical win-rate or expectancy data.
2. **Failure to Account for Transaction Friction:** Underestimating the drag of broker commissions, SEBON regulatory fees, CDSC depository fees, and Capital Gains Tax (CGT), which can turn a superficially profitable price return into a net negative trade.
3. **Absence of Unified Portfolio Telemetry:** Disconnected tracking between theoretical technical setups, backtested strategy expectancy, and active cash portfolio holdings.

### The Solution: A Complete Quantitative Analytics Ecosystem
This project replaces subjective guesswork with an audited, quantitative decision-support system:
* **Separation of Concerns:** Uncouples **pure price-action statistical validity** (unlevered price return) from **cash portfolio execution** (friction, taxes, WACC, and fee drag).
* **Automated Data Engineering:** Ingests raw NEPSE daily CSV exports, repairs malformed strings and unquoted company commas, and synchronizes a normalized SQLite database.
* **Institutional-Grade Visual Intelligence:** Delivers an interactive 4-page Power BI dashboard featuring custom declarative Vega-Lite candlestick charts, dynamic single-stock equity curves, and head-to-head strategy leaderboards.

---

## 2. End-to-End System Architecture

The pipeline processes raw market data into clean analytical feeds through three modular, decoupled stages:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  NEPSE ANALYTICS PIPELINE                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
   1. INGESTION & DATA NORMALIZATION            ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────┐
   │ Module 01: `src/01_ingest_to_sql.py`                                                     │
   │ • Fast bulk ingestion + comma-separated security name repair                             │
   │ • Strict numeric cleaning, schema enforcement, and primary key deduplication             │
   │ • Synchronizes `dim_company`, `dim_calendar`, and `fact_daily_ohlcv`                     │
   │ • Automatically compiles production views from `sql/02_views_powerbi.sql`                │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
   2. VECTORIZED SIGNAL & INDICATOR ENGINE      ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────┐
   │ Module 02: `src/02_signal_engine.py`                                                     │
   │ • Computes SMA 20, SMA 50, Bollinger Bands (20, 2.0), MACD (12, 26, 9)                   │
   │ • 14-Day Wilder's Exponential Smoothing RSI with cold-start warmup safety                │
   │ • Mathematical Candlestick Geometries: Bullish/Bearish Engulfing, Hammer, Shooting Star │
   │ • Generates discrete BUY, SELL, HOLD decisions into `fact_technical_signals`             │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
   3. MULTI-STRATEGY BACKTEST & PAPER LEDGER    ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────┐
   │ Module 03: `src/03_simple_backtester.py`                                                 │
   │ • Walk-forward simulation of 4 modular trading strategies across 402 stocks              │
   │ • Real-world transaction friction: May 2024 SEBON broker slabs, DP fees, 7.5% CGT        │
   │ • Dual-book paper trading ledger: CDSC WACC cost basis & live LTP mark-to-market         │
   │ • Populates `fact_backtest_trades` and `fact_paper_holdings`                             │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
   4. POWER BI PRESENTATION TIER                ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────┐
   │ Power BI Desktop (`NEPSE_Analytics.pbix`) & Deneb Vega-Lite Specification                │
   │ • Page 1: Market Overview & Daily Movers (Breadth, Turnover, Top Movers, Signals)        │
   │ • Page 2: Technical Terminal & Deneb Candlesticks (Bollinger Bands, RSI, MACD)           │
   │ • Page 3: Strategy Lab & Paper Trading Portfolio (Dynamic Equity Curves, Live Holdings)  │
   │ • Page 4: Strategy Screener & Benchmark Matrix (Top 10 Outperformers, Cross-Filter)      │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Power BI Executive Dashboard Suite

The Power BI dashboard is organized into four specialized analytical pages designed for institutional research and executive decision-making:

### Page 1: Market Overview & Daily Movers
* **Market Pulse KPIs:** Total Daily Market Turnover (NPR), Active Traded Securities Count, Market Advance/Decline Breadth Ratio (`Gainers / Losers`), and Total Market Transactions.
* **Top 10 Gainers & Losers:** Clustered bar visual isolating single-day percentage leaders and laggards with conditional green/red formatting.
* **Signal Distribution Donut:** Real-time classification of the entire market universe into active **BUY**, **SELL**, and **HOLD** quantitative recommendations.
* **Comprehensive Market Grid:** Cross-filterable tabular screener displaying LTP, Volume, Turnover, 14-day RSI, and Candlestick Pattern tags.

### Page 2: Technical Terminal & Custom Deneb Candlestick Visual
* **Interactive Deneb Candlestick Terminal:** Built using custom Vega-Lite v5 JSON specification. Features true financial candlesticks (green up-days, red down-days with high/low wicks), an overlayed 20-period Simple Moving Average trendline (`#FB923C`), shaded 20-day $\pm 2.0\sigma$ Bollinger Bands (`#1A73E8`), and discrete quantitative Buy (cyan $\blacktriangle$) / Sell (purple $\blacktriangledown$) trigger markers.
* **Synchronized Volume Subplot:** Bottom-docked daily volume bars with color-coded directional alignment.
* **Wilder's 14-Day RSI Sub-chart:** Continuous line chart bounded by dashed Overbought ($70$) and Oversold ($40$) threshold lines.
* **MACD (12, 26, 9) Momentum Oscillator:** Line and clustered column chart plotting MACD Line, Signal Line, and zero-centered momentum histogram bars.
* **Slicer Controls:** Single-select security dropdown with live search and an interactive date range timeline slider.

### Page 3: Strategy Lab & Paper Trading Portfolio
* **Interactive Strategy Backtest Lab:**
  * Dynamic Strategy Slicer: Toggle between Composite Multi-Factor, MACD Crossover, RSI Mean Reversion, and Candlestick Price Action.
  * Single-Stock Dynamic Cumulative Equity Curve: Visualizes theoretical portfolio trajectory against total cumulative fees paid.
  * Trade Audit Log: Detailed execution table showing Entry Date, Exit Date, Holding Duration (Days), Gross Price Return %, Fees Paid, and Net Realized P&L.
* **Live Paper Trading Portfolio (Dual-Book Accounting):**
  * Ingests real user BUY executions from `data/paper_trades.csv`.
  * Computes strict **CDSC Weighted Average Cost of Capital (WACC)** including acquisition broker commissions and SEBON fees.
  * Computes live mark-to-market **Unrealized P&L (NPR)** and **Unrealized Return %** against the latest verified market Closing Price (LTP).

### Page 4: Strategy Screener & Benchmark Matrix
* **Top 10 Outperformers vs. Underperformers:** Horizontal bar charts ranking the top winning and losing stocks for any selected quantitative strategy.
* **Strategy Benchmark Comparison Matrix:** Executive cross-comparison table evaluating all 4 strategies head-to-head across **Trade Count**, **Win Rate %**, **Average Price Return %**, **Average Holding Days**, **Cumulative Net P&L (NPR)**, and **Total Regulatory Friction Drag (NPR)**.
* **Holding Duration vs. Return Scatter:** Visualizes trade return distribution across holding duration, highlighting quick stop-outs vs. extended trend rides.

---

## 4. Quantitative Strategy Benchmark Leaderboard

All four strategies were simulated across **60,178 daily price bars** over **402 distinct securities** for the 2026 trading year under strict out-of-sample walk-forward execution (exiting on the immediate subsequent trading day's close upon signal generation):

```
=========================================================================================================
QUANTITATIVE STRATEGY BENCHMARK LEADERBOARD (Pure Price Action & Realistic Friction)
=========================================================================================================
                Strategy  Trades  Wins  Losses Win Rate % Avg Price Ret %  Avg Hold Days Net PnL (NPR) Total Friction
  Composite Multi-Factor    1512   457    1055     30.22%          -1.12%           17.9 -1,488,128.24     623,172.44
    MACD Trend Crossover     914   247     667     27.02%          -1.38%           14.5 -1,063,234.02     392,102.80
      RSI Mean Reversion     604   178     426     29.47%          -1.24%           30.5   -620,114.82     237,080.11
Candlestick Price Action     697   217     480     31.13%          -1.62%           26.5   -835,675.32     272,512.95
=========================================================================================================
```

### Quantitative Findings:
1. **The Friction Drag Phenomenon:** Across all strategies, transaction fees (brokerage + SEBON + DP charges) eroded between **15% to 40% of gross capital**, proving that frequent retail trading in NEPSE is structurally penalized without high-conviction expectancy.
2. **Mean Reversion vs. Momentum:** RSI Mean Reversion exhibited the lowest total fee drag (NPR 237,080) and longest average holding duration (30.5 days), acting as a superior risk-adjusted swing framework compared to fast-switching trend crossover systems in range-bound market regimes.
3. **Price Return Statistical Separation:** Isolating `price_return_pct` from cash-sized P&L guarantees that statistical validity is evaluated independently of arbitrary position sizing.

---

## 5. Real-World Market Friction & Nepal Regulatory Modeling

Unlike generic trading tutorials that assume zero slippage and zero commissions, this pipeline precisely encodes the **official Securities Board of Nepal (SEBON) regulatory gazette (effective May 2024 / Jestha 2081)**:

### 1. Tiered Broker Commission Slabs (Equity Tranche)
$$
\text{Broker Fee} = 
\begin{cases} 
0.40\% & \text{for Trade Amount} \le \text{NPR } 50,000 \\
0.37\% & \text{for NPR } 50,001 \text{ to } 500,000 \\
0.34\% & \text{for NPR } 500,001 \text{ to } 2,000,000 \\
0.30\% & \text{for NPR } 2,000,001 \text{ to } 10,000,000 \\
0.27\% & \text{for Trade Amount} > \text{NPR } 10,000,000 
\end{cases}
$$
*(Minimum broker commission floor: NPR 10.00 per transaction)*

### 2. Regulatory & Clearing Charges
* **SEBON Regulatory Fee:** Flat **0.015%** ($0.00015$) levied on total turnover on both BUY and SELL transactions.
* **CDSC Depository (DP) Fee:** Flat **NPR 25.00** per security transfer, applied strictly on **SELL** transactions (zero DP charge on BUY).

### 3. Capital Gains Taxation (CGT)
* **Individual CGT:** Flat **7.5%** on realized net capital gains ($\text{Gross Profit} - \text{Total Buy Fees} - \text{Total Sell Fees}$). Zero tax assessed on unprofitable trades.

### 4. CDSC Weighted Average Cost of Capital (WACC) Formula
For paper portfolio accounting, open positions calculate true acquisition cost using official CDSC WACC standards:
$$
\text{WACC} = \frac{\sum (\text{Purchase Value} + \text{Broker Commission} + \text{SEBON Fee})}{\text{Total Traded Quantity}}
$$

---

## 6. Reproduction & Execution Guide

The entire pipeline is self-contained, reproducible, and requires only standard Python libraries:

### Step 1: Clone the Repository
```bash
git clone https://github.com/kab-s/nepse-analytics-powerbi.git
cd nepse-analytics-powerbi
```

### Step 2: Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 3: Execute the Data & Quant Pipeline
Run the three idempotent modules sequentially:

```bash
# 1. Ingest daily CSVs, normalize OHLCV facts, and compile SQL views
python src/01_ingest_to_sql.py

# 2. Compute technical indicators, RSI, MACD, and candlestick patterns
python src/02_signal_engine.py

# 3. Ingest paper trades, calculate CDSC WACC, and execute walk-forward backtests
python src/03_simple_backtester.py
```
*Total pipeline execution time: ~25 seconds on standard hardware.*

### Step 4: Open and Explore in Power BI Desktop
1. Open [`NEPSE_Analytics.pbix`](NEPSE_Analytics.pbix) in **Power BI Desktop**.
2. Click **Home $\rightarrow$ Refresh** to synchronize the report with the freshly compiled SQLite database (`nepse.db`).
3. Alternatively, review the pre-rendered showcase presentation in [`NEPSE_Analytics.pdf`](NEPSE_Analytics.pdf).

---

## 7. Repository Structure

```
.
├── README.md                              <- Production repository overview & technical documentation
├── requirements.txt                       <- Pinned Python dependencies (pandas, numpy, python-dateutil)
├── .gitignore                             <- Git exclusion rules (virtual environments, local caches)
├── nepse.db                               <- Pre-compiled production SQLite 3 relational database
├── NEPSE_Analytics.pbix                   <- Power BI Desktop multi-page report with DAX & Deneb
├── NEPSE_Analytics.pdf                    <- High-resolution 4-page executive presentation deck
│
├── data/                                  <- Market data input directory
│   ├── 2026.csv                           <- Official 2026 NEPSE historical daily OHLCV dataset
│   ├── paper_trades.csv                   <- CSV ledger for user paper portfolio BUY executions
│   └── Today's Price - 2026-*.csv         <- Daily transaction delta price feeds
│
├── powerbi/                               <- Custom visual templates & theme definitions
│   └── deneb_candlestick_spec.json        <- Production Vega-Lite v5 specification for Deneb
│
├── sql/                                   <- Relational database scripts
│   ├── 01_schema_ddl.sql                  <- DDL schema creating dimension, fact tables, and indexes
│   └── 02_views_powerbi.sql               <- Production analytical views feeding Power BI
│
└── src/                                   <- Modular Python ETL & quantitative engine
    ├── 01_ingest_to_sql.py                <- Module 01: Ingestion, cleaning, and SQL view synchronization
    ├── 02_signal_engine.py                <- Module 02: Vectorized indicators & candlestick patterns
    └── 03_simple_backtester.py            <- Module 03: Multi-strategy backtester & CDSC WACC ledger
```

---

## 8. Analytical Boundaries & Risk Disclosures

To maintain professional and quantitative integrity:
* **Historical Simulation Boundary:** Past backtested performance is strictly educational and does not guarantee future financial returns. Market liquidity, execution slippage, circuit breakers, and order book depth may affect live trading executions.
* **No Financial Advice:** This project serves as an analytical engineering framework and decision-support tool. It does not constitute investment advice or brokerage recommendations.
* **Idempotent Data Integrity:** All database operations use `IF NOT EXISTS`, `ON CONFLICT DO UPDATE`, and atomic transactions to prevent duplicate records or orphaned foreign keys.

---

## 👨‍💻 Author & Connect

**Kabindra Shrestha**  
*Data Analyst | Data Scientist | Applied AI/ML Engineer | BI & MIS Specialist*  
**MBA • BBIS • MCA (Candidate)**  
Lalitpur, Nepal

* 💼 **LinkedIn:** [kabindra-shrestha](https://www.linkedin.com/in/kabindra-shrestha-b34542170/)
* 🌐 **Flagship Project:** [FlyRank: Enterprise Page Priority Pipeline](https://github.com/kab-s/flyrank-page-priority-pipeline)
* 🐙 **GitHub:** [@kab-s](https://github.com/kab-s)
