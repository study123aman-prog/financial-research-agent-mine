"""
Peer Comparison Tool
Identifies industry peers and compares key financial metrics
"""

import yfinance as yf
from typing import Dict, Any, List


# Common peer groups for major companies
PEER_GROUPS = {
    "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "CRM"],
    "GOOGL": ["MSFT", "META", "AAPL", "AMZN"],
    "TSLA": ["F", "GM", "RIVN", "NIO"],
    "NVDA": ["AMD", "INTC", "QCOM", "TSM"],
    "JPM": ["BAC", "WFC", "GS", "MS"],
    "AMZN": ["MSFT", "GOOGL", "AAPL", "WMT"],
    "META": ["GOOGL", "SNAP", "TWTR", "PINS"]
}


def peer_comparison(
    ticker: str,
    num_peers: int = 4,
    metrics: List[str] = None
) -> Dict[str, Any]:
    """
    Compare a company against its industry peers.

    Args:
        ticker: Stock ticker symbol e.g. AAPL
        num_peers: Number of peers to compare
        metrics: List of metrics to compare

    Returns:
        Dictionary with peer comparison data
    """

    if metrics is None:
        metrics = ["pe_ratio", "market_cap", "revenue", "profit_margin"]

    try:
        # Get peers for this ticker
        peers = PEER_GROUPS.get(ticker.upper(), [])

        if not peers:
            # Try to find peers via Yahoo Finance sector
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get("sector", "Technology")
            peers = _get_sector_peers(sector, ticker)

        peers = peers[:num_peers]

        # Gather data for main company and peers
        all_tickers = [ticker] + peers
        comparison_data = []

        for t in all_tickers:
            try:
                stock = yf.Ticker(t)
                info = stock.info

                comparison_data.append({
                    "ticker": t,
                    "company_name": info.get("longName", t),
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "revenue": info.get("totalRevenue", "N/A"),
                    "profit_margin": info.get("profitMargins", "N/A"),
                    "roe": info.get("returnOnEquity", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "52_week_return": info.get("52WeekChange", "N/A"),
                    "is_primary": t == ticker
                })

            except Exception:
                comparison_data.append({
                    "ticker": t,
                    "company_name": t,
                    "market_cap": "N/A",
                    "pe_ratio": "N/A",
                    "revenue": "N/A",
                    "profit_margin": "N/A",
                    "is_primary": t == ticker
                })

        if not comparison_data:
            return _mock_peer_comparison(ticker)

        return {
            "ticker": ticker,
            "peers": peers,
            "comparison": comparison_data,
            "source": "Yahoo Finance",
            "reliability_tier": 2,
            "is_mock": False
        }

    except Exception as e:
        print(f"[Peer Comparison] Error: {e}. Using mock.")
        return _mock_peer_comparison(ticker)


def _get_sector_peers(sector: str, exclude: str) -> List[str]:
    """Returns default peers for a sector"""
    sector_defaults = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "META"],
        "Financial Services": ["JPM", "BAC", "WFC", "GS"],
        "Healthcare": ["JNJ", "PFE", "UNH", "ABBV"],
        "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE"]
    }
    peers = sector_defaults.get(sector, ["AAPL", "MSFT", "GOOGL"])
    return [p for p in peers if p != exclude.upper()]


def _mock_peer_comparison(ticker: str) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "peers": ["MSFT", "GOOGL", "META"],
        "comparison": [
            {
                "ticker": ticker,
                "company_name": f"{ticker} Corporation",
                "market_cap": 2850000000000,
                "pe_ratio": 28.5,
                "revenue": 394000000000,
                "profit_margin": 0.246,
                "roe": 0.871,
                "debt_to_equity": 1.76,
                "is_primary": True
            },
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation",
                "market_cap": 2800000000000,
                "pe_ratio": 32.1,
                "revenue": 211000000000,
                "profit_margin": 0.341,
                "roe": 0.432,
                "debt_to_equity": 0.42,
                "is_primary": False
            }
        ],
        "source": "Yahoo Finance (mock)",
        "reliability_tier": 2,
        "is_mock": True
    }