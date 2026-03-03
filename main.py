import pandas as pd
import sys
import time

from src.strategy import fetch_data, calculate_indicators, get_technical_signal
from src.backtest import run_simulation
from src.reporting import generate_report
from src.history import init_firebase, update_paper_portfolio
from src.sentiment import get_sentiment

def main():
    print("Starting Multi-Asset Trading Bot Simulation...")

    # Initialize Firebase
    init_firebase()

    # Define Portfolio Assets (Stock + Crypto mix)
    SYMBOLS = ['BTC-USD', 'ETH-USD', 'NVDA', 'AAPL', 'GOOGL']
    print(f"Assets: {SYMBOLS}")

    # 1. Fetch Data
    print("Fetching data...")
    # Fetch 5 years for backtest
    data_dict = fetch_data(SYMBOLS, period='5y')

    if not data_dict:
        print("Error: Could not fetch data for any symbol. Exiting.")
        sys.exit(1)

    print(f"Fetched data for: {list(data_dict.keys())}")

    # 2. Calculate Indicators for all
    print("Calculating indicators...")
    for symbol, df in data_dict.items():
        data_dict[symbol] = calculate_indicators(df)

    # 3. Run Backtest Simulation (Technical Only)
    print("Running backtest simulation with 00 capital...")
    df_res, trades = run_simulation(data_dict, initial_capital=100)

    # 4. Update Paper Trading History (Weighted Algorithm)
    print("Updating paper trading history...")

    # Get latest data points for Paper Trading Decision
    current_prices = {}
    technical_signals = {}
    sentiment_scores = {}

    latest_date = df_res.index[-1]

    for symbol in SYMBOLS:
        # Get Price and Technical Signal
        if symbol in data_dict:
            df = data_dict[symbol]
            if not df.empty:
                latest_row = df.iloc[-1]
                current_prices[symbol] = latest_row['Close']
                technical_signals[symbol] = get_technical_signal(latest_row)

        # Get Sentiment Score (Live)
        # Note: This makes a network call to Google News
        print(f"Fetching news sentiment for {symbol}...")
        sentiment_scores[symbol] = get_sentiment(symbol)
        # Be nice to Google News API
        time.sleep(1)

    print("Technical Signals:", technical_signals)
    print("Sentiment Scores:", sentiment_scores)

    # Update and get full history
    history = update_paper_portfolio(latest_date, current_prices, technical_signals, sentiment_scores)

    # 5. Generate Report
    print("Generating report...")
    generate_report(df_res, trades, data_dict, history=history)

    # Print Summary
    initial_value = 100
    final_value = df_res['PortfolioValue'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100

    print(f"Simulation Complete.")
    print(f"Final Backtest Value: ")
    print(f"Total Return (Backtest): {total_return:.2f}%")
    print(f"Total Trades: {len(trades)}")
    print("Report saved to index.html")

if __name__ == "__main__":
    main()
