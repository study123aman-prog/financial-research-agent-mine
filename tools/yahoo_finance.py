"""
Yahoo Finance Tool
Retrieves stock prices, company info, and key ratios
Free - no API key required
"""

import yfinance as yf
from typing import Dict, Any


def stock_price(
    ticker: str,
    period: str = "1y"
) -> Dict[str, Any]:
    """
    Retrieve stock price and key financial ratios.

    Args:
        ticker: Stock ticker symbol e.g. AAPL
        period: Time period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y

    Returns:
        Dictionary with price data and key ratios
    """

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get current price data
        hist = stock.history(period=period)

        if hist.empty:
            print(f"[Yahoo Finance] No data for {ticker}. Using mock.")
            return _mock_stock_data(ticker)

        current_price = hist["Close"].iloc[-1]
        start_price = hist["Close"].iloc[0]
        price_change = ((current_price - start_price) / start_price) * 100

        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "current_price": round(float(current_price), 2),
            "price_change_percent": round(float(price_change), 2),
            "period": period,
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "eps": info.get("trailingEps", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "volume": info.get("volume", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "source": "Yahoo Finance",
            "reliability_tier": 2,
            "is_mock": False
        }

    except Exception as e:
        print(f"[Yahoo Finance] Error: {e}. Using mock data.")
        return _mock_stock_data(ticker)


def _mock_stock_data(ticker: str) -> Dict[str, Any]:
    """Returns mock stock data when API is unavailable"""
    return {
        "ticker": ticker,
        "company_name": f"{ticker} Corporation",
        "current_price": 185.50,
        "price_change_percent": 12.5,
        "period": "1y",
        "market_cap": 2850000000000,
        "pe_ratio": 28.5,
        "forward_pe": 25.2,
        "eps": 6.13,
        "dividend_yield": 0.005,
        "52_week_high": 199.62,
        "52_week_low": 124.17,
        "volume": 58000000,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "source": "Yahoo Finance (mock)",
        "reliability_tier": 2,
        "is_mock": True
    }