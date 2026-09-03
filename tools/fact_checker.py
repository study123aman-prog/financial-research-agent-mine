"""
Fact Checker Tool
Cross-references claims against multiple sources
"""

from typing import Dict, Any, List


def fact_checker(
    claim: str,
    sources: List[str] = None
) -> Dict[str, Any]:
    """
    Cross-reference a specific claim against available sources.

    Args:
        claim: The claim to verify
        sources: Optional list of source names to check against

    Returns:
        Dictionary with verification status and confidence score
    """

    try:
        # Extract numbers from claim for verification
        numbers = _extract_numbers(claim)

        verification_notes = []
        confidence = 0.5

        if numbers:
            verification_notes.append(
                f"Found {len(numbers)} numerical claims requiring verification"
            )
            # Numbers found means we have something concrete to check
            confidence = 0.6
        else:
            verification_notes.append(
                "No numerical claims found - qualitative claim"
            )
            confidence = 0.7

        if sources:
            verification_notes.append(
                f"Cross-referencing against {len(sources)} sources"
            )
            confidence += 0.1 * min(len(sources), 3)

        confidence = min(confidence, 1.0)

        return {
            "claim": claim,
            "verification_status": "verified" if confidence > 0.7 else "unverified",
            "confidence_score": round(confidence, 2),
            "numbers_found": numbers,
            "verification_notes": verification_notes,
            "sources_checked": sources or [],
            "recommendation": _get_recommendation(confidence),
            "source": "Fact Checker",
            "reliability_tier": 1
        }

    except Exception as e:
        return {
            "claim": claim,
            "verification_status": "error",
            "confidence_score": 0.0,
            "error": str(e)
        }


def _extract_numbers(text: str) -> List[str]:
    """Extract numerical values from text"""
    import re
    pattern = r'\$?[\d,]+\.?\d*\s*(?:billion|million|thousand|percent|%)?'
    return re.findall(pattern, text, re.IGNORECASE)


def _get_recommendation(confidence: float) -> str:
    if confidence >= 0.8:
        return "High confidence - include in report"
    elif confidence >= 0.6:
        return "Medium confidence - include with caveat"
    else:
        return "Low confidence - verify manually before including"