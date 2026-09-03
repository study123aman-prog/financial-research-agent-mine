# ARA-1: Autonomous Research Agent - Architecture Specification
# Author: Aman Singh
# Version: 1.0

---

## 1. Executive Summary

ARA-1 is a fully autonomous financial research agent that replicates
the workflow of a junior financial analyst. Given a natural language
research query, ARA-1 independently formulates a research plan,
gathers data from multiple sources including SEC EDGAR filings,
financial data APIs, earnings call transcripts, and news feeds,
resolves conflicting information, and produces a structured
professional investment research report without human guidance.

---

## 2. Agent Pattern: Hybrid Plan-and-Execute + ReAct

ARA-1 uses a hybrid architecture.

Outer loop is Plan-and-Execute:
- Planner LLM generates structured research steps upfront
- Each step is then executed one by one
- Plan is revised if intermediate results require it

Inner loop is ReAct:
- Thought: reason about the current step
- Action: invoke the best tool
- Observation: process the result
- Repeat until step is complete

Why not pure ReAct: causes redundant tool calls and poor coherence
for complex multi-source research.

Why not pure Plan-and-Execute: a rigid plan cannot adapt when
intermediate results reveal unexpected information like API failures
or company restatements.

---

## 3. LangGraph State Design

The agent maintains a shared state object throughout the research
session. Here are the fields:

query - the original user query
query_type - factual, analytical, comparative, or ambiguous
assumptions - list of disambiguation assumptions made
plan - ordered list of research steps
current_step - which step we are currently on
plan_revisions - how many times the plan was revised
gathered_data - all tool results stored by source type
sources - all sources with metadata and reliability tier
conflicts - detected data conflicts and how they were resolved
memory_hits - number of times ChromaDB was used instead of an API
session_id - unique identifier for this research session
synthesis - the synthesized analytical narrative
draft_report - first report before verification
verified_report - final report after the verification pass
errors - all errors encountered with recovery actions taken
fallbacks_used - which fallback chains were triggered
tool_calls - total number of tool invocations
start_time - timestamp for latency tracking

---

## 4. LangGraph Nodes and Flow

The agent moves through these nodes in order:

query_analyzer → planner → executor → synthesizer → verifier → reporter

The executor loops back to itself until all plan steps are complete,
then passes to synthesizer.

Node details:

query_analyzer lives in agent/query_analyzer.py
- Takes the raw query
- Classifies its type and ambiguity level
- Documents any assumptions made

planner lives in agent/planner.py
- Takes the classified query
- Generates an ordered list of research steps

executor lives in agent/core.py
- Takes one plan step at a time
- Runs the ReAct inner loop
- Calls tools and processes observations

synthesizer lives in synthesis/engine.py
- Takes all gathered data
- Merges findings from all sources
- Resolves conflicts using reliability hierarchy
- Produces analytical narrative

verifier lives in tools/fact_checker.py
- Takes the draft report
- Checks every numerical claim against sources
- Flags or corrects anything unverifiable

reporter lives in tools/report_gen.py
- Takes the verified content
- Formats it into a structured markdown report

---

## 5. Tool Registry - 12 Tools

Tool 1: sec_filing_search
- File: tools/sec_edgar.py
- Source: SEC EDGAR
- Fallback: web_search

Tool 2: financial_data_api
- File: tools/financial_api.py
- Source: Alpha Vantage
- Fallback: yahoo_finance

Tool 3: stock_price
- File: tools/yahoo_finance.py
- Source: Yahoo Finance
- Fallback: financial_data_api

Tool 4: news_sentiment
- File: tools/news_sentiment.py
- Source: NewsAPI + VADER sentiment
- Fallback: web_search

Tool 5: earnings_transcript
- File: tools/earnings.py
- Source: Alpha Vantage
- Fallback: web_search

Tool 6: company_profile
- File: tools/company_profile.py
- Source: Yahoo Finance
- Fallback: financial_data_api

Tool 7: peer_comparison
- File: tools/peer_comparison.py
- Source: Yahoo Finance
- Fallback: financial_data_api

Tool 8: calculation_engine
- File: tools/calculator.py
- Source: Pure Python math
- Fallback: none needed

Tool 9: fact_checker
- File: tools/fact_checker.py
- Source: Multi-source cross-reference
- Fallback: none needed

Tool 10: vector_db_search
- File: memory/vector_store.py
- Source: ChromaDB
- Fallback: none needed

Tool 11: vector_db_store
- File: memory/vector_store.py
- Source: ChromaDB
- Fallback: none needed

Tool 12: report_generator
- File: tools/report_gen.py
- Source: Internal formatter
- Fallback: none needed

---

## 6. Three-Layer Memory Architecture

Layer 1 - Short-Term Memory
- Lives inside LangGraph ResearchState
- Exists only during current session
- When approaching token limit, earlier steps are summarized

Layer 2 - Long-Term Memory
- ChromaDB vector database stored locally
- Persists across all research sessions
- Embedding model: all-MiniLM-L6-v2 (free, runs locally, 384 dimensions)
- Chunking rules:
  SEC filings are chunked by section (Risk Factors, MD&A, Financials)
  Earnings transcripts are chunked by Q&A pair
  News articles are chunked by paragraph with headline included
  Financial statements are stored as JSON not embedded

- Each record in ChromaDB contains:
  id, content, ticker, source_type, date, confidence, verified, session_id

Layer 3 - Episodic Memory
- SQLite database file
- Persists across all sessions
- Stores: session_id, query, plan, tools_used, tools_failed,
  fallbacks_triggered, outcome, evaluation_score, duration, timestamp
- Used to learn which strategies work for which query types

---

## 7. RAG Pipeline - 7 Stages

Stage 1: Query Transformation
The raw query is decomposed by the LLM into 3 to 5 specific
retrieval sub-queries.

Stage 2: Memory Check First
ChromaDB is searched before any external API is called.
If similarity score is above 0.85, the cached result is used.

Stage 3: External API Retrieval
Only called when memory does not have the answer.

Stage 4: Relevance Filtering
Each retrieved document is scored against the query.
Documents below 0.7 relevance are discarded.

Stage 5: Context Assembly
Token budget:
- 40 percent for primary data (filings, financials)
- 30 percent for supporting evidence (news, transcripts)
- 20 percent for system prompt and tool descriptions
- 10 percent for generation space

Stage 6: Grounded Generation
LLM generates response using only retrieved context.
Every claim must cite a specific source.

Stage 7: Post-Generation Verification
Second LLM pass checks all numerical claims.
Anything not traceable to a source is flagged or corrected.

---

## 8. Source Reliability Hierarchy

Tier 1 - SEC Filings (10-K, 10-Q)
Legally mandated, audited, criminal penalties for misrepresentation.
This is the highest reliability source.

Tier 2 - Financial Data APIs (Alpha Vantage, Yahoo Finance)
Professional curation with quality controls.

Tier 3 - Earnings Call Transcripts
Direct management commentary but subject to spin.

Tier 4 - Major News Outlets (Reuters, Bloomberg, Financial Times)
Editorial oversight but may contain errors.

Tier 5 - Social Media and Anonymous Forums
Unverified and subject to manipulation. Lowest trust.

Conflict Resolution Protocol:
1. Detect when two sources differ by more than 5 percent
2. Check if different time periods explain the difference
3. Check for financial restatements
4. Apply highest tier rule - prefer the more reliable source
5. Document the conflict and resolution in the final report

---

## 9. Error Handling Architecture

Retry Logic:
Attempt 1 - immediate
Attempt 2 - wait 1 second plus random jitter up to 500ms
Attempt 3 - wait 2 seconds plus jitter
Attempt 4 - wait 4 seconds plus jitter
Attempt 5 - wait 8 seconds plus jitter
After 5 failures - trigger fallback chain

Fallback Chains:
financial_data_api fails → try yahoo_finance → try vector_db_search
sec_filing_search fails  → try web_search   → try vector_db_search
news_sentiment fails     → try web_search   → try vector_db_search

Circuit Breaker:
Opens after 3 consecutive failures on the same tool.
Resets after 60 seconds.
Prevents one broken tool from consuming all retry budget.

Graceful Degradation:
When all fallbacks are exhausted:
- Log what data is missing and why
- Continue research with available data
- Clearly state gaps in the final report
- Never fabricate data to fill gaps

---

## 10. Evaluation Framework - 22 Metrics

Category 1: Factual Accuracy
FA-1: Numerical Accuracy Rate - target above 98 percent
FA-2: Citation Accuracy - target 100 percent
FA-3: Temporal Accuracy - target 100 percent
FA-4: Entity Accuracy - target 100 percent
FA-5: Hallucination Rate - target zero

Category 2: Completeness
CO-1: Section Coverage - target 100 percent
CO-2: Data Source Diversity - target 4 or more source types
CO-3: Temporal Coverage - target 3 or more years
CO-4: Risk Factor Coverage - target 80 percent or above

Category 3: Analytical Depth
AD-1: Insight Density - target 3 or more per page
AD-2: Cross-Source Synthesis - target 5 or more per report
AD-3: Quantitative Reasoning - target 10 or more calculations
AD-4: Forward-Looking Analysis - target 2 or more sections

Category 4: Coherence and Structure
CS-1: Logical Flow - assessed by LLM judge
CS-2: Internal Consistency - target zero contradictions
CS-3: Executive Summary Quality - assessed by comparison
CS-4: Professional Formatting - follows template

Category 5: Agent Behaviour
AB-1: Tool Efficiency - target 70 percent or above
AB-2: Error Recovery Rate - target 90 percent or above
AB-3: Planning Quality - assessed qualitatively
AB-4: Memory Utilization - target 0.3 or above
AB-5: Latency - target under 5 minutes per single company report

---

## 11. Tech Stack

Agent Framework: LangGraph
LLM for development: GPT-4o-mini
LLM for final runs: GPT-4o
Vector Database: ChromaDB running locally
Episodic Memory: SQLite
Embedding Model: sentence-transformers all-MiniLM-L6-v2
Financial Data: Alpha Vantage
Market Data: Yahoo Finance via yfinance library
News: NewsAPI with VADER sentiment scoring
SEC Filings: EDGAR full-text search API (free, no auth)
Programming Language: Python 3.14

---

## 12. Eight Progressive Research Challenges

Challenge 1: Microsoft company profile - Difficulty 1 out of 5
Challenge 2: Apple quarterly earnings analysis - Difficulty 2 out of 5
Challenge 3: Tesla risk assessment - Difficulty 2 out of 5
Challenge 4: AWS vs Azure vs GCP comparison - Difficulty 3 out of 5
Challenge 5: Palantir contradictory data - Difficulty 3 out of 5
Challenge 6: What is happening with the banks - Difficulty 4 out of 5
Challenge 7: Tech sector themes using memory - Difficulty 4 out of 5
Challenge 8: NVIDIA full report with 50 percent tool failures - Difficulty 5 out of 5