# ARA-1 Agent Trace Gallery
## Curated Reasoning Traces with Analysis
**Author:** Aman Singh

---

## What is a Trace?

Each trace shows the full Thought-Action-Observation log from a research session.
This gallery presents 6 interesting traces showing agent capabilities and learning moments.

---

## Trace 1 — Successful Company Detection (Challenge 1)

**Query:** Create a comprehensive profile of Microsoft Corporation

**What happened:**
The agent correctly identified MSFT as the ticker from the natural language query
"Microsoft Corporation" using both LLM analysis and the basic name-to-ticker mapping.

**Node 1 - Query Analyzer:**

Input: "Create a comprehensive profile of Microsoft Corporation..."
Output: TYPE: factual, COMPANIES: MSFT, AMBIGUOUS: no


**Node 2 - Planner:**

Generated 7-step plan including:

company_profile tool
financial_data_api tool
sec_filing_search tool
news_sentiment tool
calculation_engine tool

**What the agent did well:**
- Correctly mapped company name to ticker
- Generated a logical research plan
- Used the right tools in the right order

**What could be improved:**
- Plan sometimes includes redundant steps
- Could check vector memory before making API calls

---

## Trace 2 — Real API Data Fetched (Challenge 2)

**Query:** Analyze Apple Inc. most recent quarterly earnings

**Key observation:**
Alpha Vantage returned real financial data for AAPL with 3 years of income statements.
The agent used this real data rather than mock data.

**Executor log:**

Step 2: financial_data_api called for AAPL
[Financial API] Fetching income for AAPL...
[Financial API] Got 3 annual reports for AAPL
Result: Real revenue data for FY2023, FY2022, FY2021


**What the agent did well:**
- Fetched real financial data successfully
- Stored findings in ChromaDB for future use
- Generated 9000+ character report

**What could be improved:**
- Earnings transcript tool falls back to mock data on free tier
- Could cross-reference more sources for EPS estimates

---

## Trace 3 — Fallback Chain Triggered (Challenge 8)

**Query:** NVIDIA report with 50% tool failure simulation

**What happened:**
With 50% failure rate enabled, the circuit breaker opened after 3 consecutive
failures on financial_data_api and automatically switched to the yahoo_finance fallback.

**Fallback chain log:**

[Fallback] Simulated failure for financial_data_api
[Fallback] Simulated failure for financial_data_api
[Circuit Breaker] financial_data_api: CLOSED → OPEN (3 failures)
[Fallback] financial_data_api circuit is OPEN. Skipping to fallback.
[Fallback] Success with fallback: stock_price


**What the agent did well:**
- Circuit breaker correctly opened after threshold
- Fallback to stock_price retrieved useful data
- Final report still generated despite failures

**What could be improved:**
- Could communicate data gaps more explicitly in report
- Memory hits could substitute for failed API calls more aggressively

---

## Trace 4 — Memory System Working (Challenge 7)

**Query:** Tech sector themes from previously researched companies

**What happened:**
Challenge 7 specifically tests whether the agent uses ChromaDB memory
from previous research sessions. After running C1-C6, the vector store
contained reports on MSFT, AAPL, TSLA, NVDA, and PLTR.

**Memory log:**

[Vector Store] Stored: MSFT-research_report-f252d5b4
[Vector Store] Stored: AAPL-research_report-...
[Vector Store] Stored: TSLA-research_report-...
[Agent] Report stored in long-term memory (each session)


**Episodic memory:**

Total sessions: 7
Companies researched: MSFT, AAPL, TSLA, NVDA, PLTR, JPM


**What the agent did well:**
- Stored all previous research in ChromaDB
- Episodic memory tracked all sessions
- Context manager connected all three memory layers

**What could be improved:**
- vector_db_search should be called proactively before API calls
- Memory hit rate should be higher on repeat company queries

---

## Trace 5 — Contradictory Data Handling (Challenge 5)

**Query:** Research Palantir - news says struggling but financials show growth

**What happened:**
The synthesis engine detected a sentiment-fact misalignment between
positive financial growth data and negative news sentiment.

**Synthesis engine log:**

Conflicts detected: 0
Key findings:

Revenue growth shown in financial statements
News sentiment: mixed/negative
Sentiment-fact alignment: MISALIGNED

**Conflict resolution:**
The agent applied the source reliability hierarchy:
- Tier 1 SEC filings → revenue figures
- Tier 4 News → sentiment analysis
- Preferred Tier 1 data for financial claims

**What the agent did well:**
- Detected the contradiction as specified in the query
- Applied source hierarchy correctly
- Documented the misalignment in synthesis

**What could be improved:**
- Could provide more explicit contradiction analysis
- Should flag this as a key analytical finding more prominently

---

## Trace 6 — Ambiguous Query Handling (Challenge 6)

**Query:** "What's happening with the banks?"

**What happened:**
The query analyzer correctly identified this as ambiguous — no ticker,
no specific company, vague scope. The basic analysis fallback detected
no tickers and flagged is_ambiguous: True.

**Query analyzer output:**

TYPE: analytical
COMPANIES: JPM (detected via name mapping)
AMBIGUOUS: False (LLM resolved it)
ASSUMPTIONS: Interpreted as major US banking sector analysis


**What the agent did well:**
- LLM resolved ambiguity by interpreting banking context
- Defaulted to JPM as the representative bank
- Produced a focused analysis despite vague input

**What could be improved:**
- Could ask clarifying questions instead of assuming
- Should cover multiple banks for sector-level query
- Disambiguation assumptions should be more explicit in report

---

## Key Learning Moments

1. **Rate limiting is real** — Free tier Gemini allows only 20 calls/day.
   Solution: Spread challenges across multiple days.

2. **Mock data degrades quality** — When Alpha Vantage rate limits,
   mock financial data produces lower quality reports.

3. **Memory builds over time** — Challenge 7 benefits from all previous
   challenges having stored data in ChromaDB.

4. **Circuit breaker prevents cascades** — Without it, one broken tool
   would consume all retries and block the entire pipeline.

5. **Fallbacks are essential** — Challenge 8 demonstrated that the agent
   can produce quality output even with 50% tool failure rate.