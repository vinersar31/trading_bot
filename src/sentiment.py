import feedparser
from textblob import TextBlob
from datetime import datetime
import time

def get_sentiment(symbol):
    """
    Fetches Google News RSS feed for a symbol and calculates a sentiment score.

    Args:
        symbol (str): The stock/crypto symbol (e.g., 'BTC-USD', 'NVDA', 'Bitcoin').

    Returns:
        float: Normalized sentiment score between -1.0 (Negative) and 1.0 (Positive).
    """
    # Clean symbol for search (e.g., 'BTC-USD' -> 'Bitcoin', 'NVDA' -> 'NVIDIA' or just 'NVDA')
    # Simple mapping for better search results
    search_term = symbol
    if 'BTC' in symbol:
        search_term = 'Bitcoin'
    elif 'ETH' in symbol:
        search_term = 'Ethereum'

    # URL encode the search term
    search_term = search_term.replace(' ', '%20')

    rss_url = f"https://news.google.com/rss/search?q={search_term}&hl=en-US&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"No news found for {symbol}")
            return 0.0

        total_polarity = 0.0
        count = 0

        # Analyze the latest 10 articles
        for entry in feed.entries[:10]:
            title = entry.title
            # Some feeds might have summary, but Google News RSS summaries are often just the title + source
            # We focus on the title which is most descriptive

            analysis = TextBlob(title)
            polarity = analysis.sentiment.polarity

            total_polarity += polarity
            count += 1

        if count > 0:
            avg_polarity = total_polarity / count
            # TextBlob polarity is already -1 to 1
            return avg_polarity
        else:
            return 0.0

    except Exception as e:
        print(f"Error fetching sentiment for {symbol}: {e}")
        return 0.0

if __name__ == "__main__":
    # Test block
    symbols = ["BTC-USD", "NVDA", "AAPL"]
    for sym in symbols:
        score = get_sentiment(sym)
        print(f"Sentiment for {sym}: {score:.4f}")
