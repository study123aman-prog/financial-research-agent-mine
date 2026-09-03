"""
Tools Package
Registers all tools into the ToolRegistry
"""

from tools.tool_registry import ToolRegistry
from tools.sec_edgar import sec_filing_search
from tools.financial_api import financial_data_api
from tools.yahoo_finance import stock_price
from tools.news_sentiment import news_sentiment
from tools.web_search import web_search
from tools.company_profile import company_profile
from tools.earnings import earnings_transcript
from tools.peer_comparison import peer_comparison
from tools.calculator import calculation_engine
from tools.fact_checker import fact_checker
from tools.report_gen import report_generator
from memory.vector_store import vector_db_store, vector_db_search

def create_registry() -> ToolRegistry:
    """Create and return a fully populated tool registry"""

    registry = ToolRegistry()

    registry.register(
        name="sec_filing_search",
        description="Search and retrieve SEC EDGAR filings for a publicly traded US company. Use for official regulatory disclosures including 10-K annual reports, 10-Q quarterly reports, and 8-K material events.",
        function=sec_filing_search,
        input_schema={
            "ticker": "str - stock ticker symbol e.g. AAPL",
            "filing_type": "str - 10-K, 10-Q, or 8-K",
            "year": "int - optional, defaults to most recent"
        },
        fallback_tools=["web_search"]
    )

    registry.register(
        name="financial_data_api",
        description="Retrieve structured financial statements including income statement, balance sheet, and cash flow. Use for revenue, profit, and financial ratio data.",
        function=financial_data_api,
        input_schema={
            "ticker": "str - stock ticker symbol",
            "statement_type": "str - income, balance, or cashflow",
            "period": "str - annual or quarterly",
            "years": "int - number of years"
        },
        fallback_tools=["stock_price"]
    )

    registry.register(
        name="stock_price",
        description="Retrieve current stock price, historical prices, and key market ratios like P/E ratio and market cap from Yahoo Finance.",
        function=stock_price,
        input_schema={
            "ticker": "str - stock ticker symbol",
            "period": "str - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"
        },
        fallback_tools=["financial_data_api"]
    )

    registry.register(
        name="news_sentiment",
        description="Fetch recent news articles about a company or topic and analyze overall sentiment. Use to understand current market perception and recent developments.",
        function=news_sentiment,
        input_schema={
            "query": "str - company name or topic to search",
            "num_articles": "int - number of articles, default 10",
            "lookback_days": "int - days to look back, default 30"
        },
        fallback_tools=["web_search"]
    )

    registry.register(
        name="web_search",
        description="Perform a general web search for current news, analysis, and information about a company or financial topic. Use when other tools fail or for general research.",
        function=web_search,
        input_schema={
            "query": "str - search query",
            "num_results": "int - number of results, default 10",
            "date_range": "str - optional date filter"
        },
        fallback_tools=[]
    )

    registry.register(
        name="company_profile",
        description="Retrieve basic company information including sector, industry, number of employees, business description, and key executives.",
        function=company_profile,
        input_schema={
            "ticker": "str - stock ticker symbol"
        },
        fallback_tools=["financial_data_api"]
    )

    registry.register(
        name="earnings_transcript",
        description="Retrieve earnings call data and key highlights for a specific quarter. Use to understand management commentary and forward guidance.",
        function=earnings_transcript,
        input_schema={
            "ticker": "str - stock ticker symbol",
            "quarter": "str - Q1, Q2, Q3, or Q4",
            "year": "int - year of earnings call"
        },
        fallback_tools=["web_search"]
    )

    registry.register(
        name="peer_comparison",
        description="Identify industry peers and compare key financial metrics across companies. Use for competitive analysis and benchmarking.",
        function=peer_comparison,
        input_schema={
            "ticker": "str - stock ticker symbol",
            "num_peers": "int - number of peers, default 4",
            "metrics": "list - metrics to compare"
        },
        fallback_tools=["financial_data_api"]
    )

    registry.register(
        name="calculation_engine",
        description="Perform financial calculations including growth rates, CAGR, P/E ratio, ROE, DCF valuation, and profit margins. Use when you need to compute derived metrics.",
        function=calculation_engine,
        input_schema={
            "calculation_type": "str - growth_rate, cagr, pe_ratio, roe, dcf, profit_margin, ebitda_margin",
            "inputs": "dict - input values for the calculation"
        },
        fallback_tools=[]
    )

    registry.register(
        name="fact_checker",
        description="Cross-reference a specific claim against multiple sources to verify accuracy. Use for all numerical claims before including in final report.",
        function=fact_checker,
        input_schema={
            "claim": "str - the claim to verify",
            "sources": "list - optional list of source names"
        },
        fallback_tools=[]
    )

    registry.register(
        name="vector_db_search",
        description="Search the agent long-term memory for previously researched information. Always check this before making external API calls to avoid redundant requests.",
        function=vector_db_search,
        input_schema={
            "query": "str - search query",
            "top_k": "int - number of results to return"
        },
        fallback_tools=[]
    )

    registry.register(
        name="vector_db_store",
        description="Store research findings in long-term memory for future retrieval.",
        function=vector_db_store,
        input_schema={
            "content": "str - text content to store",
            "metadata": "dict - ticker, source_type, date, confidence"
        },
        fallback_tools=[]
    )

    registry.register(
        name="report_generator",
        description="Format all researched data into a structured professional investment research report. Use as the final step after all data has been gathered and verified.",
        function=report_generator,
        input_schema={
            "template": "str - report template type",
            "sections": "dict - report sections and content",
            "sources": "list - sources used in research"
        },
        fallback_tools=[]
    )

    return registry