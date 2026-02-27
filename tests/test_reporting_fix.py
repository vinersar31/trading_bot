import unittest
import pandas as pd
from src.reporting import generate_report

class TestReporting(unittest.TestCase):
    def test_generate_report_no_history(self):
        # Setup Data
        dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'PortfolioValue': [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
        }, index=dates)
        trades = []

        # Should not raise exception
        generate_report(df, trades)

    def test_generate_report_with_history(self):
        # Setup Data
        dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'PortfolioValue': [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
        }, index=dates)
        trades = []
        history = [
            {'date': '2020-01-01', 'value': 100.0, 'cash': 100.0, 'holdings': {}},
            {'date': '2020-01-02', 'value': 101.0, 'cash': 0.0, 'holdings': {'BTC': 1.0}}
        ]

        # Should not raise exception, particularly the subplot error
        try:
            generate_report(df, trades, history=history)
        except ValueError as e:
            self.fail(f"generate_report raised ValueError unexpectedly: {e}")

if __name__ == '__main__':
    unittest.main()
