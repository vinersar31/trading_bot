import unittest
from unittest.mock import patch, MagicMock
import os
import pandas as pd
import json
from src.history import init_firebase, update_paper_portfolio, db

class TestHistory(unittest.TestCase):

    def setUp(self):
        # Reset the global db variable before each test
        # We need to access the module directly to reset the global variable
        import src.history
        src.history.db = None

        # Clean up local history file if it exists
        if os.path.exists('history.json'):
            os.remove('history.json')

    def tearDown(self):
         if os.path.exists('history.json'):
            os.remove('history.json')

    @patch('src.history.firebase_admin.initialize_app')
    @patch('src.history.credentials.Certificate')
    @patch('src.history.firestore.client')
    @patch.dict(os.environ, {'FIREBASE_SERVICE_ACCOUNT_KEY': '{"type": "service_account"}'})
    def test_init_firebase_success(self, mock_firestore, mock_cred, mock_init):
        init_firebase()

        mock_cred.assert_called_once()
        mock_init.assert_called_once()
        mock_firestore.assert_called_once()

        import src.history
        self.assertIsNotNone(src.history.db)

    @patch.dict(os.environ, {}, clear=True)
    def test_init_firebase_missing_env(self):
        init_firebase()
        import src.history
        self.assertIsNone(src.history.db)

    @patch.dict(os.environ, {'FIREBASE_SERVICE_ACCOUNT_KEY': 'invalid_json'})
    def test_init_firebase_invalid_json(self):
        init_firebase()
        import src.history
        self.assertIsNone(src.history.db)

    def test_update_portfolio_local_fallback(self):
        # Ensure db is None
        import src.history
        src.history.db = None

        date = pd.Timestamp('2024-01-01')
        current_prices = {'BTC-USD': 50000.0}
        technical_signals = {'BTC-USD': 1} # Bullish
        sentiment_scores = {'BTC-USD': 1.0} # Positive

        # Weighted Score = 0.7*1 + 0.3*1 = 1.0 > 0.5 (Buy)

        # First Run: Initial Capital 100
        history = update_paper_portfolio(date, current_prices, technical_signals, sentiment_scores)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['cash'], 0.0) # Used all cash to buy

        # Holdings check
        holdings = history[0]['holdings']
        self.assertIn('BTC-USD', holdings)
        self.assertAlmostEqual(holdings['BTC-USD'], 100.0/50000.0)

        # Second Run: Next Day, Price Goes Up
        date2 = pd.Timestamp('2024-01-02')
        current_prices2 = {'BTC-USD': 55000.0}
        technical_signals2 = {'BTC-USD': 0} # Neutral
        sentiment_scores2 = {'BTC-USD': 0.0} # Neutral
        # Score = 0 -> Hold

        history = update_paper_portfolio(date2, current_prices2, technical_signals2, sentiment_scores2)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]['cash'], 0.0)
        # Value should increase
        self.assertAlmostEqual(history[1]['value'], (100.0/50000.0) * 55000.0)
