"""
Synthesis Package
Multi-source synthesis engine for ARA-1
"""

from synthesis.engine import synthesize_findings
from synthesis.conflict_resolver import resolve_data_conflicts, check_sentiment_fact_alignment
from synthesis.narrative import build_narrative, identify_themes