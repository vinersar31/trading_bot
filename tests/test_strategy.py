import pandas as pd
import numpy as np
from src.strategy import get_technical_signal

def test_get_technical_signal_all_bullish():
    row = pd.Series({
        'SMA50': 60, 'SMA200': 50,
        'MACD': 1.5, 'MACD_Signal': 1.0,
        'RSI': 25,  # Oversold (<30) -> Bullish
        'StochRSI_K': 0.8, 'StochRSI_D': 0.6
    })
    # SMA: +1, MACD: +1, RSI: +1, Stoch: +1 => score = 4 -> 1
    assert get_technical_signal(row) == 1

def test_get_technical_signal_all_bearish():
    row = pd.Series({
        'SMA50': 50, 'SMA200': 60,
        'MACD': 1.0, 'MACD_Signal': 1.5,
        'RSI': 75,  # Overbought (>70) -> Bearish
        'StochRSI_K': 0.6, 'StochRSI_D': 0.8
    })
    # SMA: -1, MACD: -1, RSI: -1, Stoch: -1 => score = -4 -> -1
    assert get_technical_signal(row) == -1

def test_get_technical_signal_mixed():
    row = pd.Series({
        'SMA50': 60, 'SMA200': 50,  # +1
        'MACD': 1.0, 'MACD_Signal': 1.5,  # -1
        'RSI': 50,  # 0
        'StochRSI_K': 0.8, 'StochRSI_D': 0.6  # +1
    })
    # Total score = 1 -> 1
    assert get_technical_signal(row) == 1

def test_get_technical_signal_neutral():
    row = pd.Series({
        'SMA50': 60, 'SMA200': 50,  # +1
        'MACD': 1.0, 'MACD_Signal': 1.5,  # -1
        'RSI': 50,  # 0
        'StochRSI_K': 0.6, 'StochRSI_D': 0.8  # -1
    })
    # Total score = -1 -> -1
    assert get_technical_signal(row) == -1

    row2 = pd.Series({
        'SMA50': 50, 'SMA200': 50,  # 0
        'MACD': 1.0, 'MACD_Signal': 1.0,  # 0
        'RSI': 50,  # 0
        'StochRSI_K': 0.6, 'StochRSI_D': 0.6  # 0
    })
    # Total score = 0 -> 0
    assert get_technical_signal(row2) == 0

def test_get_technical_signal_missing_data():
    row = pd.Series({
        'SMA50': np.nan, 'SMA200': 50,
        'MACD': 1.5, 'MACD_Signal': np.nan,
        'RSI': 25,
        'StochRSI_K': 0.8, 'StochRSI_D': np.nan
    })
    # SMA: 0, MACD: 0, RSI: +1, Stoch: 0 => score = 1 -> 1
    assert get_technical_signal(row) == 1

    row2 = pd.Series({
        'SMA50': np.nan, 'SMA200': np.nan,
        'MACD': np.nan, 'MACD_Signal': np.nan,
        'RSI': np.nan,
        'StochRSI_K': np.nan, 'StochRSI_D': np.nan
    })
    # All 0 => score = 0 -> 0
    assert get_technical_signal(row2) == 0
