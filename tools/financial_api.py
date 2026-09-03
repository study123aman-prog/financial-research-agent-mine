"""
Financial Data API Tool
Retrieves financial statements and ratios using Alpha Vantage
"""

import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"


def financial_data_api(
    ticker: str,
    statement_type: str = "income",
    period: str = "annual",
    years: int = 3
) -> Dict[str, Any]:
    """
    Retrieve financial statements for a company.

    Args:
        ticker: Stock ticker symbol e.g. AAPL
        statement_type: income, balance, cashflow, overview
        period: annual or quarterly
        years: number of years to retrieve

    Returns:
        Dictionary with financial statement data
    """

    if not ALPHA_VANTAGE_KEY:
        print("[Financial API] No API key found. Using mock data.")
        return _mock_financials(ticker, statement_type)

    # Map statement type to Alpha Vantage function
    function_map = {
        "income": "INCOME_STATEMENT",
        "balance": "BALANCE_SHEET",
        "cashflow": "CASH_FLOW",
        "overview": "OVERVIEW"
    }

    function = function_map.get(statement_type, "INCOME_STATEMENT")

    try:
        params = {
            "function": function,
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_KEY
        }

        print(f"[Financial API] Fetching {statement_type} for {ticker}...")
        response = requests.get(BASE_URL, params=params, timeout=15)

        if response.status_code != 200:
            print(f"[Financial API] HTTP {response.status_code}. Using mock.")
            return _mock_financials(ticker, statement_type)

        data = response.json()

        # Check for API error or rate limit
        if "Error Message" in data:
            print(f"[Financial API] Error: {data['Error Message']}. Using mock.")
            return _mock_financials(ticker, statement_type)

        if "Note" in data:
            print(f"[Financial API] Rate limit hit. Using mock.")
            return _mock_financials(ticker, statement_type)

        if "Information" in data:
            print(f"[Financial API] Rate limit. Using mock.")
            return _mock_financials(ticker, statement_type)

        # Handle overview differently
        if statement_type == "overview":
            return {
                "ticker": ticker,
                "statement_type": "overview",
                "company_name": data.get("Name", ticker),
                "sector": data.get("Sector", "N/A"),
                "industry": data.get("Industry", "N/A"),
                "market_cap": data.get("MarketCapitalization", "N/A"),
                "pe_ratio": data.get("PERatio", "N/A"),
                "eps": data.get("EPS", "N/A"),
                "revenue_ttm": data.get("RevenueTTM", "N/A"),
                "profit_margin": data.get("ProfitMargin", "N/A"),
                "roe": data.get("ReturnOnEquityTTM", "N/A"),
                "debt_to_equity": data.get("DebtToEquityRatio", "N/A"),
                "description": data.get("Description", "N/A"),
                "source": "Alpha Vantage",
                "reliability_tier": 2,
                "is_mock": False
            }

        # Get the right reports
        if period == "annual":
            reports = data.get("annualReports", [])
        else:
            reports = data.get("quarterlyReports", [])

        if not reports:
            print(f"[Financial API] No reports found. Using mock.")
            return _mock_financials(ticker, statement_type)

        # Limit to requested years
        reports = reports[:years]

        print(f"[Financial API] Got {len(reports)} {period} reports for {ticker}")

        return {
            "ticker": ticker,
            "statement_type": statement_type,
            "period": period,
            "reports": reports,
            "latest": reports[0] if reports else {},
            "source": "Alpha Vantage",
            "reliability_tier": 2,
            "is_mock": False
        }

    except Exception as e:
        print(f"[Financial API] Error: {e}. Using mock data.")
        return _mock_financials(ticker, statement_type)


def _mock_financials(ticker: str, statement_type: str) -> Dict[str, Any]:
    """Returns mock financial data when API is unavailable"""
    return {
        "ticker": ticker,
        "statement_type": statement_type,
        "period": "annual",
        "reports": [
            {
                "fiscalDateEnding": "2023-12-31",
                "totalRevenue": "211915000000",
                "grossProfit": "146052000000",
                "operatingIncome": "88523000000",
                "netIncome": "72361000000",
                "eps": "9.72"
            },
            {
                "fiscalDateEnding": "2022-12-31",
                "totalRevenue": "198270000000",
                "grossProfit": "135620000000",
                "operatingIncome": "83383000000",
                "netIncome": "72738000000",
                "eps": "9.65"
            }
        ],
        "latest": {
            "fiscalDateEnding": "2023-12-31",
            "totalRevenue": "211915000000",
            "grossProfit": "146052000000",
            "netIncome": "72361000000"
        },
        "source": "Alpha Vantage (mock)",
        "reliability_tier": 2,
        "is_mock": True
    }