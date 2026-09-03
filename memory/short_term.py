"""
Short-Term Memory
Manages context window during a research session
"""

from typing import Dict, Any, List


class ShortTermMemory:
    """
    Manages the agent context window during a research session.
    Summarizes older content when approaching token limits.
    """

    def __init__(self, max_tokens: int = 80000):
        self.max_tokens = max_tokens
        self.messages: List[Dict] = []
        self.key_findings: List[str] = []
        self.total_tokens: int = 0

    def add_finding(self, finding: str, source: str, importance: str = "medium"):
        """Add a key finding to short-term memory"""
        self.key_findings.append({
            "finding": finding,
            "source": source,
            "importance": importance
        })

    def add_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """Add a tool result to context"""
        summary = self._summarize_result(tool_name, result)
        self.messages.append({
            "type": "tool_result",
            "tool": tool_name,
            "summary": summary,
            "tokens": len(summary.split()) * 2
        })
        self.total_tokens += len(summary.split()) * 2

    def get_context_summary(self) -> str:
        """Get a summary of current context"""
        if not self.key_findings and not self.messages:
            return "No research conducted yet."

        summary = "KEY FINDINGS SO FAR:\n"
        for i, finding in enumerate(self.key_findings[-10:], 1):
            summary += f"{i}. [{finding['source']}] {finding['finding']}\n"

        summary += f"\nTOOLS USED: {[m['tool'] for m in self.messages]}\n"
        summary += f"TOTAL CONTEXT SIZE: ~{self.total_tokens} tokens\n"

        return summary

    def is_near_limit(self) -> bool:
        """Check if approaching context window limit"""
        return self.total_tokens > (self.max_tokens * 0.8)

    def compress(self):
        """Compress older messages to save space"""
        if len(self.messages) > 10:
            old_messages = self.messages[:-5]
            compressed = f"[COMPRESSED: {len(old_messages)} earlier tool results]"
            self.messages = [{"type": "compressed", "summary": compressed}] + self.messages[-5:]
            print("[Short-Term] Context compressed to save space")

    def _summarize_result(self, tool_name: str, result: Dict) -> str:
        """Create a brief summary of a tool result"""
        if not result:
            return f"{tool_name}: No data returned"

        is_mock = result.get("is_mock", False)
        source = result.get("source", tool_name)
        mock_label = " (mock)" if is_mock else ""

        if tool_name == "company_profile":
            return f"Company Profile{mock_label}: {result.get('company_name', 'N/A')}, {result.get('sector', 'N/A')}, Market Cap: {result.get('market_cap', 'N/A')}"

        elif tool_name == "financial_data_api":
            reports = result.get("reports", [])
            if reports:
                latest = reports[0]
                return f"Financials{mock_label} [{source}]: Revenue {latest.get('totalRevenue', 'N/A')}, Net Income {latest.get('netIncome', 'N/A')}"
            return f"Financials{mock_label}: No reports available"

        elif tool_name == "stock_price":
            return f"Stock{mock_label}: ${result.get('current_price', 'N/A')}, P/E: {result.get('pe_ratio', 'N/A')}, Market Cap: {result.get('market_cap', 'N/A')}"

        elif tool_name == "news_sentiment":
            return f"News{mock_label}: {result.get('total_articles', 0)} articles, Sentiment: {result.get('overall_sentiment', 'N/A')}"

        elif tool_name == "sec_filing_search":
            return f"SEC Filing{mock_label}: {result.get('filing_type', 'N/A')} filed {result.get('filed_date', 'N/A')}"

        elif tool_name == "peer_comparison":
            peers = result.get("peers", [])
            return f"Peers{mock_label}: {', '.join(peers[:3])}"

        else:
            return f"{tool_name}{mock_label}: Data retrieved from {source}"

    def clear(self):
        """Clear all short-term memory"""
        self.messages = []
        self.key_findings = []
        self.total_tokens = 0