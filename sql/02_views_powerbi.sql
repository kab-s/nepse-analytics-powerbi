-- 1. Latest Market Overview & Daily Movers View
DROP VIEW IF EXISTS vw_market_overview_latest;
CREATE VIEW vw_market_overview_latest AS
WITH latest_date AS (
    SELECT MAX(trade_date) AS max_dt FROM fact_daily_ohlcv
)
SELECT 
    o.trade_date,
    o.symbol,
    c.company_name,
    o.open_price,
    o.high_price,
    o.low_price,
    o.close_price,
    ROUND(((o.close_price - o.open_price) / o.open_price) * 100, 2) AS daily_change_pct,
    o.volume,
    o.turnover,
    o.transactions,
    s.rsi_14,
    s.candle_pattern,
    s.signal_decision
FROM fact_daily_ohlcv o
JOIN dim_company c ON o.symbol = c.symbol
JOIN latest_date ld ON o.trade_date = ld.max_dt
LEFT JOIN fact_technical_signals s 
       ON o.trade_date = s.trade_date AND o.symbol = s.symbol;

-- 2. Technical Candlestick & Signal View (For Deneb Vega-Lite Terminal)
DROP VIEW IF EXISTS vw_deneb_candlestick;
CREATE VIEW vw_deneb_candlestick AS
SELECT 
    o.trade_date,
    o.symbol,
    o.open_price,
    o.high_price,
    o.low_price,
    o.close_price,
    o.volume,
    s.sma_20,
    s.sma_50,
    s.bb_upper,
    s.bb_lower,
    s.rsi_14,
    s.macd_line,
    s.macd_signal,
    s.macd_hist,
    s.candle_pattern,
    s.signal_decision,
    -- Signal triggers for Vega-Lite triangle markers
    CASE WHEN s.signal_decision = 'BUY' THEN o.low_price * 0.985 ELSE NULL END AS buy_marker_price,
    CASE WHEN s.signal_decision = 'SELL' THEN o.high_price * 1.015 ELSE NULL END AS sell_marker_price
FROM fact_daily_ohlcv o
LEFT JOIN fact_technical_signals s 
       ON o.trade_date = s.trade_date AND o.symbol = s.symbol;

-- 3. Backtest Trade Performance & Fee Drag Breakdown (Multi-Strategy & Price Return Aware)
DROP VIEW IF EXISTS vw_backtest_performance;
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

-- 4. Paper Trading Live Holdings View (CDSC WACC Basis & Live LTP)
DROP VIEW IF EXISTS vw_paper_portfolio_holdings;
CREATE VIEW vw_paper_portfolio_holdings AS
SELECT 
    symbol,
    open_kitta,
    wacc,
    ltp,
    cost_basis,
    current_value,
    unrealized_pnl,
    return_pct
FROM fact_paper_holdings;
