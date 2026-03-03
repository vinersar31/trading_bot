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
    prev_indicators = {} # {symbol: (sma50, sma200, macd, macd_signal, rsi, stoch_k, stoch_d)}

    for i, current_date in enumerate(all_dates):
        current_portfolio_value = cash

        # 1. Update Portfolio Value based on current holdings and prices
        for symbol, df in aligned_data.items():
            try:
                curr_row = df.iloc[i]
                price = curr_row['Close']

                if pd.isna(price):
                    continue

                holding_qty = holdings[symbol]
                current_portfolio_value += holding_qty * price

            except Exception:
                continue

        sim_df.iloc[i, sim_df.columns.get_loc('PortfolioValue')] = current_portfolio_value

        # 2. Check Signals and Trade
        buy_signals = []
        sell_signals = []

        current_prices_map = {}

        for symbol, df in aligned_data.items():
            curr_row = df.iloc[i]

            # Skip if essential data missing
            if pd.isna(curr_row['Close']):
                continue

            price = curr_row['Close']
            current_prices_map[symbol] = price

            # We need previous day's data for this symbol
            prev_ind = prev_indicators.get(symbol)
            if prev_ind is None:
                # Initialize
                prev_indicators[symbol] = (
                    curr_row.get('SMA50'), curr_row.get('SMA200'),
                    curr_row.get('MACD'), curr_row.get('MACD_Signal'),
                    curr_row.get('RSI'), curr_row.get('StochRSI_K'), curr_row.get('StochRSI_D')
                )
                continue

            # Unpack previous
            p_sma50, p_sma200, p_macd, p_macd_sig, p_rsi, p_stoch_k, p_stoch_d = prev_ind

            # Get current
            c_sma50, c_sma200 = curr_row.get('SMA50'), curr_row.get('SMA200')
            c_macd, c_macd_sig = curr_row.get('MACD'), curr_row.get('MACD_Signal')
            c_rsi = curr_row.get('RSI')
            c_stoch_k, c_stoch_d = curr_row.get('StochRSI_K'), curr_row.get('StochRSI_D')

            # Update for next loop
            prev_indicators[symbol] = (c_sma50, c_sma200, c_macd, c_macd_sig, c_rsi, c_stoch_k, c_stoch_d)

            # Evaluate Signals
            is_buy = False
            is_sell = False

            # SMA Cross
            if not pd.isna(p_sma50) and not pd.isna(p_sma200) and not pd.isna(c_sma50) and not pd.isna(c_sma200):
                if p_sma50 < p_sma200 and c_sma50 > c_sma200:
                    is_buy = True
                elif p_sma50 > p_sma200 and c_sma50 < c_sma200:
                    is_sell = True

            # MACD Cross
            if not pd.isna(p_macd) and not pd.isna(p_macd_sig) and not pd.isna(c_macd) and not pd.isna(c_macd_sig):
                if p_macd < p_macd_sig and c_macd > c_macd_sig:
                    is_buy = True
                elif p_macd > p_macd_sig and c_macd < c_macd_sig:
                    is_sell = True

            # RSI Cross 30/70
            if not pd.isna(p_rsi) and not pd.isna(c_rsi):
                if p_rsi < 30 and c_rsi >= 30: # Crossing up from oversold
                    is_buy = True
                elif p_rsi > 70 and c_rsi <= 70: # Crossing down from overbought
                    is_sell = True

            # StochRSI Cross
            if not pd.isna(p_stoch_k) and not pd.isna(p_stoch_d) and not pd.isna(c_stoch_k) and not pd.isna(c_stoch_d):
                if p_stoch_k < p_stoch_d and c_stoch_k > c_stoch_d:
                     is_buy = True
                elif p_stoch_k > p_stoch_d and c_stoch_k < c_stoch_d:
                     is_sell = True

            if is_buy and not is_sell:
                buy_signals.append(symbol)
            elif is_sell and not is_buy:
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
