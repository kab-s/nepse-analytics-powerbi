# NEPSE Analytics & Quantitative Trading Terminal

> **An end-to-end financial analytics pipeline, multi-strategy backtester, and interactive 4-page Power BI dashboard for the Nepal Stock Exchange (NEPSE).**

[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](NEPSE_Analytics.pbix)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](nepse.db)
[![Deneb](https://img.shields.io/badge/Deneb-Vega--Lite%20v5-FF4B4B?style=for-the-badge)](powerbi/deneb_candlestick_spec.json)
[![Showcase PDF](https://img.shields.io/badge/Showcase_Deck-PDF-E11D48?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](NEPSE_Analytics.pdf)

---

## 📑 Quick Navigation

- 📄 **[Executive 4-Page PDF Showcase (`NEPSE_Analytics.pdf`)](NEPSE_Analytics.pdf)** — High-resolution export of the complete 4-page dashboard.
- 📊 **[Power BI Report File (`NEPSE_Analytics.pbix`)](NEPSE_Analytics.pbix)** — Interactive data model with custom DAX measures and Deneb visual.
- 🕯️ **[Deneb Candlestick Specification (`powerbi/deneb_candlestick_spec.json`)](powerbi/deneb_candlestick_spec.json)** — Vega-Lite JSON code for the custom financial terminal.
- 🗄️ **[Database Schemas & Views (`sql/`)](sql/)** — DDL schemas and optimized analytical views feeding Power BI.
- 💻 **[ETL & Quant Source Code (`src/`)](src/)** — Ingestion, indicator calculation, and multi-strategy backtester.

---

## 🖥️ The 4-Page Power BI Dashboard

The dashboard is structured into four focused analytical pages in **Power BI Desktop**, connecting directly to analytical SQL views compiled in **SQLite**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             POWER BI DASHBOARD SUITE                             │
├─────────────────────┬──────────────────────┬────────────────────┬────────────────┤
│       PAGE 1        │        PAGE 2        │       PAGE 3       │     PAGE 4     │
│   Market Overview   │  Technical Terminal  │    Strategy Lab    │    Strategy    │
│   & Daily Movers    │  (Deneb Candlestick) │ & Paper Portfolio  │    Screener    │
└─────────────────────┴──────────────────────┴────────────────────┴────────────────┘
```

### Page 1: Market Overview & Daily Movers
*Provides an immediate and interactive overview of the entire trading day.*
* **Market Pulse Cards:** Total Daily Turnover, Volume, Gainers and Losers.
* **Top 10 Gainers & Losers:** Clustered horizontal bar charts displaying single-day percentage momentum with dynamic green/red conditional fills.
* **Signal Classification Donut:** Real-time classification of the entire market universe into active **BUY**, **SELL**, and **HOLD** recommendations.
* **Market Table:** Table displaying Opening & Closing Price, Daily Change %, Transactions, Turnover, Volume, 14-day RSI, detected Candlestick Patterns, and Signal Decision.

### Page 2: Technical Terminal (Custom Deneb Candlestick Chart)
*Standard Power BI visuals cannot render financial candlesticks with overlaid technical indicators. Therefore, a custom multi-layer financial chart using the **Deneb (Vega-Lite v5)** visual has been implemented.*

- **Multi-Layer Financial Canvas:**
  - True OHLC candlesticks (green up-days, red down-days with high/low wicks).
  - 20-period Simple Moving Average trendline.
  - Shaded 20-day **±2.0σ** Bollinger Bands channel to visualize volatility expansion/contraction.
  - Quantitative signal triggers: Blue triangle markers (**▲**) for Buy signals, Purple triangle markers (**▼**) for Sell signals.
- **Synchronized Volume Subplot:** Daily volume bars docked below price action with directional color matching.
- **14-Day Wilder's RSI Sub-chart:** Continuous line chart bounded by dashed Overbought (**70**) and Oversold (**40**) reference lines.
- **MACD (12, 26, 9) Indicator Visual:** Combo visual displaying MACD Line, Signal Line, and zero-centered momentum histogram bars.
- **Interactive Slicers:** Single-select security dropdown with search and interactive date range slider.

### Page 3: Strategy Lab & Paper Trading Portfolio
*Brings together 4 trade strategy for validation and current portfolio view.*
* **Top Strategy KPI Cards:** Strategy Win Rate %, Total Winning Trades, Total Losing Trades, Profit Factor, and Total Backtest Trades.
* **Closed Trades Audit Ledger:** Transparent trade-by-trade audit table showing Entry Date, Exit Date, Holding Duration, Entry Price, Exit Price, and Price Return %.
* **Trade Holding Duration vs. Pure Price Return %:** Scatter visual displaying holding period (days) on the X-axis against percentage return on the Y-axis, categorized by `Win` vs. `Loss`.
* **Paper Portfolio Summary Cards:** Total Cost Basis, Current Market Value, and Net Unrealized P&L.
* **Live Paper Holdings Table:** Active positions showing Symbol, Open Quantity (Kitta), Cost, Book Value, Current Market Value, and Unrealized P/L (Amt & %).
* **Dynamic Cumulative Price Return % (Growth Curve):** Line chart plotting the cumulative percentage price return trajectory over exit dates. Slicing by any stock (e.g., `NABIL`, `HATHY`) dynamically renders that stock's individual equity growth curve.

### Page 4: Strategy Screener & Benchmark Matrix
*Cross-sectional screener to compare strategies and identify consistent performers.*
* **Top 10 Winning Stocks:** Bar chart ranking securities by winning trade frequency under the selected strategy.
* **Top 10 Losing Stocks:** Bar chart highlighting the securities that generate the highest frequency of false signals.
* **Cross-Strategy Comparison Matrix:** Side-by-side comparison of all 4 quantitative strategies across Total Trades, Winning Trades, Losing Trades, Win Rate %, and Average Price Return % per trade.
* **Stock Win Rate % vs. Trade Frequency Scatter:** Bubble visual plotting trade frequency (X-axis) against win rate (Y-axis), with bubble size reflecting total wins, referenced against a 50% Win Rate dashed line.

---

## 📊 Quantitative Strategy Benchmark Matrix

Evaluating trade strategies across **3,727 completed walk-forward trades** in the 2026 dataset:

| Strategy | Total Trades | Winning Trades | Losing Trades | Strategy Win Rate % | 
|---|:---:|:---:|:---:|:---:|
| **Composite Multi-Factor** | 1,512 | 457 | 1,055 | **30.22%** | 
| **Candlestick Price Action** | 697 | 217 | 480 | **31.13%** | 
| **Wilder's RSI Mean Reversion** | 604 | 178 | 426 | **29.47%** | 
| **MACD Trend Crossover** | 914 | 247 | 667 | **27.02%** |

---

## 💼 Active Paper Portfolio Ledger & CDSC WACC

### Simple CSV Ingestion (`data/paper_trades.csv`)
Adding a purchase requires only 3 fields:
```csv
trade_date,symbol,quantity
2026-01-05,NABIL,100
2026-02-16,HATHY,200
2026-03-10,GLBSL,80
2026-04-12,ENL,120
2026-05-15,SHIVM,150
```
The ingestion script automatically looks up the official closing price on the purchase date from `fact_daily_ohlcv`.

---

## 🔄 Automated ETL Pipeline & Data Architecture

The repository demonstrates a complete, automated **Extract, Transform, Load (ETL)** pipeline that turns messy market exports into optimized relational tables and analytical views:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AUTOMATED ETL FLOW                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [ EXTRACT ]    Raw Daily & Historical CSVs (NEPSE exports, unquoted commas, paper trades)
                         │
                         ▼
  [ TRANSFORM ]  • Line-by-line comma repair in security names & string normalization
                 • Type-casting & numeric cleaning (stripping commas, nulls, invalid bars)
                 • Dimensional modeling: synchronizes `dim_company` & `dim_calendar`
                 • Vectorized Signal Engine (SMA 20/50, Bollinger Bands, RSI 14, MACD)
                 • Mathematical Candlestick pattern detection (Engulfing, Hammer, Star)
                 • Multi-strategy walk-forward backtesting (3,727 simulated trades)
                 • CDSC WACC accounting with official May 2024 SEBON fee slabs
                         │
                         ▼
  [ LOAD ]       • Automated DDL execution (`sql/01_schema_ddl.sql`) into SQLite
                 • Idempotent upserts (`ON CONFLICT DO UPDATE`) across Fact & Dim tables
                 • Automated compilation of Power BI views (`sql/02_views_powerbi.sql`)
```

### 1. Extract
* **Heterogeneous Ingestion:** Dynamically scans `data/` to ingest both bulk historical dumps (`2026.csv`) and official daily exports (`Today's Price - *.csv`).
* **Paper Ledger Ingestion:** Reads user BUY orders directly from `data/paper_trades.csv`.

### 2. Transform
* **Robust Text Repair:** Implements a fallback parser that reconstructs records where company names contain unquoted commas (a frequent defect in raw NEPSE exports).
* **Dimensional Modeling:** Normalizes raw records into a clean relational schema, generating a calendar dimension (`dim_calendar`) to enable time-intelligence calculations in DAX.
* **Vectorized Financial Analytics:** Uses pandas and NumPy to compute rolling indicators, exponential smoothing (Wilder's RSI, MACD), and price-action candle geometry across all securities.
* **CDSC WACC Accounting:** Computes fee-inclusive acquisition costs using May 2024 SEBON tiered broker commission slabs and marks open positions to market against live closing prices (LTP).

### 3. Load
* **Automated SQLite DDL:** Running the scripts automatically executes `sql/01_schema_ddl.sql` to initialize all 7 tables and query indexes with zero manual database administration.
* **Idempotent Ingestion:** Employs composite primary key constraints (`trade_date`, `symbol`) and `ON CONFLICT DO UPDATE` clauses to guarantee safe, repeatable re-runs.
* **Analytical View Compilation:** Automatically executes `sql/02_views_powerbi.sql` upon ingestion completion, ensuring Power BI feeds are always synchronized and query-ready.

---

## 🚀 Reproduction & Setup Guide

The pipeline is 100% self-contained and reproducible:

### 1. Clone & Setup
```bash
git clone https://github.com/kab-s/nepse-analytics-powerbi.git
cd nepse-analytics-powerbi

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies (pandas, numpy, python-dateutil)
pip install -r requirements.txt
```

### 2. Run the Pipeline
```bash
# 1. Ingest daily CSVs, normalize OHLCV facts, and compile SQL views
python src/01_ingest_to_sql.py

# 2. Compute technical indicators, RSI, MACD, and candlestick patterns
python src/02_signal_engine.py

# 3. Sync paper portfolio from CSV and run walk-forward backtest
python src/03_simple_backtester.py
```

### 3. Open the Power BI Dashboard
* Open [`NEPSE_Analytics.pbix`](NEPSE_Analytics.pbix) in **Power BI Desktop**.
* Click **Home → Refresh** to pull the latest facts.
  
---

## 📁 Repository Structure

```
.
├── README.md                              <- Project documentation and quantitative overview
├── requirements.txt                       <- Pinned Python dependencies
├── .gitignore                             <- Excludes virtual environments and local artifacts
├── nepse.db                               <- Pre-compiled SQLite 3 database (ready to query)
├── NEPSE_Analytics.pbix                   <- Power BI Desktop 4-page dashboard
├── NEPSE_Analytics.pdf                    <- High-resolution 4-page PDF presentation deck
│
├── data/                                  <- Market data feeds
│   ├── 2026.csv                           <- Official 2026 NEPSE daily OHLCV dataset
│   ├── paper_trades.csv                   <- User paper portfolio BUY ledger
│   └── Today's Price - 2026-*.csv         <- Daily price delta updates
│
├── powerbi/                               <- Custom visual specifications
│   └── deneb_candlestick_spec.json        <- Production Vega-Lite v5 specification for Deneb
│
├── sql/                                   <- Relational database code
│   ├── 01_schema_ddl.sql                  <- DDL creating dimensions, facts, and indexes
│   └── 02_views_powerbi.sql               <- Analytical SQL views feeding Power BI
│
└── src/                                   <- Python ETL and quant engine
    ├── 01_ingest_to_sql.py                <- Ingestion, data repair, and view compilation
    ├── 02_signal_engine.py                <- Vectorized indicators and candlestick detection
    └── 03_simple_backtester.py            <- Multi-strategy backtester and CDSC WACC ledger
```

---

**Kabindra Shrestha**  
*Data Analyst | Data Scientist | Applied AI/ML Engineer | BI & MIS Specialist*  
**MBA • BBIS • MCA (Candidate)**  
Lalitpur, Nepal
* 💼 **LinkedIn:** [kabindra-shrestha](https://www.linkedin.com/in/kabindra-shrestha-b34542170/)