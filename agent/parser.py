"""
Response Parser
Parses LLM outputs into structured data
"""

import re
from typing import Dict, Any, Optional


def parse_tool_call(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse a tool call from LLM response.

    Args:
        response: Raw LLM response text

    Returns:
        Dictionary with tool name and inputs, or None
    """

    # Look for tool call pattern
    tool_pattern = r'TOOL:\s*(\w+)\s*INPUTS:\s*(\{.*?\})'
    match = re.search(tool_pattern, response, re.DOTALL)

    if match:
        tool_name = match.group(1).strip()
        inputs_str = match.group(2).strip()

        try:
            import json
            inputs = json.loads(inputs_str)
            return {"tool": tool_name, "inputs": inputs}
        except Exception:
            return {"tool": tool_name, "inputs": {}}

    return None


def parse_final_answer(response: str) -> Optional[str]:
    """
    Check if LLM response contains a final answer.

    Args:
        response: Raw LLM response text

    Returns:
        Final answer text or None
    """

    if "FINAL ANSWER:" in response:
        parts = response.split("FINAL ANSWER:", 1)
        return parts[1].strip()

    return None


def parse_thought(response: str) -> str:
    """
    Extract thought/reasoning from LLM response.

    Args:
        response: Raw LLM response text

    Returns:
        Thought text
    """

    if "THOUGHT:" in response:
        parts = response.split("THOUGHT:", 1)
        thought = parts[1].split("\n")[0].strip()
        return thought

    return response[:200]


def extract_numbers(text: str) -> list:
    """
    Extract all numerical values from text.

    Args:
        text: Input text

    Returns:
        List of numerical strings found
    """

    pattern = r'\$?[\d,]+\.?\d*\s*(?:billion|million|thousand|percent|%|B|M|K)?'
    return re.findall(pattern, text, re.IGNORECASE)


def clean_response(response: str) -> str:
    """
    Clean and normalize LLM response text.

    Args:
        response: Raw response

    Returns:
        Cleaned response
    """

    # Remove excessive whitespace
    response = re.sub(r'\n{3,}', '\n\n', response)
    response = response.strip()
    return response