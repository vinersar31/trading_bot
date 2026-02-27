import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def generate_report(df_sim, trades, data_dict, history=None):
    """
    Generates an HTML report with plots and statistics for multi-asset simulation.

    Args:
        df_sim (pd.DataFrame): Simulation result DataFrame with 'PortfolioValue'.
        trades (list): List of trades.
        data_dict (dict): Dictionary of {symbol: DataFrame} with 'Close', 'SMA50', 'SMA200'.
        history (list, optional): List of paper trading history dictionaries.
    """
    # Calculate Statistics
    initial_value = df_sim['PortfolioValue'].iloc[0]
    final_value = df_sim['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100

    # Max Drawdown
    cummax = df_sim['PortfolioValue'].cummax()
    drawdown = (df_sim['PortfolioValue'] - cummax) / cummax
    max_drawdown = drawdown.min() * 100

    num_trades = len(trades)

    # Determine rows and heights
    rows = 2
    row_heights = [0.6, 0.4]
    subplot_titles = ['Asset Price & Strategy', 'Backtest Portfolio Value']
    specs = [[{"type": "xy"}], [{"type": "xy"}]]

    if history:
        rows = 3
        row_heights = [0.5, 0.3, 0.2]
        subplot_titles.append('Paper Trading History')
        specs.append([{"type": "xy"}])

    # Create Figure
    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=False,
                        vertical_spacing=0.1,
                        subplot_titles=tuple(subplot_titles),
                        row_heights=row_heights,
                        specs=specs)

    # Convert trades list to DataFrame for easier filtering
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        if 'date' in trades_df.columns:
            trades_df['date'] = pd.to_datetime(trades_df['date'])

    # --- Row 1: Asset Strategy with Dropdown ---
    symbols = list(data_dict.keys())

    for i, symbol in enumerate(symbols):
        df = data_dict[symbol]

        # Visibility: Only first symbol is visible initially
        is_visible = (i == 0)

        # 1. Price
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=f'{symbol} Price',
                                 line=dict(color='black', width=1), visible=is_visible),
                      row=1, col=1)

        # 2. SMA 50
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name=f'{symbol} SMA 50',
                                 line=dict(color='orange', width=1), visible=is_visible),
                      row=1, col=1)

        # 3. SMA 200
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name=f'{symbol} SMA 200',
                                 line=dict(color='blue', width=1), visible=is_visible),
                      row=1, col=1)

        # 4. Buy Signals
        if not trades_df.empty and 'symbol' in trades_df.columns:
            buys = trades_df[(trades_df['symbol'] == symbol) & (trades_df['type'] == 'BUY')]
            if not buys.empty:
                 fig.add_trace(go.Scatter(x=buys['date'], y=buys['price'], mode='markers',
                                         name=f'{symbol} Buy', marker=dict(symbol='triangle-up', size=10, color='green'),
                                         visible=is_visible), row=1, col=1)

            # 5. Sell Signals
            sells = trades_df[(trades_df['symbol'] == symbol) & (trades_df['type'] == 'SELL')]
            if not sells.empty:
                 fig.add_trace(go.Scatter(x=sells['date'], y=sells['price'], mode='markers',
                                         name=f'{symbol} Sell', marker=dict(symbol='triangle-down', size=10, color='red'),
                                         visible=is_visible), row=1, col=1)

    # --- Row 2: Backtest Portfolio Value ---
    # This trace should always be visible
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim['PortfolioValue'], name='Backtest Value',
                             line=dict(color='purple', width=2), visible=True), row=2, col=1)

    # --- Row 3: Paper Trading History (if available) ---
    if history:
        hist_df = pd.DataFrame(history)
        if not hist_df.empty and 'date' in hist_df.columns and 'value' in hist_df.columns:
            hist_df['date'] = pd.to_datetime(hist_df['date'])
            fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['value'], name='Paper Value',
                                     line=dict(color='green', width=2, dash='dot'), visible=True), row=3, col=1)


    # --- Create Dropdown Menus ---
    buttons = []

    for symbol in symbols:
        # Construct visibility vector for this symbol
        visibility = []
        for trace in fig.data:
            # Check if trace belongs to this symbol (Strategy traces)
            # Use 'Price', 'SMA', 'Buy', 'Sell' keywords along with symbol name
            # Note: We used f'{symbol} ...' for names.
            if trace.name and trace.name.startswith(symbol) and any(x in trace.name for x in ['Price', 'SMA', 'Buy', 'Sell']):
                visibility.append(True)
            elif trace.name and (trace.name == 'Backtest Value' or trace.name == 'Paper Value'):
                 # These should always be visible
                 visibility.append(True)
            elif trace.name and any(x in trace.name for x in ['Price', 'SMA', 'Buy', 'Sell']):
                # Belongs to another symbol's strategy
                visibility.append(False)
            else:
                # Fallback, maybe shouldn't happen based on our code, but keep visible if unknown?
                # Actually safest is to hide unless we explicitly know it's shared.
                # But here we covered all cases.
                visibility.append(True)

        buttons.append(dict(label=symbol,
                            method="update",
                            args=[{"visible": visibility},
                                  {"title": f"Multi-Asset Trading Bot Simulation - {symbol}<br>Total Return: {total_return:.2f}% | Max Drawdown: {max_drawdown:.2f}% | Trades: {num_trades}"}]))

    # Update Layout with Menus
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ],
        title_text=f"Multi-Asset Trading Bot Simulation - {symbols[0]}<br>Total Return: {total_return:.2f}% | Max Drawdown: {max_drawdown:.2f}% | Trades: {num_trades}",
        height=1000 if history else 800,
        template="plotly_white"
    )

    # Save to HTML
    fig.write_html("index.html")
    print("Report generated: index.html")
