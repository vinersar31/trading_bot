import yfinance as yf
import pandas as pd

def fetch_data(symbols, period='2y'):
    """
    Fetches historical data for a list of symbols or a single symbol.

    Args:
        symbols (str or list): Single symbol string or list of symbol strings.
        period (str): Data period to fetch.

    Returns:
        dict: Dictionary of {symbol: DataFrame}
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    data_dict = {}

    for symbol in symbols:
        try:
            # progress=False to avoid printing progress bars to stdout
            # For multiple tickers, yf.download works best with a list and group_by='ticker'
            # But here we loop for simplicity and robustness with single requests
            df = yf.download(symbol, period=period, progress=False)

            if df.empty:
                print(f"Warning: No data found for {symbol}")
                continue

            # Flatten MultiIndex columns if present (common in newer yfinance versions)
            # If result is single ticker, yfinance returns 'Open', 'High', etc.
            # If result is multi ticker, it returns MultiIndex columns.

            # Since we download one by one in loop, we expect simple columns
            # BUT sometimes yfinance wraps single ticker result too.
            if isinstance(df.columns, pd.MultiIndex):
                # Try to drop the ticker level if it exists
                # e.g., columns are (Price, Ticker)
                try:
                    df.columns = df.columns.droplevel(1)
                except:
                    pass

            # Validate required columns
            if 'Close' not in df.columns:
                 # specific to some yfinance versions returning 'Adj Close' only?
                 # Or just structure issue.
                 pass

            data_dict[symbol] = df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    return data_dict

def calculate_indicators(df):
    """Calculates SMA50 and SMA200 indicators for a DataFrame."""
    if df.empty:
        return df

    # Ensure we are working with a copy to avoid SettingWithCopyWarning
    df = df.copy()

    # Calculate Simple Moving Averages
    # Check if 'Close' is present
    if 'Close' in df.columns:
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()

    return df

def get_technical_signal(row):
    """
    Determines the technical signal based on SMAs from a single row (Series).

    Args:
        row (pd.Series): A row from the DataFrame containing SMA50 and SMA200.

    Returns:
        int: 1 (Bullish State), -1 (Bearish State), 0 (Neutral/Indeterminate)
    """
    if pd.isna(row.get('SMA50')) or pd.isna(row.get('SMA200')):
        return 0

    if row['SMA50'] > row['SMA200']:
        return 1
    elif row['SMA50'] < row['SMA200']:
        return -1
    else:
        return 0
