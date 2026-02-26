import pandas as pd

def run_simulation(df, initial_capital=100):
    """
    Runs the backtest simulation.

    Args:
        df (pd.DataFrame): DataFrame with 'Close', 'SMA50', 'SMA200'.
        initial_capital (float): Starting capital.

    Returns:
        pd.DataFrame: DataFrame with 'PortfolioValue' and 'Signal' columns.
        list: List of trades (dictionaries).
    """
    cash = float(initial_capital)
    position = 0.0 # Amount of BTC

    # Create columns to store simulation state
    df = df.copy()
    df['PortfolioValue'] = float(initial_capital)
    df['Signal'] = 0 # 1=Buy, -1=Sell, 0=Hold

    trades = []

    # Get column indices for faster/safer access
    idx_portfolio_val = df.columns.get_loc('PortfolioValue')
    idx_signal = df.columns.get_loc('Signal')

    # Iterate through the DataFrame
    # We need previous row values, so we start from index 1
    for i in range(1, len(df)):
        # Get current and previous row
        # Using iloc is safer
        prev_row = df.iloc[i-1]
        curr_row = df.iloc[i]

        # Check if indicators are not NaN
        if pd.isna(curr_row['SMA50']) or pd.isna(curr_row['SMA200']) or \
           pd.isna(prev_row['SMA50']) or pd.isna(prev_row['SMA200']):
            # Update portfolio value (price change affects holding)
            current_value = cash + position * curr_row['Close']
            df.iloc[i, idx_portfolio_val] = current_value
            continue

        # Golden Cross: SMA50 crosses above SMA200
        golden_cross = (prev_row['SMA50'] < prev_row['SMA200']) and (curr_row['SMA50'] > curr_row['SMA200'])

        # Death Cross: SMA50 crosses below SMA200
        death_cross = (prev_row['SMA50'] > prev_row['SMA200']) and (curr_row['SMA50'] < curr_row['SMA200'])

        price = curr_row['Close']

        # Execute Buy
        if golden_cross and cash > 0:
            amount = cash / price
            position = amount
            cash = 0.0
            df.iloc[i, idx_signal] = 1
            trades.append({
                'date': df.index[i],
                'type': 'BUY',
                'price': price,
                'amount': amount,
                'value': amount * price
            })

        # Execute Sell
        elif death_cross and position > 0:
            amount = position
            cash = amount * price
            position = 0.0
            df.iloc[i, idx_signal] = -1
            trades.append({
                'date': df.index[i],
                'type': 'SELL',
                'price': price,
                'amount': amount,
                'value': cash
            })

        # Update Portfolio Value
        current_value = cash + position * price
        df.iloc[i, idx_portfolio_val] = current_value

    return df, trades
