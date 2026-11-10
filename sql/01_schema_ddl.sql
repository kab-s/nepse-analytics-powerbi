-- 1. Dim Company (Purely verified symbols & registered company names)
CREATE TABLE IF NOT EXISTS dim_company (
    symbol TEXT PRIMARY KEY,
    company_name TEXT
);

-- 2. Dim Calendar (Enables clean time-intelligence in Power BI DAX)
CREATE TABLE IF NOT EXISTS dim_calendar (
    trade_date DATE PRIMARY KEY,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day_name TEXT,
    is_trading_day BOOLEAN DEFAULT 1
);

-- 3. Fact Daily OHLCV (Core historical and daily market prices)
CREATE TABLE IF NOT EXISTS fact_daily_ohlcv (
    trade_date DATE,
    symbol TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    turnover REAL,
    transactions INTEGER,
    PRIMARY KEY (trade_date, symbol),
    FOREIGN KEY (trade_date) REFERENCES dim_calendar(trade_date),
    FOREIGN KEY (symbol) REFERENCES dim_company(symbol)
);

-- 4. Fact Technical Signals (Populated by Module 02)
CREATE TABLE IF NOT EXISTS fact_technical_signals (
    trade_date DATE,
    symbol TEXT,
    close_price REAL,
    sma_20 REAL,
    sma_50 REAL,
    rsi_14 REAL,
    macd_line REAL,
    macd_signal REAL,
    macd_hist REAL,
    bb_upper REAL,
    bb_lower REAL,
    candle_pattern TEXT,
    signal_decision TEXT, -- 'BUY', 'SELL', 'HOLD'
    PRIMARY KEY (trade_date, symbol),
    FOREIGN KEY (trade_date) REFERENCES dim_calendar(trade_date),
    FOREIGN KEY (symbol) REFERENCES dim_company(symbol)
);

-- 5. Fact Paper Portfolio (Dual-book tracking)
CREATE TABLE IF NOT EXISTS fact_paper_portfolio (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE,
    symbol TEXT,
    trade_type TEXT,          -- 'BUY', 'SELL'
    quantity INTEGER,
    execution_price REAL,
    broker_comm REAL,
    sebon_fee REAL,
    dp_fee REAL DEFAULT 25.0,
    portfolio_mode TEXT DEFAULT 'PAPER_TRADING'
);

-- 6. Fact Paper Holdings (CDSC WACC mark-to-market live positions)
CREATE TABLE IF NOT EXISTS fact_paper_holdings (
    symbol TEXT PRIMARY KEY,
    open_kitta INTEGER,
    wacc REAL,
    ltp REAL,
    cost_basis REAL,
    current_value REAL,
    unrealized_pnl REAL,
    return_pct REAL
);

-- 7. Fact Backtest Trades (Multi-strategy walk-forward simulation results)
CREATE TABLE IF NOT EXISTS fact_backtest_trades (
    strategy_name TEXT,
    symbol TEXT,
    entry_date DATE,
    exit_date DATE,
    holding_days INTEGER,
    qty INTEGER,
    entry_price REAL,
    exit_price REAL,
    price_return_pct REAL,
    total_fees REAL,
    cgt_tax REAL,
    net_pnl REAL,
    net_return_pct REAL,
    is_win INTEGER
);

-- Query Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON fact_daily_ohlcv(trade_date);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol ON fact_daily_ohlcv(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_date ON fact_technical_signals(trade_date);
CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON fact_backtest_trades(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_exit ON fact_backtest_trades(exit_date);