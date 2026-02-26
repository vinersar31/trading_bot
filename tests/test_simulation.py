import pandas as pd
import numpy as np
import pytest
from src.strategy import calculate_indicators
from src.backtest import run_simulation

def test_calculate_indicators():
    # Create random data
    dates = pd.date_range(start='2020-01-01', periods=300, freq='D')
    df = pd.DataFrame({'Close': np.random.rand(300) * 100}, index=dates)

    df_ind = calculate_indicators(df)

    assert 'SMA50' in df_ind.columns
    assert 'SMA200' in df_ind.columns

    # Check first 49 values are NaN for SMA50
    assert pd.isna(df_ind['SMA50'].iloc[48])
    assert not pd.isna(df_ind['SMA50'].iloc[49])

    # Check first 199 values are NaN for SMA200
    assert pd.isna(df_ind['SMA200'].iloc[198])
    assert not pd.isna(df_ind['SMA200'].iloc[199])

def test_backtest_logic():
    # Setup Data
    dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
    df = pd.DataFrame({
        'Close': [100, 110, 120, 130, 140, 130, 120, 110, 100, 90],
    }, index=dates)

    # Add dummy SMAs
    # Day 0: 50, 60
    # ...
    # Day 3: 60, 50 (Golden Cross) -> Buy at 130
    # ...
    # Day 8: 50, 60 (Death Cross) -> Sell at 100
    df['SMA50'] = [50, 50, 50, 60, 70, 70, 70, 60, 50, 40]
    df['SMA200'] = [60, 60, 60, 50, 40, 40, 40, 50, 60, 70]

    # Run Simulation
    df_res, trades = run_simulation(df, initial_capital=100)

    assert len(trades) == 2

    # Check Buy Trade
    buy_trade = trades[0]
    assert buy_trade['type'] == 'BUY'
    assert buy_trade['price'] == 130
    # Use to_datetime to ensure correct comparison
    assert pd.to_datetime(buy_trade['date']) == pd.to_datetime('2020-01-04')

    # Check Sell Trade
    sell_trade = trades[1]
    assert sell_trade['type'] == 'SELL'
    assert sell_trade['price'] == 100
    assert pd.to_datetime(sell_trade['date']) == pd.to_datetime('2020-01-09')

    # Check Portfolio Value at end
    # Buy at 130, Sell at 100. Loss ~23%.
    expected_value = 100 * (100/130)
    final_value = df_res['PortfolioValue'].iloc[-1]

    # Allow small float error
    assert abs(final_value - expected_value) < 1e-6
