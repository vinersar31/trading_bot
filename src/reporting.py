import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def generate_report(df, trades):
    """
    Generates an HTML report with plots and statistics.

    Args:
        df (pd.DataFrame): Simulation result DataFrame.
        trades (list): List of trades.
    """
    # Calculate Statistics
    initial_value = df['PortfolioValue'].iloc[0]
    final_value = df['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100

    # Max Drawdown
    cummax = df['PortfolioValue'].cummax()
    drawdown = (df['PortfolioValue'] - cummax) / cummax
    max_drawdown = drawdown.min() * 100

    num_trades = len(trades)

    # Create Figure with 2 subplots
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=('BTC Price & Strategy', 'Portfolio Value'),
                        row_heights=[0.7, 0.3])

    # 1. Price Chart
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='BTC Price', line=dict(color='black', width=1)), row=1, col=1)

    if 'SMA50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='SMA 50', line=dict(color='orange', width=1)), row=1, col=1)

    if 'SMA200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name='SMA 200', line=dict(color='blue', width=1)), row=1, col=1)

    # Buy/Sell Markers
    buy_signals = df[df['Signal'] == 1]
    sell_signals = df[df['Signal'] == -1]

    if not buy_signals.empty:
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers',
                                 marker=dict(symbol='triangle-up', color='green', size=12), name='Buy Signal'), row=1, col=1)

    if not sell_signals.empty:
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers',
                                 marker=dict(symbol='triangle-down', color='red', size=12), name='Sell Signal'), row=1, col=1)

    # 2. Portfolio Value
    fig.add_trace(go.Scatter(x=df.index, y=df['PortfolioValue'], name='Portfolio Value', line=dict(color='purple', width=2)), row=2, col=1)

    # Update Layout
    fig.update_layout(title_text=f"Bitcoin Golden Cross Strategy Simulation<br>Total Return: {total_return:.2f}% | Max Drawdown: {max_drawdown:.2f}% | Trades: {num_trades}",
                      height=800,
                      template="plotly_white")

    # Add stats box as annotation if needed, but title is fine for now.

    # Save to HTML
    fig.write_html("index.html")
    print("Report generated: index.html")
