import unittest
import pandas as pd
from src.reporting import generate_report

class TestReporting(unittest.TestCase):
    def setUp(self):
        # Create dummy data_dict
        dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
        self.dummy_data_dict = {
            'BTC': pd.DataFrame({
                'Close': [100 + i for i in range(10)],
                'SMA50': [90 + i for i in range(10)],
                'SMA200': [80 + i for i in range(10)]
            }, index=dates)
        }

    def test_generate_report_no_history(self):
        # Setup Data
        dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'PortfolioValue': [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
        }, index=dates)
        trades = []

        # Should not raise exception
        generate_report(df, trades, self.dummy_data_dict)

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
            generate_report(df, trades, self.dummy_data_dict, history=history)
        except ValueError as e:
            self.fail(f"generate_report raised ValueError unexpectedly: {e}")

if __name__ == '__main__':
    unittest.main()
