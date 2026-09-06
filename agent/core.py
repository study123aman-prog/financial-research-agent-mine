"""
ARA-1 Core Agent
LangGraph StateGraph implementation of the research agent
"""

import os
import uuid
import time
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def _extract_text(response) -> str:
    """Extract text from any Gemini response format"""
    try:
        # Try .content attribute first
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for item in content:
                if hasattr(item, 'text'):
                    return item.text
                if isinstance(item, dict) and 'text' in item:
                    return item['text']
            return str(content[0])
        if isinstance(content, dict):
            return content.get('text', str(content))
        return str(content)
    except Exception:
        return str(response)

# ─── State Definition ───────────────────────────────────────────────────────

class ResearchState(TypedDict):
    """Shared state across all agent nodes"""
    # Query
    query: str
    query_type: str
    companies: List[str]
    assumptions: List[str]
    clean_query: str

    # Planning
    plan: List[str]
    current_step: int
    plan_revisions: int

    # Data
    gathered_data: Dict[str, Any]
    sources: List[Dict]
    conflicts: List[Dict]

    # Memory
    memory_hits: int
    session_id: str

    # Output
    synthesis: str
    draft_report: str
    verified_report: str
    final_report: str

    # Monitoring
    errors: List[Dict]
    fallbacks_used: List[str]
    tool_calls: int
    start_time: float
    failure_rate: float

# ─── Node Functions ──────────────────────────────────────────────────────────

def node_query_analyzer(state: ResearchState) -> ResearchState:
    """Node 1: Analyze and classify the incoming query"""

    print(f"\n[Node 1: Query Analyzer] Analyzing: {state['query']}")

    from agent.query_analyzer import analyze_query
    analysis = analyze_query(state["query"])

    print(f"  Type: {analysis['query_type']}")
    print(f"  Companies: {analysis['companies']}")
    print(f"  Ambiguous: {analysis['is_ambiguous']}")

    return {
        **state,
        "query_type": analysis["query_type"],
        "companies": analysis["companies"],
        "assumptions": analysis["assumptions"],
        "clean_query": analysis["clean_query"]
    }


def node_planner(state: ResearchState) -> ResearchState:
    """Node 2: Generate research plan"""

    print(f"\n[Node 2: Planner] Generating research plan...")

    from agent.planner import generate_plan
    plan = generate_plan(
        state["clean_query"],
        {
            "query_type": state["query_type"],
            "companies": state["companies"]
        }
    )

    print(f"  Plan has {len(plan)} steps:")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step}")

    return {
        **state,
        "plan": plan,
        "current_step": 0
    }


def node_executor(state: ResearchState) -> ResearchState:
    """Node 3: Execute one step of the research plan"""

    current = state["current_step"]
    plan = state["plan"]

    if current >= len(plan):
        print(f"\n[Node 3: Executor] All steps complete")
        return state

    step = plan[current]
    print(f"\n[Node 3: Executor] Step {current + 1}/{len(plan)}: {step}")

    # Execute the step
    result = _execute_step(step, state, state["failure_rate"])

    # Update gathered data
    gathered = state["gathered_data"].copy()
    gathered[f"step_{current + 1}"] = {
        "step": step,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

    # Track sources
    sources = state["sources"].copy()
    if result.get("source"):
        sources.append({
            "name": result.get("source"),
            "type": result.get("source", "unknown"),
            "tier": result.get("reliability_tier", 4),
            "step": current + 1
        })

    return {
        **state,
        "gathered_data": gathered,
        "sources": sources,
        "current_step": current + 1,
        "tool_calls": state["tool_calls"] + 1
    }


def node_synthesizer(state: ResearchState) -> ResearchState:
    """Node 4: Synthesize all gathered data"""

    print(f"\n[Node 4: Synthesizer] Synthesizing {len(state['gathered_data'])} data points...")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from agent.prompts import SYNTHESIS_PROMPT

        # Format findings for prompt
        findings = ""
        for key, data in state["gathered_data"].items():
            findings += f"\n{key}: {data['step']}\n"
            result = data.get("result", {})
            if isinstance(result, dict):
                for k, v in list(result.items())[:5]:
                    findings += f"  {k}: {v}\n"

        sources_text = "\n".join([
            f"- {s['name']} (Tier {s['tier']})"
            for s in state["sources"]
        ])

        conflicts_text = "None detected" if not state["conflicts"] else str(state["conflicts"])

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )

        prompt = SYNTHESIS_PROMPT.format(
            query=state["clean_query"],
            findings=findings,
            sources=sources_text,
            conflicts=conflicts_text
        )

        response = llm.invoke(prompt)
        synthesis = _extract_text(response)

        print(f"  Synthesis complete: {len(synthesis)} characters")

    except Exception as e:
        print(f"  [Synthesizer] Error: {e}. Using basic synthesis.")
        synthesis = f"Research completed for query: {state['query']}\n"
        synthesis += f"Data gathered from {len(state['gathered_data'])} sources.\n"
        synthesis += f"Steps completed: {state['current_step']}"

    return {
        **state,
        "synthesis": synthesis
    }


def node_verifier(state: ResearchState) -> ResearchState:
    """Node 5: Verify claims in the synthesis"""

    print(f"\n[Node 5: Verifier] Verifying claims...")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from agent.prompts import VERIFICATION_PROMPT

        sources_text = str(state["gathered_data"])[:2000]

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        prompt = VERIFICATION_PROMPT.format(
            report=state["synthesis"],
            sources=sources_text
        )

        response = llm.invoke(prompt)
        verification_notes = _extract_text(response)
        print(f"  Verification complete")

        # Create draft report combining synthesis and verification
        draft = f"{state['synthesis']}\n\n---\nVERIFICATION NOTES:\n{verification_notes}"

    except Exception as e:
        print(f"  [Verifier] Error: {e}")
        draft = state["synthesis"]
        verification_notes = "Verification skipped due to error"

    return {
        **state,
        "draft_report": draft,
        "verified_report": verification_notes
    }


def node_reporter(state: ResearchState) -> ResearchState:
    """Node 6: Generate final formatted report"""

    print(f"\n[Node 6: Reporter] Generating final report...")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from agent.prompts import REPORT_PROMPT

        companies = state["companies"]
        company = companies[0] if companies else "Company"
        date = datetime.now().strftime("%Y-%m-%d")

        sources_text = "\n".join([
            f"- {s['name']} (Reliability Tier {s['tier']})"
            for s in state["sources"]
        ])

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )

        prompt = REPORT_PROMPT.format(
            query=state["clean_query"],
            synthesis=state["synthesis"],
            verification=state["verified_report"],
            sources=sources_text,
            company=company,
            date=date
        )

        response = llm.invoke(prompt)
        final_report = _extract_text(response)
        # Calculate duration
        duration = time.time() - state["start_time"]

        print(f"  Report generated: {len(final_report)} characters")
        print(f"  Total time: {duration:.1f} seconds")
        print(f"  Tool calls: {state['tool_calls']}")

    except Exception as e:
        print(f"  [Reporter] Error: {e}")
        final_report = state["synthesis"]

    return {
        **state,
        "final_report": final_report
    }


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _execute_step(step: str, state: ResearchState, failure_rate: float = 0.0) -> Dict[str, Any]:
    """Execute a single research step using fallback chains"""

    from tools import create_registry
    from agent.fallback_chains import execute_with_fallback

    if not hasattr(_execute_step, '_registry') or failure_rate > 0:
        _execute_step._registry = create_registry()
    registry = _execute_step._registry

    step_lower = step.lower()
    companies = state["companies"]
    ticker = companies[0] if companies else "AAPL"

    # Route to correct tool
    if "company profile" in step_lower or "profile" in step_lower:
        tool_name = "company_profile"
        inputs = {"ticker": ticker}

    elif "sec filing" in step_lower or "10-k" in step_lower or "edgar" in step_lower:
        tool_name = "sec_filing_search"
        inputs = {"ticker": ticker, "filing_type": "10-K"}

    elif "financial statement" in step_lower or "income" in step_lower or "financial data" in step_lower:
        tool_name = "financial_data_api"
        inputs = {"ticker": ticker, "statement_type": "income", "period": "annual", "years": 3}

    elif "news" in step_lower or "sentiment" in step_lower:
        tool_name = "news_sentiment"
        inputs = {"query": ticker, "num_articles": 10, "lookback_days": 30}

    elif "stock price" in step_lower or "price" in step_lower or "market data" in step_lower:
        tool_name = "stock_price"
        inputs = {"ticker": ticker, "period": "1y"}

    elif "ratio" in step_lower or "calculat" in step_lower:
        tool_name = "calculation_engine"
        inputs = {"calculation_type": "growth_rate", "inputs": {"current_value": 100, "previous_value": 90}}

    elif "peer" in step_lower or "comparison" in step_lower or "competitor" in step_lower:
        tool_name = "peer_comparison"
        inputs = {"ticker": ticker, "num_peers": 3}

    elif "earnings" in step_lower or "transcript" in step_lower:
        tool_name = "earnings_transcript"
        inputs = {"ticker": ticker, "quarter": "Q4", "year": 2023}

    else:
        tool_name = "web_search"
        inputs = {"query": f"{ticker} {step}", "num_results": 5}

    print(f"  [Executor] Tool: {tool_name}, Ticker: {ticker}, FailureRate: {failure_rate}")

    result = execute_with_fallback(
        tool_name=tool_name,
        inputs=inputs,
        registry=registry,
        failure_rate=failure_rate
    )

    return result

# ─── Should Continue Function ─────────────────────────────────────────────────

def should_continue(state: ResearchState) -> str:
    """Decide whether to continue executing steps or move to synthesis"""

    if state["current_step"] >= len(state["plan"]):
        return "synthesize"

    if state["tool_calls"] >= 20:
        print("  [Core] Max tool calls reached. Moving to synthesis.")
        return "synthesize"

    return "continue"


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_agent():
    """Build and return the LangGraph agent"""

    from langgraph.graph import StateGraph, END

    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("query_analyzer", node_query_analyzer)
    graph.add_node("planner", node_planner)
    graph.add_node("executor", node_executor)
    graph.add_node("synthesizer", node_synthesizer)
    graph.add_node("verifier", node_verifier)
    graph.add_node("reporter", node_reporter)

    # Add edges
    graph.set_entry_point("query_analyzer")
    graph.add_edge("query_analyzer", "planner")
    graph.add_edge("planner", "executor")

    # Conditional edge - loop executor or move to synthesizer
    graph.add_conditional_edges(
        "executor",
        should_continue,
        {
            "continue": "executor",
            "synthesize": "synthesizer"
        }
    )

    graph.add_edge("synthesizer", "verifier")
    graph.add_edge("verifier", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


# ─── Run Agent ────────────────────────────────────────────────────────────────

def run_agent(query: str, failure_rate: float = 0.0) -> Dict[str, Any]:
    """
    Run the agent on a research query.

    Args:
        query: Research query string

    Returns:
        Final state with report
    """

    print(f"\n{'='*60}")
    print(f"ARA-1 AUTONOMOUS RESEARCH AGENT")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    # Initialize state
    initial_state: ResearchState = {
        "query": query,
        "query_type": "",
        "companies": [],
        "assumptions": [],
        "clean_query": query,
        "plan": [],
        "current_step": 0,
        "plan_revisions": 0,
        "gathered_data": {},
        "sources": [],
        "conflicts": [],
        "memory_hits": 0,
        "session_id": str(uuid.uuid4()),
        "synthesis": "",
        "draft_report": "",
        "verified_report": "",
        "final_report": "",
        "errors": [],
        "fallbacks_used": [],
        "tool_calls": 0,
        "failure_rate": failure_rate,
        "start_time": time.time()
    }

    # Build and run agent
    agent = build_agent()
    final_state = agent.invoke(initial_state)
    # Debug - check what final_report contains
    report = final_state.get("final_report", "")

    # Save session to episodic memory
    try:
        from memory.context_manager import ContextManager
        cm = ContextManager(initial_state["session_id"])
        cm.save_session(final_state)
        print(f"[Agent] Session saved to episodic memory")
    except Exception as e:
        print(f"[Agent] Could not save session: {e}")

    # Store final report in vector DB
    try:
        from memory.vector_store import vector_db_store
        companies = final_state.get("companies", [])
        ticker = companies[0] if companies else "unknown"
        report = final_state.get("final_report", "")
        if report and isinstance(report, str) and len(report) > 100:
            vector_db_store(
                content=report[:2000],
                metadata={
                    "ticker": ticker,
                    "source_type": "research_report",
                    "confidence": 0.8,
                    "session_id": initial_state["session_id"]
                }
            )
            print(f"[Agent] Report stored in long-term memory")
    except Exception as e:
        print(f"[Agent] Could not store report: {e}")

    return final_state