# Bitcoin Trading Bot Simulation

This project simulates a Bitcoin Golden Cross trading strategy. It fetches historical data, runs a backtest, and generates an interactive report.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Simulation**:
    ```bash
    python main.py
    ```

3.  **View Results**:
    Open `index.html` in your browser.

## Strategy

-   **Golden Cross**: Buy when the 50-day SMA crosses above the 200-day SMA.
-   **Death Cross**: Sell when the 50-day SMA crosses below the 200-day SMA.
-   **Initial Capital**: $100.
-   **Execution**: At the Close price of the day the signal occurs.

## GitHub Pages

To publish the results:
1.  Run the simulation.
2.  Commit `index.html` to a branch (e.g., `gh-pages` or `main` depending on your settings).
    -   Note: `index.html` is ignored by default to keep the repo clean. You can force add it: `git add -f index.html`.
3.  Enable GitHub Pages in your repository settings.
