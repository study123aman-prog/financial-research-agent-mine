"""
Context Manager
Connects all three memory layers and manages data flow between them
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime


class ContextManager:
    """
    Manages all three memory layers:
    - Short-term: current session context
    - Long-term: ChromaDB vector store
    - Episodic: SQLite session history
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = time.time()

        from memory.short_term import ShortTermMemory
        self.short_term = ShortTermMemory()

        print(f"[Context Manager] Session started: {session_id}")

    def check_memory_first(self, query: str, ticker: str = None) -> Optional[Dict]:
        """
        Check long-term memory before making external API calls.
        Returns cached result if similarity is high enough.
        """

        from memory.vector_store import vector_db_search

        filter_dict = {"ticker": ticker} if ticker else None
        results = vector_db_search(query, top_k=3, filter=filter_dict)

        if results.get("results"):
            top_result = results["results"][0]
            similarity = top_result.get("similarity_score", 0)

            if similarity > 0.85:
                print(f"[Context Manager] Memory hit! Similarity: {similarity:.2f}")
                return top_result

        return None

    def store_finding(
        self,
        content: str,
        ticker: str,
        source_type: str,
        confidence: float = 0.7
    ):
        """Store a research finding in long-term memory"""

        from memory.vector_store import vector_db_store

        metadata = {
            "ticker": ticker,
            "source_type": source_type,
            "date": datetime.now().isoformat(),
            "confidence": confidence,
            "verified": False,
            "session_id": self.session_id
        }

        result = vector_db_store(content, metadata)
        return result

    def add_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """Add tool result to short-term memory"""
        self.short_term.add_tool_result(tool_name, result)

        if self.short_term.is_near_limit():
            self.short_term.compress()

    def get_context(self) -> str:
        """Get current context summary"""
        return self.short_term.get_context_summary()

    def save_session(
        self,
        state: Dict[str, Any],
        evaluation_score: float = 0.0
    ):
        """Save completed session to episodic memory"""

        from memory.episodic import save_session

        duration = time.time() - self.start_time
        report = state.get("final_report", "")
        report_length = len(str(report)) if report else 0

        session_data = {
            "session_id": self.session_id,
            "query": state.get("query", ""),
            "query_type": state.get("query_type", ""),
            "companies": state.get("companies", []),
            "plan": state.get("plan", []),
            "tools_used": list(state.get("gathered_data", {}).keys()),
            "tools_failed": [e.get("tool", "") for e in state.get("errors", [])],
            "fallbacks_triggered": state.get("fallbacks_used", []),
            "outcome": "completed",
            "evaluation_score": evaluation_score,
            "total_tool_calls": state.get("tool_calls", 0),
            "memory_hits": state.get("memory_hits", 0),
            "duration_seconds": duration,
            "report_length": report_length
        }

        save_session(session_data)
        print(f"[Context Manager] Session saved. Duration: {duration:.1f}s")

    def get_previous_research(self, ticker: str) -> List[Dict]:
        """Get previous research for a company"""

        from memory.episodic import get_previous_research
        return get_previous_research(ticker=ticker, limit=3)