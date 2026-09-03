"""
Earnings Transcript Tool
Retrieves earnings call transcripts and key highlights
"""

import os
import requests
import yfinance as yf
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def earnings_transcript(
    ticker: str,
    quarter: str = "Q4",
    year: int = 2023
) -> Dict[str, Any]:
    """
    Retrieve earnings call transcript for a company.

    Args:
        ticker: Stock ticker symbol e.g. AAPL
        quarter: Quarter - Q1, Q2, Q3, Q4
        year: Year of the earnings call

    Returns:
        Dictionary with transcript and key highlights
    """

    try:
        # Try Alpha Vantage earnings data
        if ALPHA_VANTAGE_KEY:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "EARNINGS",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_KEY
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "quarterlyEarnings" in data:
                    quarterly = data["quarterlyEarnings"]

                    return {
                        "ticker": ticker,
                        "quarter": quarter,
                        "year": year,
                        "earnings_data": quarterly[:4],
                        "transcript_summary": f"Earnings data retrieved for {ticker}. Full transcript unavailable via free tier.",
                        "key_highlights": [
                            f"EPS reported: {quarterly[0].get('reportedEPS', 'N/A')}",
                            f"EPS estimated: {quarterly[0].get('estimatedEPS', 'N/A')}",
                            f"Surprise: {quarterly[0].get('surprise', 'N/A')}",
                            f"Surprise percent: {quarterly[0].get('surprisePercentage', 'N/A')}%"
                        ],
                        "source": "Alpha Vantage",
                        "reliability_tier": 3,
                        "is_mock": False
                    }

        return _mock_transcript(ticker, quarter, year)

    except Exception as e:
        print(f"[Earnings] Error: {e}. Using mock.")
        return _mock_transcript(ticker, quarter, year)


def _mock_transcript(
    ticker: str,
    quarter: str,
    year: int
) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "quarter": quarter,
        "year": year,
        "earnings_data": [],
        "transcript_summary": f"Mock transcript for {ticker} {quarter} {year}. Management expressed confidence in continued growth.",
        "key_highlights": [
            "Revenue exceeded analyst expectations by 3.2 percent",
            "Gross margins improved by 150 basis points year over year",
            "Management raised full year guidance",
            "New product launches expected in next quarter",
            "Share buyback program expanded by 10 billion dollars"
        ],
        "management_tone": "positive",
        "forward_guidance": "Management expects continued growth in the next quarter",
        "source": "Earnings Tool (mock)",
        "reliability_tier": 3,
        "is_mock": True
    }