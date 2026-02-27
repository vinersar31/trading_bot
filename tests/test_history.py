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

    def test_update_portfolio_local_fallback(self):
        # Ensure db is None
        import src.history
        src.history.db = None

        date = pd.Timestamp('2024-01-01')
        price = 50000.0
        signal = 1 # Buy

        # First Run: Initial Capital 100
        history = update_paper_portfolio(date, price, signal)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['cash'], 0.0) # Used all cash to buy
        self.assertAlmostEqual(history[0]['position'], 100.0/50000.0)
        self.assertEqual(history[0]['signal'], 1)

        # Second Run: Next Day, Price Goes Up
        date2 = pd.Timestamp('2024-01-02')
        price2 = 55000.0
        signal2 = 0 # Hold

        history = update_paper_portfolio(date2, price2, signal2)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]['cash'], 0.0)
        # Value should increase
        self.assertAlmostEqual(history[1]['value'], (100.0/50000.0) * 55000.0)

    @patch('src.history.firebase_admin.initialize_app')
    @patch('src.history.credentials.Certificate')
    @patch('src.history.firestore.client')
    @patch.dict(os.environ, {'FIREBASE_SERVICE_ACCOUNT_KEY': '{"type": "service_account"}'})
    def test_update_portfolio_firebase(self, mock_firestore_client, mock_cred, mock_init):
        # Setup Mock Firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db

        # Mock retrieving history (empty initially)
        mock_collection = mock_db.collection.return_value
        mock_collection.order_by.return_value.stream.return_value = []

        # Initialize
        init_firebase()

        # Run Update
        date = pd.Timestamp('2024-01-01')
        price = 50000.0
        signal = 1

        history = update_paper_portfolio(date, price, signal)

        # Verify Interactions
        mock_db.collection.assert_called_with('history')
        # Check that set() was called on the document
        mock_db.collection().document().set.assert_called()

if __name__ == '__main__':
    unittest.main()
