# Lazy imports — collectors are loaded on demand to avoid missing-dependency errors
# when optional modules (ntscraper, praw) are not installed.

def __getattr__(name):
    if name == "RedditCollector":
        from collectors.reddit_collector import RedditCollector
        return RedditCollector
    if name == "TwitterCollector":
        from collectors.twitter_collector import TwitterCollector
        return TwitterCollector
    if name == "MarketCollector":
        from collectors.market_collector import MarketCollector
        return MarketCollector
    if name == "GdeltCollector":
        from collectors.gdelt_collector import GdeltCollector
        return GdeltCollector
    raise AttributeError(f"module 'collectors' has no attribute {name!r}")

__all__ = ["RedditCollector", "TwitterCollector", "MarketCollector", "GdeltCollector"]
