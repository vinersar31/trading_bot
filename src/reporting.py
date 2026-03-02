import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import os

def generate_report(df_sim, trades, data_dict, history=None):
    # Calculate Statistics
    initial_value = df_sim['PortfolioValue'].iloc[0]
    final_value = df_sim['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100

    cummax = df_sim['PortfolioValue'].cummax()
    drawdown = (df_sim['PortfolioValue'] - cummax) / cummax
    max_drawdown = drawdown.min() * 100

    num_trades = len(trades)

    # Win rate calculation
    win_trades = 0
    total_completed_trades = 0
    trade_profits = []

    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        if 'date' in trades_df.columns:
            trades_df['date'] = pd.to_datetime(trades_df['date'])

        for symbol in data_dict.keys():
            if 'symbol' in trades_df.columns:
                sym_trades = trades_df[trades_df['symbol'] == symbol].sort_values('date')
                buys = sym_trades[sym_trades['type'] == 'BUY']['price'].tolist()
                sells = sym_trades[sym_trades['type'] == 'SELL']['price'].tolist()

                paired = min(len(buys), len(sells))
                for i in range(paired):
                    total_completed_trades += 1
                    profit = (sells[i] - buys[i]) / buys[i]
                    trade_profits.append(profit)
                    if profit > 0:
                        win_trades += 1

    win_rate = (win_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0

    rows = 2
    row_heights = [0.6, 0.4]
    subplot_titles = ['Asset Price & Strategy', 'Backtest Portfolio Value']
    specs = [[{"type": "xy"}], [{"type": "xy"}]]

    if history:
        rows = 3
        row_heights = [0.5, 0.3, 0.2]
        subplot_titles.append('Paper Trading History')
        specs.append([{"type": "xy"}])

    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=False,
                        vertical_spacing=0.1,
                        subplot_titles=tuple(subplot_titles),
                        row_heights=row_heights,
                        specs=specs)

    symbols = list(data_dict.keys())

    for i, symbol in enumerate(symbols):
        df = data_dict[symbol]
        is_visible = (i == 0)

        # 1. Candlestick Price (fallback to line if OHLC not available in dummy data)
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            fig.add_trace(go.Candlestick(x=df.index,
                                         open=df['Open'],
                                         high=df['High'],
                                         low=df['Low'],
                                         close=df['Close'],
                                         name=f'{symbol} Price',
                                         visible=is_visible),
                          row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=f'{symbol} Price',
                                     line=dict(color='black', width=1), visible=is_visible),
                          row=1, col=1)


        # 2. SMA 50
        if 'SMA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name=f'{symbol} SMA 50',
                                     line=dict(color='orange', width=1.5), visible=is_visible),
                          row=1, col=1)

        # 3. SMA 200
        if 'SMA200' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name=f'{symbol} SMA 200',
                                     line=dict(color='blue', width=1.5), visible=is_visible),
                          row=1, col=1)

        # 4. Buy Signals
        if not trades_df.empty and 'symbol' in trades_df.columns:
            buys = trades_df[(trades_df['symbol'] == symbol) & (trades_df['type'] == 'BUY')]
            if not buys.empty:
                 fig.add_trace(go.Scatter(x=buys['date'], y=buys['price'], mode='markers',
                                         name=f'{symbol} Buy', marker=dict(symbol='triangle-up', size=12, color='green', line=dict(width=1, color='darkgreen')),
                                         visible=is_visible), row=1, col=1)

            # 5. Sell Signals
            sells = trades_df[(trades_df['symbol'] == symbol) & (trades_df['type'] == 'SELL')]
            if not sells.empty:
                 fig.add_trace(go.Scatter(x=sells['date'], y=sells['price'], mode='markers',
                                         name=f'{symbol} Sell', marker=dict(symbol='triangle-down', size=12, color='red', line=dict(width=1, color='darkred')),
                                         visible=is_visible), row=1, col=1)

    # --- Row 2: Backtest Portfolio Value ---
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim['PortfolioValue'], name='Backtest Value',
                             line=dict(color='purple', width=2), visible=True, fill='tozeroy', fillcolor='rgba(128, 0, 128, 0.1)'), row=2, col=1)

    # --- Row 3: Paper Trading History (if available) ---
    if history:
        hist_df = pd.DataFrame(history)
        if not hist_df.empty and 'date' in hist_df.columns and 'value' in hist_df.columns:
            hist_df['date'] = pd.to_datetime(hist_df['date'])
            fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['value'], name='Paper Value',
                                     line=dict(color='green', width=2, dash='dot'), visible=True), row=3, col=1)

    # Build Asset Dropdown
    buttons_asset = []
    for symbol in symbols:
        visibility = []
        for trace in fig.data:
            if trace.name and trace.name.startswith(symbol) and any(x in trace.name for x in ['Price', 'SMA', 'Buy', 'Sell']):
                visibility.append(True)
            elif trace.name and (trace.name == 'Backtest Value' or trace.name == 'Paper Value'):
                visibility.append(True)
            elif trace.name and any(x in trace.name for x in ['Price', 'SMA', 'Buy', 'Sell']):
                visibility.append(False)
            else:
                visibility.append(True)

        buttons_asset.append(dict(label=f"Asset: {symbol}",
                            method="update",
                            args=[{"visible": visibility}]))

    # Build Theme Dropdown
    buttons_theme = [
        dict(label="Dark Mode", method="relayout", args=[{"template": "plotly_dark"}]),
        dict(label="Light Mode", method="relayout", args=[{"template": "plotly_white"}])
    ]

    dashboard_title = (
        f"<b>Multi-Asset Trading Bot Dashboard</b><br><br>"
        f"<span style='font-size: 14px'>"
        f"<b>Initial Capital:</b> ${initial_value:,.2f}  |  <b>Final Value:</b> ${final_value:,.2f}  |  "
        f"<b>Total Return:</b> <span style='color:{'green' if total_return >= 0 else 'red'}'>{total_return:,.2f}%</span>  |  "
        f"<b>Max Drawdown:</b> <span style='color:red'>{max_drawdown:,.2f}%</span>  |  "
        f"<b>Total Trades:</b> {num_trades}  |  "
        f"<b>Win Rate:</b> {win_rate:.1f}% ({win_trades}/{total_completed_trades} trades)"
        f"</span>"
    )

    fig.update_layout(
        title_text=dashboard_title,
        title_x=0.5,
        title_y=0.95,
        margin=dict(t=120),
        updatemenus=[
            dict(
                active=0,
                buttons=buttons_asset,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.1,
                yanchor="top",
            ),
            dict(
                active=0,
                buttons=buttons_theme,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.15,
                xanchor="left",
                y=1.1,
                yanchor="top",
            ),
        ],
        height=1000 if history else 850,
        template="plotly_dark",
        hovermode="x unified"
    )

    fig.update_xaxes(rangeslider_visible=False)


    # Create output directory if it doesn't exist
    out_dir = "frontend/public"
    os.makedirs(out_dir, exist_ok=True)

    # Write the chart JSON
    fig.write_json(os.path.join(out_dir, "chart.json"))

    # Write the stats JSON
    stats = {
        "initialValue": float(initial_value),
        "finalValue": float(final_value),
        "totalReturn": float(total_return),
        "maxDrawdown": float(max_drawdown),
        "numTrades": int(num_trades),
        "winRate": float(win_rate),
        "winTrades": int(win_trades),
        "totalCompletedTrades": int(total_completed_trades)
    }
    with open(os.path.join(out_dir, "stats.json"), "w") as f:
        json.dump(stats, f)

    print(f"Report JSONs generated in {out_dir}")
