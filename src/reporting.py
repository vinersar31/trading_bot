import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def generate_report(df_sim, trades, history=None):
    """
    Generates an HTML report with plots and statistics for multi-asset simulation.

    Args:
        df_sim (pd.DataFrame): Simulation result DataFrame with 'PortfolioValue'.
        trades (list): List of trades.
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
    subplot_titles = ('Backtest Portfolio Value', 'Paper Trading History & Allocation')

    # Define subplot specs
    specs = [[{"type": "xy"}], [{"type": "xy"}]]

    if history:
        rows = 3
        row_heights = [0.5, 0.3, 0.2]
        subplot_titles = ('Backtest Portfolio Value', 'Paper Trading History', 'Current Allocation')
        # Add specs for 3rd row (Pie chart requires 'domain' type)
        specs = [[{"type": "xy"}], [{"type": "xy"}], [{"type": "domain"}]]

    # Create Figure
    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=False,
                        vertical_spacing=0.1,
                        subplot_titles=subplot_titles,
                        row_heights=row_heights,
                        specs=specs)

    # 1. Backtest Portfolio Value
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim['PortfolioValue'], name='Backtest Value',
                             line=dict(color='purple', width=2)), row=1, col=1)

    # 2. Paper Trading History (if available)
    if history:
        # Convert list of dicts to DataFrame for easier plotting
        hist_df = pd.DataFrame(history)
        if not hist_df.empty and 'date' in hist_df.columns and 'value' in hist_df.columns:
            # Ensure 'date' is datetime for proper x-axis plotting
            hist_df['date'] = pd.to_datetime(hist_df['date'])

            fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['value'], name='Paper Value',
                                     line=dict(color='green', width=2, dash='dot')), row=2, col=1)

            # Add markers for significant changes?

            # 3. Current Asset Allocation (Pie Chart)
            # Get latest holdings from history
            latest_record = history[-1]
            holdings = latest_record.get('holdings', {})
            cash = latest_record.get('cash', 0.0)

            labels = ['Cash'] + list(holdings.keys())

            # Calculate values in USD
            # Note: We need prices to calculate value of holdings.
            # If history stores value, we might not have breakdown per asset unless we stored it.
            # But we stored holdings quantity. We need price.
            # Simplified: Use quantity for pie chart? No, use Value.
            # We don't have current prices readily available here unless passed.
            # BUT we can approximate or just show Quantity if prices unavailable?
            # Better: The History record should probably store Value breakdown or we just accept 'Cash vs Invested'

            # Let's try to use the 'value' from record as total and cash as cash.
            invested_value = latest_record.get('value', 0.0) - cash

            # If we can't easily get value per asset, let's just plot Cash vs Invested
            pie_values = [cash, invested_value]
            pie_labels = ['Cash', 'Invested Assets']

            fig.add_trace(go.Pie(labels=pie_labels, values=pie_values, hole=.3), row=3, col=1)

    # Update Layout
    fig.update_layout(title_text=f"Multi-Asset Trading Bot Simulation<br>Total Return: {total_return:.2f}% | Max Drawdown: {max_drawdown:.2f}% | Trades: {num_trades}",
                      height=1000 if history else 800,
                      template="plotly_white")

    # Save to HTML
    fig.write_html("index.html")
    print("Report generated: index.html")
