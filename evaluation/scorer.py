"""
LLM-based Scorer
Uses Gemini to assess qualitative metrics
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def llm_judge_report(
    report: str,
    query: str,
    sources: list
) -> Dict[str, Any]:
    """
    Use Gemini as an LLM judge to score qualitative aspects.

    Args:
        report: The research report to evaluate
        query: Original research query
        sources: Sources used

    Returns:
        Qualitative scores and feedback
    """

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        prompt = f"""You are evaluating a financial research report.

Original Query: {query}

Report to evaluate (first 2000 chars):
{report[:2000]}

Rate the following on a scale of 0.0 to 1.0:

1. ANALYTICAL_DEPTH: Does the report go beyond summarizing facts to provide genuine insights?
2. NARRATIVE_QUALITY: Is the report well-written and professionally structured?
3. INSIGHT_ORIGINALITY: Does the report identify non-obvious patterns or connections?
4. ACTIONABILITY: Would this report be useful to a financial analyst?

Respond in exactly this format:
ANALYTICAL_DEPTH: [score]
NARRATIVE_QUALITY: [score]
INSIGHT_ORIGINALITY: [score]
ACTIONABILITY: [score]
FEEDBACK: [one sentence of key feedback]
"""

        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            text = content[0].text if hasattr(content[0], 'text') else str(content[0])
        else:
            text = str(content)

        return _parse_llm_scores(text)

    except Exception as e:
        print(f"[Scorer] LLM judge error: {e}")
        return {
            "analytical_depth": 0.7,
            "narrative_quality": 0.7,
            "insight_originality": 0.6,
            "actionability": 0.7,
            "feedback": "LLM judge unavailable - using default scores",
            "llm_judge_available": False
        }


def _parse_llm_scores(text: str) -> Dict[str, Any]:
    """Parse LLM judge response"""

    import re
    result = {
        "llm_judge_available": True
    }

    patterns = {
        "analytical_depth": r'ANALYTICAL_DEPTH:\s*([\d.]+)',
        "narrative_quality": r'NARRATIVE_QUALITY:\s*([\d.]+)',
        "insight_originality": r'INSIGHT_ORIGINALITY:\s*([\d.]+)',
        "actionability": r'ACTIONABILITY:\s*([\d.]+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            try:
                result[key] = float(match.group(1))
            except ValueError:
                result[key] = 0.7
        else:
            result[key] = 0.7

    feedback_match = re.search(r'FEEDBACK:\s*(.+)', text)
    result["feedback"] = feedback_match.group(1).strip() if feedback_match else "No feedback provided"

    return result