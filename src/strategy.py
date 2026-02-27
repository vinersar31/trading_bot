import yfinance as yf
import pandas as pd

def fetch_data(symbol='BTC-USD', period='2y'):
    """Fetches historical data for a given symbol."""
    try:
        # progress=False to avoid printing progress bars to stdout
        df = yf.download(symbol, period=period, progress=False)
        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Flatten MultiIndex columns if present (common in newer yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    """Calculates SMA50 and SMA200 indicators."""
    if df.empty:
        return df

    # Ensure we are working with a copy to avoid SettingWithCopyWarning
    df = df.copy()

    # Calculate Simple Moving Averages
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    return df
