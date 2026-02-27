from src.strategy import fetch_data, calculate_indicators
from src.backtest import run_simulation
from src.reporting import generate_report
from src.history import init_firebase, update_paper_portfolio
import pandas as pd
import sys

def main():
    print("Starting Bitcoin Golden Cross Trading Bot Simulation...")

    # Initialize Firebase
    init_firebase()

    # 1. Fetch Data
    print("Fetching data...")
    # Fetch 5 years for backtest, but paper trading updates daily based on latest
    df = fetch_data(symbol='BTC-USD', period='5y')
    if df.empty:
        print("Error: Could not fetch data. Exiting.")
        sys.exit(1)

    print(f"Fetched {len(df)} rows of data.")

    # 2. Calculate Indicators
    print("Calculating indicators...")
    df = calculate_indicators(df)

    # 3. Run Backtest Simulation
    print("Running backtest simulation with 00 capital...")
    df_res, trades = run_simulation(df, initial_capital=100)

    # 4. Update Paper Trading History
    print("Updating paper trading history...")
    # Get the latest row (today's close)
    latest_row = df_res.iloc[-1]
    latest_date = df_res.index[-1]
    latest_price = latest_row['Close']
    latest_signal = latest_row['Signal'] # 1, -1, or 0

    # Update and get full history
    history = update_paper_portfolio(latest_date, latest_price, latest_signal)

    # 5. Generate Report
    print("Generating report...")
    generate_report(df_res, trades, history=history)

    # Print Summary
    initial_value = 100
    final_value = df_res['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100
    print(f"Simulation Complete.")
    print(f"Final Portfolio Value: ")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Total Trades: {len(trades)}")
    print("Report saved to index.html")

if __name__ == "__main__":
    main()
