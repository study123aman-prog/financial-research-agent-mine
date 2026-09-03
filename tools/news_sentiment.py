"""
News Sentiment Tool
Fetches recent news and analyzes sentiment using VADER
"""

import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def news_sentiment(
    query: str,
    num_articles: int = 10,
    lookback_days: int = 30
) -> Dict[str, Any]:
    """
    Fetch recent news articles and analyze sentiment.

    Args:
        query: Search query e.g. company name or topic
        num_articles: Number of articles to retrieve
        lookback_days: How many days back to search

    Returns:
        Dictionary with articles and sentiment scores
    """

    try:
        from textblob import TextBlob

        if not NEWS_API_KEY:
            print("[News] No API key. Using mock.")
            return _mock_news(query)

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": num_articles,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": NEWS_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return _mock_news(query)

        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            return _mock_news(query)

        # Analyze sentiment for each article
        processed = []
        total_sentiment = 0

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title} {description}"

            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity

            total_sentiment += sentiment_score

            processed.append({
                "title": title,
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", ""),
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": _label(sentiment_score)
            })

        avg_sentiment = total_sentiment / len(processed) if processed else 0

        return {
            "query": query,
            "total_articles": len(processed),
            "articles": processed,
            "average_sentiment": round(avg_sentiment, 3),
            "overall_sentiment": _label(avg_sentiment),
            "source": "NewsAPI + TextBlob",
            "reliability_tier": 4,
            "is_mock": False
        }

    except Exception as e:
        print(f"[News] Error: {e}. Using mock.")
        return _mock_news(query)


def _label(score: float) -> str:
    if score > 0.1:
        return "positive"
    elif score < -0.1:
        return "negative"
    return "neutral"


def _mock_news(query: str) -> Dict[str, Any]:
    return {
        "query": query,
        "total_articles": 3,
        "articles": [
            {
                "title": f"{query} reports strong quarterly results",
                "source": "Reuters",
                "published_at": "2024-01-15",
                "url": "https://reuters.com",
                "sentiment_score": 0.45,
                "sentiment_label": "positive"
            },
            {
                "title": f"{query} faces regulatory scrutiny",
                "source": "Bloomberg",
                "published_at": "2024-01-10",
                "url": "https://bloomberg.com",
                "sentiment_score": -0.25,
                "sentiment_label": "negative"
            },
            {
                "title": f"{query} announces new product lineup",
                "source": "Financial Times",
                "published_at": "2024-01-05",
                "url": "https://ft.com",
                "sentiment_score": 0.30,
                "sentiment_label": "positive"
            }
        ],
        "average_sentiment": 0.17,
        "overall_sentiment": "positive",
        "source": "NewsAPI (mock)",
        "reliability_tier": 4,
        "is_mock": True
    }