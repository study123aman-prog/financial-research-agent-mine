"""
SEC EDGAR Tool
Retrieves SEC filings for publicly traded companies
Free API - no authentication required
"""

import requests
from typing import Dict, Any


def sec_filing_search(
    ticker: str,
    filing_type: str = "10-K",
    year: int = None
) -> Dict[str, Any]:
    """
    Search and retrieve SEC EDGAR filings for a company.

    Args:
        ticker: Stock ticker symbol e.g. AAPL, MSFT
        filing_type: Type of filing - 10-K, 10-Q, 8-K, DEF 14A
        year: Filing year, defaults to most recent

    Returns:
        Dictionary with filing text, date, and accession number
    """

    headers = {
        "User-Agent": "ARA-1 Research Agent aman@research.com"
    }

    try:
        # Step 1: Get company CIK number from ticker
        ticker_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&enddt=2024-12-31&forms={filing_type}"

        search_url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": f'"{ticker}"',
            "forms": filing_type,
            "dateRange": "custom",
            "startdt": f"{year}-01-01" if year else "2020-01-01",
            "enddt": f"{year}-12-31" if year else "2024-12-31"
        }

        response = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return _mock_filing(ticker, filing_type)

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])

        if not hits:
            return _mock_filing(ticker, filing_type)

        # Get the most recent filing
        latest = hits[0]["_source"]

        return {
            "ticker": ticker,
            "filing_type": filing_type,
            "company_name": latest.get("entity_name", ticker),
            "filed_date": latest.get("file_date", "Unknown"),
            "accession_number": latest.get("accession_no", "Unknown"),
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{latest.get('entity_id', '')}/{latest.get('accession_no', '').replace('-', '')}/",
            "summary": f"Retrieved {filing_type} filing for {ticker}",
            "source": "SEC EDGAR",
            "reliability_tier": 1
        }

    except Exception as e:
        print(f"[SEC EDGAR] Error: {e}. Using mock data.")
        return _mock_filing(ticker, filing_type)


def _mock_filing(ticker: str, filing_type: str) -> Dict[str, Any]:
    """Returns mock filing data when API is unavailable"""
    return {
        "ticker": ticker,
        "filing_type": filing_type,
        "company_name": f"{ticker} Corporation",
        "filed_date": "2024-02-15",
        "accession_number": "0000320193-24-000123",
        "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}",
        "summary": f"Mock {filing_type} filing for {ticker}. Real data unavailable.",
        "source": "SEC EDGAR (mock)",
        "reliability_tier": 1,
        "is_mock": True
    }