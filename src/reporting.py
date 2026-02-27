import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def generate_report(df, trades, history=None):
    """
    Generates an HTML report with plots and statistics.

    Args:
        df (pd.DataFrame): Simulation result DataFrame.
        trades (list): List of trades.
        history (list, optional): List of paper trading history dictionaries.
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

    # Determine rows and heights
    rows = 2
    row_heights = [0.7, 0.3]
    subplot_titles = ('BTC Price & Strategy', 'Backtest Portfolio Value')

    if history:
        rows = 3
        row_heights = [0.5, 0.25, 0.25]
        subplot_titles = ('BTC Price & Strategy', 'Backtest Portfolio Value', 'Paper Trading History')

    # Create Figure
    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=subplot_titles,
                        row_heights=row_heights)

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

    # 2. Backtest Portfolio Value
    fig.add_trace(go.Scatter(x=df.index, y=df['PortfolioValue'], name='Backtest Value', line=dict(color='purple', width=2)), row=2, col=1)

    # 3. Paper Trading History (if available)
    if history:
        # Convert list of dicts to DataFrame for easier plotting
        hist_df = pd.DataFrame(history)
        if not hist_df.empty and 'date' in hist_df.columns and 'value' in hist_df.columns:
            # Ensure 'date' is datetime for proper x-axis plotting
            hist_df['date'] = pd.to_datetime(hist_df['date'])

            fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['value'], name='Paper Value',
                                     line=dict(color='green', width=2, dash='dot')), row=3, col=1)

            # Add markers for paper trades if we want
            paper_buys = hist_df[hist_df['signal'] == 1]
            paper_sells = hist_df[hist_df['signal'] == -1]

            if not paper_buys.empty:
                 fig.add_trace(go.Scatter(x=paper_buys['date'], y=paper_buys['value'], mode='markers',
                                     marker=dict(symbol='triangle-up', color='green', size=8), showlegend=False), row=3, col=1)

            if not paper_sells.empty:
                 fig.add_trace(go.Scatter(x=paper_sells['date'], y=paper_sells['value'], mode='markers',
                                     marker=dict(symbol='triangle-down', color='red', size=8), showlegend=False), row=3, col=1)


    # Update Layout
    fig.update_layout(title_text=f"Bitcoin Golden Cross Strategy Simulation<br>Total Return: {total_return:.2f}% | Max Drawdown: {max_drawdown:.2f}% | Trades: {num_trades}",
                      height=900 if history else 800,
                      template="plotly_white")

    # Save to HTML
    fig.write_html("index.html")
    print("Report generated: index.html")
