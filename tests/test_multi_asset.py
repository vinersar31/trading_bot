import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.sentiment import get_sentiment
from src.portfolio import Portfolio
from src.strategy import fetch_data, calculate_indicators, get_technical_signal

class TestMultiAsset(unittest.TestCase):

    def test_portfolio_logic(self):
        p = Portfolio(initial_cash=1000)
        self.assertEqual(p.cash, 1000)
        self.assertEqual(p.holdings, {})

        # Test Buy
        res = p.buy('BTC', 50000, 500)
        self.assertTrue(res)
        self.assertEqual(p.cash, 500)
        self.assertEqual(p.holdings['BTC'], 0.01)

        # Test Value Calculation
        prices = {'BTC': 60000}
        val = p.get_total_value(prices)
        # 500 cash + 0.01 * 60000 = 500 + 600 = 1100
        self.assertEqual(val, 1100)

        # Test Sell
        res = p.sell('BTC', 60000, 0.5) # Sell half (0.005)
        self.assertTrue(res)
        self.assertEqual(p.holdings['BTC'], 0.005)
        self.assertEqual(p.cash, 500 + (0.005 * 60000)) # 500 + 300 = 800

    @patch('src.sentiment.feedparser.parse')
    def test_sentiment_mock(self, mock_parse):
        # Mock Feed
        mock_entry = MagicMock()
        mock_entry.title = "Bitcoin hits new all time high! Great news!"

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        score = get_sentiment('BTC')
        # "Great news" and "high" generally positive
        self.assertGreater(score, 0.0)

    @patch('src.strategy.yf.download')
    def test_strategy_multi_fetch(self, mock_download):
        # Mock DataFrame
        mock_df = pd.DataFrame({'Close': [100, 101, 102]}, index=pd.to_datetime(['2021-01-01', '2021-01-02', '2021-01-03']))
        mock_download.return_value = mock_df

        data = fetch_data(['BTC', 'ETH'])
        self.assertIn('BTC', data)
        self.assertIn('ETH', data)
        self.assertFalse(data['BTC'].empty)

    def test_technical_signal(self):
        # Neutral/None
        row = pd.Series({'SMA50': None, 'SMA200': 100})
        self.assertEqual(get_technical_signal(row), 0)

        # Bullish
        row = pd.Series({'SMA50': 105, 'SMA200': 100})
        self.assertEqual(get_technical_signal(row), 1)

        # Bearish
        row = pd.Series({'SMA50': 95, 'SMA200': 100})
        self.assertEqual(get_technical_signal(row), -1)

if __name__ == '__main__':
    unittest.main()
