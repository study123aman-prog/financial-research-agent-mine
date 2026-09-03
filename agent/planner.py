"""
Research Planner
Generates structured research plans from queries
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


def generate_plan(query: str, query_analysis: Dict[str, Any]) -> List[str]:
    """
    Generate a structured research plan for a query.

    Args:
        query: The research query
        query_analysis: Results from query analyzer

    Returns:
        List of research steps
    """

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from agent.prompts import PLANNER_PROMPT

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        prompt = PLANNER_PROMPT.format(query=query)
        response = llm.invoke(prompt)

        # Extract text from response
        content = response.content
        if isinstance(content, list):
            text = content[0].text if hasattr(content[0], 'text') else str(content[0])
        else:
            text = str(content)

        # Parse numbered list into steps
        steps = _parse_plan(text)

        if not steps:
            return _default_plan(query_analysis)

        return steps

    except Exception as e:
        print(f"[Planner] Error: {e}. Using default plan.")
        return _default_plan(query_analysis)


def _parse_plan(content) -> List[str]:
    """Parse numbered list from LLM response"""

    # Handle list response from Gemini
    if isinstance(content, list):
        text = content[0].text if hasattr(content[0], 'text') else str(content[0])
    else:
        text = str(content)

    steps = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line and line[0].isdigit():
            parts = line.split(".", 1) if "." in line else line.split(")", 1)
            if len(parts) > 1:
                step = parts[1].strip()
                if step:
                    steps.append(step)

    return steps


def _default_plan(query_analysis: Dict[str, Any]) -> List[str]:
    """Default research plan when LLM fails"""

    companies = query_analysis.get("companies", [])
    ticker = companies[0] if companies else "AAPL"

    return [
        f"Fetch company profile for {ticker} using company_profile tool",
        f"Retrieve last 3 years financial statements for {ticker} using financial_data_api",
        f"Get most recent 10-K SEC filing for {ticker} using sec_filing_search",
        f"Fetch recent news sentiment for {ticker} using news_sentiment tool",
        f"Get stock price and market data for {ticker} using stock_price tool",
        f"Calculate key financial ratios for {ticker} using calculation_engine",
        f"Compare {ticker} with industry peers using peer_comparison tool",
        f"Get earnings transcript for {ticker} using earnings_transcript tool"
    ]