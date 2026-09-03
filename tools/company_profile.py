"""
Company Profile Tool
Retrieves basic company information and overview
"""

import yfinance as yf
from typing import Dict, Any


def company_profile(ticker: str) -> Dict[str, Any]:
    """
    Retrieve comprehensive company profile.

    Args:
        ticker: Stock ticker symbol e.g. AAPL

    Returns:
        Dictionary with company profile data
    """

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "longName" not in info:
            return _mock_profile(ticker)

        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "website": info.get("website", "N/A"),
            "description": info.get("longBusinessSummary", "N/A"),
            "ceo": info.get("companyOfficers", [{}])[0].get("name", "N/A") if info.get("companyOfficers") else "N/A",
            "market_cap": info.get("marketCap", "N/A"),
            "exchange": info.get("exchange", "N/A"),
            "currency": info.get("currency", "USD"),
            "fiscal_year_end": info.get("fiscalYearEnd", "N/A"),
            "source": "Yahoo Finance",
            "reliability_tier": 2,
            "is_mock": False
        }

    except Exception as e:
        print(f"[Company Profile] Error: {e}. Using mock.")
        return _mock_profile(ticker)


def _mock_profile(ticker: str) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "company_name": f"{ticker} Corporation",
        "sector": "Technology",
        "industry": "Software",
        "country": "United States",
        "employees": 150000,
        "website": f"https://www.{ticker.lower()}.com",
        "description": f"{ticker} is a leading technology company focused on innovation.",
        "ceo": "John Smith",
        "market_cap": 2000000000000,
        "exchange": "NASDAQ",
        "currency": "USD",
        "fiscal_year_end": "December",
        "source": "Yahoo Finance (mock)",
        "reliability_tier": 2,
        "is_mock": True
    }