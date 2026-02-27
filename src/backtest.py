import pandas as pd

def run_simulation(data_dict, initial_capital=100.0):
    """
    Runs the backtest simulation for multiple assets.

    Args:
        data_dict (dict): Dictionary of {symbol: DataFrame} with 'Close', 'SMA50', 'SMA200'.
        initial_capital (float): Starting capital in USD.

    Returns:
        pd.DataFrame: Simulation portfolio value over time.
        list: List of trades (dictionaries).
    """
    cash = float(initial_capital)

    # Holdings: { 'BTC-USD': 0.0, 'NVDA': 0.0 }
    holdings = {symbol: 0.0 for symbol in data_dict.keys()}

    # Combine date indices from all assets to get the simulation timeline
    # Use the intersection of dates where we have data for all, or union?
    # Intersection is safer for comparative strategy, Union handles sparse data.
    # Let's use Union of all indices and forward fill price data for missing days (weekend vs 24/7 crypto)

    all_dates = pd.DatetimeIndex([])
    for df in data_dict.values():
        all_dates = all_dates.union(df.index)

    all_dates = all_dates.sort_values()

    # Create result DataFrame
    sim_df = pd.DataFrame(index=all_dates)
    sim_df['PortfolioValue'] = float(initial_capital)

    trades = []

    # To simulate day-by-day, we iterate through the dates
    # We need to access data for each symbol at that date

    # Optimize access by reindexing all DFs to the common index once
    aligned_data = {}
    for symbol, df in data_dict.items():
        # Forward fill prices to handle holidays/weekends for stocks when crypto trades
        aligned_data[symbol] = df.reindex(all_dates).ffill()

    # Pre-calculate signals could be faster, but let's stick to loop for clarity/logic match

    # Iterate
    prev_prices = {}
    prev_smas = {} # {symbol: (sma50, sma200)}

    for i, current_date in enumerate(all_dates):
        current_portfolio_value = cash

        # 1. Update Portfolio Value based on current holdings and prices
        for symbol, df in aligned_data.items():
            try:
                # Use .loc for safety with datetime index
                # .iloc[i] is faster if we are sure of alignment, which we are
                curr_row = df.iloc[i]
                price = curr_row['Close']

                if pd.isna(price):
                    # Should be handled by ffill, but check
                    continue

                holding_qty = holdings[symbol]
                current_portfolio_value += holding_qty * price

            except Exception:
                continue

        sim_df.iloc[i, sim_df.columns.get_loc('PortfolioValue')] = current_portfolio_value

        # 2. Check Signals and Trade
        # Strategy:
        # - Allocate equal capital to each asset if cash is available?
        # - Or just buy/sell independently based on available cash pool?
        # Simple Logic:
        # - If Buy Signal and Cash > 0: Buy with 100% of available cash / num_assets_with_signal?
        # - Let's simplify: Buy with 100% cash if only 1 signal. If multiple, split.
        # - Or simpler: Fixed allocation per trade?
        # - Let's use: Buy with all available cash for the first signal found (greedy).
        #   (Better: split cash among active buy signals this turn).

        buy_signals = []
        sell_signals = []

        current_prices_map = {}

        for symbol, df in aligned_data.items():
            curr_row = df.iloc[i]

            # Skip if data missing
            if pd.isna(curr_row['Close']) or pd.isna(curr_row['SMA50']) or pd.isna(curr_row['SMA200']):
                continue

            price = curr_row['Close']
            current_prices_map[symbol] = price

            # Check Cross
            # We need previous day's data for this symbol
            # We can use the 'prev_smas' dict we maintain

            prev_sma = prev_smas.get(symbol)
            if prev_sma is None:
                # Initialize
                prev_smas[symbol] = (curr_row['SMA50'], curr_row['SMA200'])
                continue

            prev_sma50, prev_sma200 = prev_sma
            curr_sma50, curr_sma200 = curr_row['SMA50'], curr_row['SMA200']

            # Update for next loop
            prev_smas[symbol] = (curr_sma50, curr_sma200)

            if pd.isna(prev_sma50) or pd.isna(prev_sma200) or pd.isna(curr_sma50) or pd.isna(curr_sma200):
                continue

            # Golden Cross
            if prev_sma50 < prev_sma200 and curr_sma50 > curr_sma200:
                buy_signals.append(symbol)

            # Death Cross
            elif prev_sma50 > prev_sma200 and curr_sma50 < curr_sma200:
                sell_signals.append(symbol)

        # Execute Sells First (to free up cash)
        for symbol in sell_signals:
            qty = holdings[symbol]
            if qty > 0:
                price = current_prices_map[symbol]
                proceeds = qty * price
                cash += proceeds
                holdings[symbol] = 0.0

                trades.append({
                    'date': current_date,
                    'type': 'SELL',
                    'symbol': symbol,
                    'price': price,
                    'amount': qty,
                    'value': proceeds
                })

        # Execute Buys
        if buy_signals and cash > 1.0: # Minimum cash to bother
            # Split cash equally among buy signals
            amount_per_trade = cash / len(buy_signals)

            for symbol in buy_signals:
                price = current_prices_map[symbol]
                qty = amount_per_trade / price
                holdings[symbol] += qty
                cash -= amount_per_trade

                trades.append({
                    'date': current_date,
                    'type': 'BUY',
                    'symbol': symbol,
                    'price': price,
                    'amount': qty,
                    'value': amount_per_trade
                })

    return sim_df, trades
