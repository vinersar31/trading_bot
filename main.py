from src.strategy import fetch_data, calculate_indicators
from src.backtest import run_simulation
from src.reporting import generate_report
import pandas as pd
import sys

def main():
    print("Starting Bitcoin Golden Cross Trading Bot Simulation...")

    # 1. Fetch Data
    print("Fetching data...")
    df = fetch_data(symbol='BTC-USD', period='5y') # 5 years to ensure we catch some crosses
    if df.empty:
        print("Error: Could not fetch data. Exiting.")
        sys.exit(1)

    print(f"Fetched {len(df)} rows of data.")

    # 2. Calculate Indicators
    print("Calculating indicators...")
    df = calculate_indicators(df)

    # 3. Run Simulation
    print("Running simulation with $100 capital...")
    df_res, trades = run_simulation(df, initial_capital=100)

    # 4. Generate Report
    print("Generating report...")
    generate_report(df_res, trades)

    # Print Summary
    initial_value = 100
    final_value = df_res['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100
    print(f"Simulation Complete.")
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Total Trades: {len(trades)}")
    print("Report saved to index.html")

if __name__ == "__main__":
    main()
