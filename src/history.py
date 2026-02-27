import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

# Global variable to store the Firestore client
db = None

def init_firebase():
    """
    Initializes Firebase.
    Checks for FIREBASE_SERVICE_ACCOUNT_KEY environment variable.
    If present, initializes the app.
    If not, defaults to local file storage.
    """
    global db

    # Check if already initialized
    if firebase_admin._apps:
        if not db:
             try:
                db = firestore.client()
             except Exception:
                 pass # Fallback if app exists but client fails
        return

    service_account_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')

    if service_account_key:
        try:
            # Parse the JSON string from the environment variable
            cred_dict = json.loads(service_account_key)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}. Falling back to local storage.")
            db = None
    else:
        print("FIREBASE_SERVICE_ACCOUNT_KEY not found. Using local storage (history.json).")
        db = None

def update_paper_portfolio(date, current_prices, technical_signals, sentiment_scores):
    """
    Updates the paper trading history using a weighted decision algorithm.

    Args:
        date (pd.Timestamp): Current simulation date.
        current_prices (dict): {'BTC-USD': 50000, ...}
        technical_signals (dict): {'BTC-USD': 1 (Bull), -1 (Bear), 0 (Neutral)}
        sentiment_scores (dict): {'BTC-USD': 0.5, ...}

    Returns:
        list: The complete history of portfolio values.
    """
    global db

    # Convert Timestamp to string for storage
    date_str = date.strftime('%Y-%m-%d')

    # 1. Load existing history
    history = []
    if db:
        try:
            docs = db.collection('history').order_by('date').stream()
            history = [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error reading from Firebase: {e}")
            history = []
    else:
        if os.path.exists('history.json'):
            try:
                with open('history.json', 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

    # 2. Determine Current State from History
    if not history:
        # Initial State
        current_cash = 100.0
        # Holdings: dictionary of symbol -> quantity
        current_holdings = {}
    else:
        last_record = history[-1]
        current_cash = float(last_record.get('cash', 100.0))
        # Handle migration from old single-asset format
        if 'position' in last_record and 'holdings' not in last_record:
            # Old format had 'position' for BTC-USD
            # Assuming BTC-USD was the only asset
            # But let's check if we know the symbol. Defaulting to BTC-USD for migration.
            current_holdings = {'BTC-USD': float(last_record.get('position', 0.0))}
        else:
            current_holdings = last_record.get('holdings', {})
            # Ensure quantities are floats
            current_holdings = {k: float(v) for k, v in current_holdings.items()}

    # 3. Weighted Decision Algorithm
    # Weights
    W_TECH = 0.7
    W_SENT = 0.3

    # Thresholds for Action
    BUY_THRESHOLD = 0.5  # If Score > 0.5
    SELL_THRESHOLD = -0.5 # If Score < -0.5

    decisions = {} # symbol -> 'BUY', 'SELL', 'HOLD'

    for symbol in current_prices.keys():
        tech_sig = technical_signals.get(symbol, 0)
        sent_score = sentiment_scores.get(symbol, 0.0)

        # Calculate Weighted Score
        # Tech signal is -1, 0, 1
        # Sentiment is -1.0 to 1.0

        final_score = (tech_sig * W_TECH) + (sent_score * W_SENT)

        if final_score > BUY_THRESHOLD:
            decisions[symbol] = 'BUY'
        elif final_score < SELL_THRESHOLD:
            decisions[symbol] = 'SELL'
        else:
            decisions[symbol] = 'HOLD'

    # 4. Execute Trades
    # Priority: Sell first to raise cash, then Buy

    new_cash = current_cash
    new_holdings = current_holdings.copy()

    # Execute Sells
    for symbol, action in decisions.items():
        if action == 'SELL':
            qty = new_holdings.get(symbol, 0.0)
            if qty > 0:
                price = current_prices.get(symbol, 0.0)
                proceeds = qty * price
                new_cash += proceeds
                new_holdings[symbol] = 0.0
                print(f"Paper Trade: SELL {symbol} at {price:.2f} (Score)")

    # Execute Buys
    # Distribute available cash among BUY signals?
    buy_candidates = [s for s, a in decisions.items() if a == 'BUY']

    if buy_candidates and new_cash > 1.0: # Min cash
        amount_per_trade = new_cash / len(buy_candidates)

        for symbol in buy_candidates:
            price = current_prices.get(symbol, 0.0)
            if price > 0:
                qty = amount_per_trade / price
                new_holdings[symbol] = new_holdings.get(symbol, 0.0) + qty
                new_cash -= amount_per_trade
                print(f"Paper Trade: BUY {symbol} at {price:.2f} (Amount: {amount_per_trade:.2f})")

    # 5. Calculate Total Value
    total_value = new_cash
    for sym, qty in new_holdings.items():
        price = current_prices.get(sym, 0.0)
        total_value += qty * price

    new_record = {
        'date': date_str,
        'cash': float(new_cash),
        'holdings': new_holdings,
        'value': float(total_value),
        # Optional: store signals/scores for debugging
        'decisions': decisions
    }

    # 6. Save Record
    if db:
        try:
            db.collection('history').document(date_str).set(new_record)
            if history and history[-1]['date'] == date_str:
                history[-1] = new_record
            else:
                history.append(new_record)
        except Exception as e:
            print(f"Error saving to Firebase: {e}")
    else:
        if history and history[-1]['date'] == date_str:
            history[-1] = new_record
        else:
            history.append(new_record)

        with open('history.json', 'w') as f:
            json.dump(history, f, indent=4)

    return history
