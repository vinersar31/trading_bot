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
    Checks for FIREBASE_SERVICE_ACCOUNT environment variable.
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

    service_account_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

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
        print("FIREBASE_SERVICE_ACCOUNT not found. Using local storage (history.json).")
        db = None

def update_paper_portfolio(date, price, signal):
    """
    Updates the paper trading history.

    Args:
        date (pd.Timestamp): Current simulation date.
        price (float): Current price of BTC.
        signal (int): 1 (Buy), -1 (Sell), 0 (Hold).

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
            # Retrieve all documents from 'history' collection, ordered by date
            docs = db.collection('history').order_by('date').stream()
            history = [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error reading from Firebase: {e}")
            history = []
    else:
        # Load from local file
        if os.path.exists('history.json'):
            try:
                with open('history.json', 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

    # 2. Determine Current State
    if not history:
        # Initial State
        current_cash = 100.0
        current_position = 0.0
    else:
        last_record = history[-1]
        current_cash = last_record.get('cash', 100.0)
        current_position = last_record.get('position', 0.0)

    # 3. Execute Trade Logic (Paper Trading)
    # Note: This logic mirrors the backtest but runs step-by-step daily

    new_cash = current_cash
    new_position = current_position

    # Buy Signal
    if signal == 1 and current_cash > 0:
        amount = current_cash / price
        new_position = amount
        new_cash = 0.0
        print(f"Paper Trade: BUY at {price}")

    # Sell Signal
    elif signal == -1 and current_position > 0:
        amount = current_position
        new_cash = amount * price
        new_position = 0.0
        print(f"Paper Trade: SELL at {price}")

    # Calculate Current Portfolio Value
    portfolio_value = new_cash + (new_position * price)

    new_record = {
        'date': date_str,
        'price': float(price),
        'signal': int(signal),
        'cash': float(new_cash),
        'position': float(new_position),
        'value': float(portfolio_value)
    }

    # 4. Save New Record
    # Check if record for today already exists to avoid duplicates (idempotency)
    # We use date_str as the document ID in Firebase for easy lookups

    if db:
        try:
            db.collection('history').document(date_str).set(new_record)
            # Re-fetch history to ensure we return the updated list including the new record
            # Optimized: Just append to local list since we know what we saved
            # But we need to handle the case where we overwrote an existing daily record

            # Simple approach: Check if last record date is same
            if history and history[-1]['date'] == date_str:
                history[-1] = new_record
            else:
                history.append(new_record)

        except Exception as e:
            print(f"Error saving to Firebase: {e}")
    else:
        # Local Storage
        if history and history[-1]['date'] == date_str:
            history[-1] = new_record
        else:
            history.append(new_record)

        with open('history.json', 'w') as f:
            json.dump(history, f, indent=4)

    return history
