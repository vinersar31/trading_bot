class Portfolio:
    def __init__(self, initial_cash=100.0, holdings=None):
        self.cash = float(initial_cash)
        # Holdings: { 'BTC-USD': 0.005, 'NVDA': 1.2 }
        self.holdings = holdings if holdings else {}
        self.history = []

    def get_total_value(self, current_prices):
        """
        Calculates total portfolio value based on current cash and asset prices.

        Args:
            current_prices (dict): {'BTC-USD': 50000, 'NVDA': 1000}

        Returns:
            float: Total value in USD.
        """
        assets_value = 0.0
        for symbol, quantity in self.holdings.items():
            price = current_prices.get(symbol, 0.0)
            assets_value += quantity * price

        return self.cash + assets_value

    def buy(self, symbol, price, amount_usd):
        """
        Buys an asset using USD amount.

        Args:
            symbol (str): Asset symbol.
            price (float): Current price per unit.
            amount_usd (float): Amount of USD to spend.

        Returns:
            bool: True if successful, False if insufficient funds.
        """
        if amount_usd <= 0 or price <= 0:
            return False

        if self.cash >= amount_usd:
            quantity = amount_usd / price
            self.cash -= amount_usd
            self.holdings[symbol] = self.holdings.get(symbol, 0.0) + quantity
            return True
        else:
            return False

    def sell(self, symbol, price, quantity_fraction=1.0):
        """
        Sells a fraction of the holding for a specific asset.

        Args:
            symbol (str): Asset symbol.
            price (float): Current price per unit.
            quantity_fraction (float): Fraction of holding to sell (0.0 to 1.0).

        Returns:
            bool: True if successful, False if asset not held.
        """
        if symbol not in self.holdings or self.holdings[symbol] <= 0:
            return False

        if quantity_fraction <= 0 or quantity_fraction > 1.0:
            return False

        quantity_to_sell = self.holdings[symbol] * quantity_fraction
        proceeds = quantity_to_sell * price

        self.cash += proceeds
        self.holdings[symbol] -= quantity_to_sell

        # Cleanup tiny residuals
        if self.holdings[symbol] < 1e-9:
            del self.holdings[symbol]

        return True

if __name__ == "__main__":
    # Test block
    p = Portfolio(initial_cash=1000)
    prices = {'BTC': 50000, 'ETH': 3000}

    print(f"Initial Value: {p.get_total_value(prices)}")

    p.buy('BTC', 50000, 500)
    print(f"After buying 500 USD of BTC: Cash={p.cash}, Holdings={p.holdings}")

    p.sell('BTC', 60000, 0.5) # Sell half position at profit
    prices['BTC'] = 60000
    print(f"After selling half BTC at 60k: Cash={p.cash}, Holdings={p.holdings}")
    print(f"Current Value: {p.get_total_value(prices)}")
