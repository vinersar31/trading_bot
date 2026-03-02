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
    """Calculates SMA50, SMA200, RSI, MACD, and StochRSI indicators for a DataFrame."""
    if df.empty:
        return df

    # Ensure we are working with a copy to avoid SettingWithCopyWarning
    df = df.copy()

    if 'Close' in df.columns:
        close = df['Close']

        # Simple Moving Averages
        df['SMA50'] = close.rolling(window=50).mean()
        df['SMA200'] = close.rolling(window=200).mean()

        # Relative Strength Index (RSI) - 14 period
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD - 12, 26, 9
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Stochastic RSI - 14 period, 3 period K, 3 period D
        rsi_min = df['RSI'].rolling(window=14).min()
        rsi_max = df['RSI'].rolling(window=14).max()
        df['StochRSI'] = (df['RSI'] - rsi_min) / (rsi_max - rsi_min)
        df['StochRSI_K'] = df['StochRSI'].rolling(window=3).mean()
        df['StochRSI_D'] = df['StochRSI_K'].rolling(window=3).mean()

    return df

def get_technical_signal(row):
    """
    Determines the technical signal based on multiple indicators from a single row (Series).
    Uses a composite score from SMA, MACD, RSI, and StochRSI.

    Args:
        row (pd.Series): A row from the DataFrame containing technical indicators.

    Returns:
        int: 1 (Bullish State), -1 (Bearish State), 0 (Neutral/Indeterminate)
    """
    score = 0

    # 1. SMA
    if not pd.isna(row.get('SMA50')) and not pd.isna(row.get('SMA200')):
        if row['SMA50'] > row['SMA200']:
            score += 1
        elif row['SMA50'] < row['SMA200']:
            score -= 1

    # 2. MACD
    if not pd.isna(row.get('MACD')) and not pd.isna(row.get('MACD_Signal')):
        if row['MACD'] > row['MACD_Signal']:
            score += 1
        elif row['MACD'] < row['MACD_Signal']:
            score -= 1

    # 3. RSI
    if not pd.isna(row.get('RSI')):
        if row['RSI'] < 30: # Oversold - Bullish potential
            score += 1
        elif row['RSI'] > 70: # Overbought - Bearish potential
            score -= 1

    # 4. StochRSI
    if not pd.isna(row.get('StochRSI_K')) and not pd.isna(row.get('StochRSI_D')):
        if row['StochRSI_K'] > row['StochRSI_D']:
            score += 1
        elif row['StochRSI_K'] < row['StochRSI_D']:
            score -= 1

    if score > 0:
        return 1
    elif score < 0:
        return -1
    else:
        return 0
