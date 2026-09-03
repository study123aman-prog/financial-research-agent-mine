"""
Web Search Tool
General purpose web search for current news and analysis
"""

import requests
from typing import Dict, Any, List


def web_search(
    query: str,
    num_results: int = 10,
    date_range: str = None
) -> Dict[str, Any]:
    """
    Perform a web search for current information.

    Args:
        query: Search query string
        num_results: Number of results to return
        date_range: Optional date range filter

    Returns:
        Dictionary with search results
    """

    try:
        # Using DuckDuckGo instant answer API (free, no key needed)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return _mock_search(query)

        data = response.json()

        results = []

        # Get abstract if available
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", ""),
                "source": data.get("AbstractSource", "Web")
            })

        # Get related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:100],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source": "DuckDuckGo"
                })

        if not results:
            return _mock_search(query)

        return {
            "query": query,
            "total_results": len(results),
            "results": results[:num_results],
            "source": "DuckDuckGo",
            "reliability_tier": 4,
            "is_mock": False
        }

    except Exception as e:
        print(f"[Web Search] Error: {e}. Using mock.")
        return _mock_search(query)


def _mock_search(query: str) -> Dict[str, Any]:
    return {
        "query": query,
        "total_results": 3,
        "results": [
            {
                "title": f"{query} - Latest News and Analysis",
                "url": "https://reuters.com",
                "snippet": f"Recent developments regarding {query} show significant market activity.",
                "source": "Reuters"
            },
            {
                "title": f"{query} Financial Overview",
                "url": "https://bloomberg.com",
                "snippet": f"{query} continues to demonstrate strong fundamentals.",
                "source": "Bloomberg"
            },
            {
                "title": f"Analysis: {query} outlook",
                "url": "https://ft.com",
                "snippet": f"Analysts remain cautiously optimistic about {query}.",
                "source": "Financial Times"
            }
        ],
        "source": "Web Search (mock)",
        "reliability_tier": 4,
        "is_mock": True
    }