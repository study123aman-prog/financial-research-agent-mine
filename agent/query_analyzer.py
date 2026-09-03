"""
Query Analyzer
Classifies incoming research queries and handles ambiguity
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def analyze_query(query: str) -> Dict[str, Any]:
    """
    Analyze and classify a research query.

    Args:
        query: The raw user query

    Returns:
        Dictionary with query classification and metadata
    """

    # Always run basic analysis first to detect companies
    basic = _basic_analysis(query)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from agent.prompts import QUERY_ANALYZER_PROMPT

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        prompt = QUERY_ANALYZER_PROMPT.format(query=query)
        response = llm.invoke(prompt)

        # Extract text from response
        content = response.content
        if isinstance(content, list):
            text = content[0].text if hasattr(content[0], 'text') else str(content[0])
        else:
            text = str(content)

        result = _parse_analyzer_response(text, query)

        # Always use basic analysis companies if LLM returns empty
        if not result["companies"]:
            result["companies"] = basic["companies"]

        return result

    except Exception as e:
        print(f"[Query Analyzer] Error: {e}. Using basic analysis.")
        return basic


def _parse_analyzer_response(content, original_query: str) -> Dict[str, Any]:
    """Parse the LLM response into structured data"""

    # Handle list response from Gemini
    if isinstance(content, list):
        text = content[0].text if hasattr(content[0], 'text') else str(content[0])
    else:
        text = str(content)

    lines = text.strip().split("\n")
    result = {
        "original_query": original_query,
        "query_type": "analytical",
        "companies": [],
        "complexity": "medium",
        "is_ambiguous": False,
        "assumptions": [],
        "clean_query": original_query
    }

    for line in lines:
        if line.startswith("TYPE:"):
            result["query_type"] = line.replace("TYPE:", "").strip().lower()
        elif line.startswith("COMPANIES:"):
            companies_str = line.replace("COMPANIES:", "").strip()
            if companies_str != "NONE":
                result["companies"] = [c.strip() for c in companies_str.split(",")]
        elif line.startswith("COMPLEXITY:"):
            result["complexity"] = line.replace("COMPLEXITY:", "").strip().lower()
        elif line.startswith("AMBIGUOUS:"):
            ambiguous = line.replace("AMBIGUOUS:", "").strip().lower()
            result["is_ambiguous"] = ambiguous == "yes"
        elif line.startswith("ASSUMPTIONS:"):
            assumptions_str = line.replace("ASSUMPTIONS:", "").strip()
            if assumptions_str != "NONE":
                result["assumptions"] = [assumptions_str]
        elif line.startswith("CLEAN_QUERY:"):
            result["clean_query"] = line.replace("CLEAN_QUERY:", "").strip()

    return result

def _basic_analysis(query: str) -> Dict[str, Any]:
    """Basic analysis without LLM"""

    query_upper = query.upper()

    # Company name to ticker mapping
    name_to_ticker = {
        "MICROSOFT": "MSFT",
        "APPLE": "AAPL",
        "GOOGLE": "GOOGL",
        "ALPHABET": "GOOGL",
        "AMAZON": "AMZN",
        "TESLA": "TSLA",
        "NVIDIA": "NVDA",
        "META": "META",
        "FACEBOOK": "META",
        "NETFLIX": "NFLX",
        "PALANTIR": "PLTR",
        "JPMORGAN": "JPM",
        "JP MORGAN": "JPM",
        "GOLDMAN": "GS",
        "MORGAN STANLEY": "MS"
    }

    # Direct ticker detection
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA",
               "AMZN", "META", "JPM", "PLTR", "AMD", "NFLX"]

    found_companies = [t for t in tickers if t in query_upper]

    # Name-based detection
    if not found_companies:
        for name, ticker in name_to_ticker.items():
            if name in query_upper:
                found_companies.append(ticker)

    return {
        "original_query": query,
        "query_type": "analytical",
        "companies": found_companies,
        "complexity": "medium",
        "is_ambiguous": len(found_companies) == 0,
        "assumptions": [],
        "clean_query": query
    }