# NEPSE Analytics & Quantitative Trading Terminal

> **An end-to-end financial analytics pipeline, multi-strategy walk-forward backtester, and interactive 4-page Power BI dashboard for the Nepal Stock Exchange (NEPSE)—built on verified daily market data, custom Deneb Vega-Lite candlestick charting, and a CDSC-compliant paper portfolio ledger.**

[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](NEPSE_Analytics.pbix)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](nepse.db)
[![Deneb](https://img.shields.io/badge/Deneb-Vega--Lite%20v5-FF4B4B?style=for-the-badge)](powerbi/deneb_candlestick_spec.json)
[![Showcase PDF](https://img.shields.io/badge/Showcase_Deck-PDF-E11D48?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](NEPSE_Analytics.pdf)

---

## 📑 Quick Navigation

- 📄 **[Executive 4-Page PDF Showcase (`NEPSE_Analytics.pdf`)](NEPSE_Analytics.pdf)** — High-resolution export of the complete 4-page dashboard.
- 📊 **[Power BI Report File (`NEPSE_Analytics.pbix`)](NEPSE_Analytics.pbix)** — Interactive data model with custom DAX measures and Deneb visual.
- 🕯️ **[Deneb Candlestick Specification (`powerbi/deneb_candlestick_spec.json`)](powerbi/deneb_candlestick_spec.json)** — Production Vega-Lite JSON code for the custom financial terminal.
- 🗄️ **[Database Schemas & Views (`sql/`)](sql/)** — DDL schemas and optimized analytical views feeding Power BI.
- 💻 **[ETL & Quant Source Code (`src/`)](src/)** — Ingestion, vectorized indicator engine, and multi-strategy backtester.

---

## 💡 The Core Architectural Shift: Separation of Concerns

In generic trading dashboards, backtests often make a naive assumption: **allocating an arbitrary flat cash amount (e.g., Rs. 50,000) to every single trade across hundreds of different stocks**. 

In practical quantitative finance and treasury operations, this assumption creates severe distortions:
1. **Capital Distortions:** Sizing 50k into an illiquid promoter share or micro-cap stock is completely unrealistic compared to sizing 50k into a commercial bank.
2. **Conflating Strategy Edge with Position Sizing:** Arbitrary cash sizing obscures whether a strategy genuinely has statistical price-action predictive power, or if returns were simply dominated by whichever trade happened to be larger.

To align this dashboard with how institutional quant desks and portfolio managers evaluate systems, I deliberately decoupled the architecture into two distinct domains:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARCHITECTURAL SEPARATION                                  │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│     1. QUANTITATIVE STRATEGY BACKTEST     │       2. ACTIVE PAPER PORTFOLIO LEDGER     │
│             (Pages 3 & 4)                 │             (Page 3 Bottom)                │
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ • Pure Capital-Agnostic Price Action      │ • Real-World Cash Accounting & Execution   │
│ • Unlevered Price Return % per trade      │ • User BUY orders ingested from simple CSV │
│ • Win Rate %, Wins vs. Losses             │ • Official May 2024 SEBON tiered fees      │
│ • Holding Duration (Days)                 │ • CDSC Weighted Average Cost Basis (WACC)  │
│ • Dynamic Cumulative % Growth Trajectory  │ • Live mark-to-market Unrealized P&L (NPR) │
└───────────────────────────────────────────┴────────────────────────────────────────────┘
```

* **The Backtest evaluates pure price-action edge:** It assesses the predictive power of 4 walk-forward quantitative strategies across **60,178 historical price bars** and **402 stocks** using pure percentage returns, win rates, and holding duration.
* **The Paper Portfolio evaluates real cash execution:** It tracks actual user-entered positions, pricing each purchase at the historical closing price, calculating exact tiered broker commissions (May 2024 SEBON slabs), regulatory fees, CDSC WACC, and live unrealized P&L against the latest closing price (LTP).

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
*Provides an immediate 30-second macro pulse of the entire trading session.*
* **Market Pulse Cards:** Total Daily Turnover (NPR), Active Traded Securities Count, Market Breadth (Advance/Decline Ratio), and Completed Transactions.
* **Top 10 Gainers & Losers:** Clustered horizontal bar charts displaying single-day percentage momentum with dynamic green/red conditional fills.
* **Signal Classification Donut:** Real-time classification of the entire market universe into active **BUY**, **SELL**, and **HOLD** recommendations.
* **Cross-Filter Market Table:** Searchable grid displaying Closing Price (LTP), Daily Change %, Turnover, Volume, 14-day RSI, and detected Candlestick Patterns.

### Page 2: Technical Terminal (Custom Deneb Candlestick Chart)
*Standard Power BI visuals cannot render financial candlesticks with overlaid technical indicators. I engineered a custom multi-layer financial chart using the **Deneb (Vega-Lite v5)** visual.*
* **Multi-Layer Financial Canvas:**
  * True OHLC candlesticks (green up-days, red down-days with high/low wicks).
  * 20-period Simple Moving Average trendline (`#FB923C`).
  * Shaded 20-day $\pm 2.0\sigma$ Bollinger Bands channel (`#1A73E8`) to visualize volatility expansion/contraction.
  * Quantitative signal triggers: Blue triangle markers ($\blacktriangle$) for Buy signals, Purple triangle markers ($\blacktriangledown$) for Sell signals.
* **Synchronized Volume Subplot:** Daily volume bars docked below price action with directional color matching.
* **14-Day Wilder's RSI Sub-chart:** Continuous line chart bounded by dashed Overbought ($70$) and Oversold ($40$) reference lines.
* **MACD (12, 26, 9) Indicator Visual:** Combo visual displaying MACD Line, Signal Line, and zero-centered momentum histogram bars.
* **Interactive Slicers:** Single-select security dropdown with search and interactive date range slider.

### Page 3: Strategy Lab & Paper Trading Portfolio
*Brings together pure statistical strategy validation and live cash portfolio management.*
* **Top Strategy KPI Cards:** Strategy Win Rate %, Total Winning Trades, Total Losing Trades, Average Trade Return %, and Total Trades.
* **Dynamic Cumulative Price Return % (Growth Curve):** Line chart plotting the cumulative percentage price return trajectory over exit dates. Slicing by any stock (e.g., `NABIL`, `HATHY`) dynamically renders that stock's individual equity growth curve.
* **Trade Holding Duration vs. Pure Price Return %:** Scatter visual displaying holding period (days) on the X-axis against percentage return on the Y-axis, categorized by `Win` (emerald green) vs. `Loss` (rose red).
* **Closed Trades Audit Ledger:** Transparent trade-by-trade audit table showing Entry Date, Exit Date, Holding Duration, Entry Price, Exit Price, and Price Return %.
* **CDSC Paper Portfolio Summary Cards:** Total Cost Basis (NPR), Current Market Value (NPR), and Net Unrealized P&L (NPR).
* **Live CDSC Paper Holdings Table:** Active positions showing Symbol, Open Quantity (Kitta), CDSC WACC, Latest Market Price (LTP), Total Cost Basis, Current Market Value, and Unrealized Gain/Loss (NPR & %).

### Page 4: Strategy Screener & Benchmark Matrix
*Cross-sectional screener for portfolio managers to compare strategies and identify consistent performers.*
* **Top 10 Winning Stocks:** Bar chart ranking securities by winning trade frequency under the selected strategy.
* **Top 10 Losing Stocks:** Bar chart highlighting the securities that generate the highest frequency of false signals.
* **Cross-Strategy Benchmark Matrix:** Side-by-side comparison of all 4 quantitative strategies across Total Trades, Winning Trades, Losing Trades, Win Rate %, and Average Price Return % per trade.
* **Stock Win Rate % vs. Trade Frequency Scatter:** Bubble visual plotting trade frequency (X-axis) against win rate (Y-axis), with bubble size reflecting total wins, referenced against a 50% Win Rate baseline.

---

## 📊 Quantitative Strategy Benchmark Matrix

Evaluating strategies on unlevered **Price Return %** across **3,727 completed walk-forward trades** in the 2026 dataset:

| Strategy | Total Trades | Winning Trades | Losing Trades | Strategy Win Rate % | Avg Price Return % per Trade |
|---|:---:|:---:|:---:|:---:|:---:|
| **Composite Multi-Factor** | 1,512 | 457 | 1,055 | **30.22%** | **-1.12%** |
| **Candlestick Price Action** | 697 | 217 | 480 | **31.13%** | **-1.62%** |
| **Wilder's RSI Mean Reversion** | 604 | 178 | 426 | **29.47%** | **-1.24%** |
| **MACD Trend Crossover** | 914 | 247 | 667 | **27.02%** | **-1.38%** |

### Key Quant Insights:
1. **Regime Sensitivity:** In a choppy, range-bound 2026 market regime, standard momentum and crossover signals (MACD) experienced high whip-saw rates, reflecting a ~27% win rate.
2. **Selective Filtering:** The Composite Multi-Factor model, requiring price to trade above both SMA 20 and SMA 50 while confirming RSI/MACD alignment, captured higher overall trade setups while maintaining competitive average price returns.
3. **Holding Period Behavior:** RSI Mean Reversion trades required an average holding period of ~30.5 days to reach target exits, compared to 14.5 days for fast MACD crossovers.

---

## 💼 Active Paper Portfolio Ledger & CDSC WACC

While backtests focus on pure price return, the **Paper Portfolio** models real-world cash friction under the **Securities Board of Nepal (SEBON) May 2024 regulations**:

### 1. Simple CSV Ingestion (`data/paper_trades.csv`)
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

### 2. Fee Slabs & CDSC WACC Formula
For each BUY transaction, the system calculates:
* **Broker Commission (May 2024 SEBON Slabs):** `0.40%` ($\le$ 50k), `0.37%` (50k–500k), `0.34%` (500k–2M), `0.30%` (2M–10M), `0.27%` (> 10M). Minimum NPR 10.
* **SEBON Regulatory Fee:** Flat `0.015%` on transaction turnover.
* **CDSC WACC Basis:**
$$\text{WACC} = \frac{\sum (\text{Purchase Value} + \text{Broker Commission} + \text{SEBON Fee})}{\text{Total Traded Quantity}}$$
* **Live Mark-to-Market Valuation:** Queries the latest available market LTP to calculate current value and unrealized profit/loss:
$$\text{Unrealized P\&L (NPR)} = (\text{LTP} - \text{WACC}) \times \text{Open Quantity}$$

---

## 🏗️ Technical Architecture & Pipeline

```
[ Raw NEPSE Daily CSVs ] ──> [ 01_ingest_to_sql.py ] ──> [ SQLite: nepse.db ]
                                                              │
                                                              ├──> fact_daily_ohlcv
                                                              ├──> dim_company
                                                              └──> dim_calendar
                                                              │
[ 02_signal_engine.py ]  <────────────────────────────────────┘
        │
        └──> Computes 7 Vectorized Indicators & Patterns
        └──> Populates: fact_technical_signals
        │
[ 03_simple_backtester.py ] <─────────────────────────────────┘
        │
        ├──> Ingests paper_trades.csv ──> fact_paper_holdings (CDSC WACC & LTP)
        └──> Simulates 4 Strategies  ──> fact_backtest_trades (Price Return %)
        │
[ sql/02_views_powerbi.sql ] ──> Analytical Views Feeding Power BI:
        ├── vw_market_overview_latest (Page 1)
        ├── vw_deneb_candlestick (Page 2)
        ├── vw_backtest_performance (Page 3 & 4 - Price Returns)
        └── vw_paper_portfolio_holdings (Page 3 - Cash & WACC)
        │
        ▼
[ Power BI Desktop (`NEPSE_Analytics.pbix`) ]
```

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
*Total execution time: ~25 seconds.*

### 3. Open the Power BI Dashboard
* Open [`NEPSE_Analytics.pbix`](NEPSE_Analytics.pbix) in **Power BI Desktop**.
* Click **Home $\rightarrow$ Refresh** to pull the latest facts.
* If you do not have Power BI Desktop installed, review [`NEPSE_Analytics.pdf`](NEPSE_Analytics.pdf) for the full 4-page visual presentation.

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

## 👨‍💻 About the Author

**Kabindra Shrestha**  
*Data Analyst | Data Scientist | Applied AI/ML Engineer | BI & MIS Specialist*  
**MBA • BBIS • MCA (Candidate)**  
Lalitpur, Nepal

With an extensive background across banking operations, treasury MIS reporting, applied machine learning, and business intelligence, I specialize in transforming messy enterprise data systems into robust, reliable, and actionable decision-support tools.

* 💼 **LinkedIn:** [kabindra-shrestha](https://www.linkedin.com/in/kabindra-shrestha-b34542170/)
* 🌐 **Flagship Project:** [FlyRank: Enterprise Page Priority Pipeline](https://github.com/kab-s/flyrank-page-priority-pipeline)
* 🐙 **GitHub:** [@kab-s](https://github.com/kab-s)
