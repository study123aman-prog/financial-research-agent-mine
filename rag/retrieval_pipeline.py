"""
RAG Retrieval Pipeline
Multi-stage retrieval pipeline for financial research
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def run_retrieval_pipeline(
    query: str,
    ticker: str = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Run the full RAG retrieval pipeline.

    Stage 1: Query transformation
    Stage 2: Memory check (ChromaDB first)
    Stage 3: External API retrieval if memory miss
    Stage 4: Relevance filtering
    Stage 5: Context assembly

    Args:
        query: Research query
        ticker: Company ticker for filtering
        top_k: Number of results to return

    Returns:
        Assembled context ready for LLM
    """

    print(f"[RAG Pipeline] Starting retrieval for: {query[:50]}")

    # Stage 1: Query transformation
    sub_queries = transform_query(query)
    print(f"[RAG Pipeline] Stage 1: Generated {len(sub_queries)} sub-queries")

    # Stage 2: Search long-term memory first
    memory_results = search_memory(sub_queries, ticker, top_k)
    print(f"[RAG Pipeline] Stage 2: Found {len(memory_results)} memory results")

    # Stage 3: Filter by relevance
    filtered = filter_by_relevance(memory_results, query, threshold=0.3)
    print(f"[RAG Pipeline] Stage 3: {len(filtered)} results after filtering")

    # Stage 4: Assemble context with token budget
    context = assemble_context(filtered, query)
    print(f"[RAG Pipeline] Stage 4: Context assembled ({len(context['text'])} chars)")

    return context


def transform_query(query: str) -> List[str]:
    """
    Stage 1: Transform raw query into specific retrieval queries.
    Decomposes complex queries into 3-5 targeted sub-queries.
    """

    # Extract company names and key concepts
    import re

    sub_queries = [query]

    # Add financial-specific sub-queries
    financial_terms = ["revenue", "earnings", "profit", "risk", "growth"]
    for term in financial_terms:
        if term not in query.lower():
            continue
        sub_queries.append(f"{query} {term} analysis")

    # Add time-specific queries
    sub_queries.append(f"{query} 2024 2025")
    sub_queries.append(f"{query} financial performance")

    return sub_queries[:5]


def search_memory(
    sub_queries: List[str],
    ticker: str = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Stage 2: Search ChromaDB for relevant past research.
    Returns combined results from all sub-queries.
    """

    from memory.vector_store import vector_db_search

    all_results = []
    seen_ids = set()

    for sub_query in sub_queries:
        filter_dict = {"ticker": ticker} if ticker else None
        results = vector_db_search(sub_query, top_k=top_k, filter=filter_dict)

        for r in results.get("results", []):
            content = r.get("content", "")
            content_id = hash(content[:100])

            if content_id not in seen_ids:
                seen_ids.add(content_id)
                all_results.append(r)

    return all_results


def filter_by_relevance(
    results: List[Dict],
    query: str,
    threshold: float = 0.3
) -> List[Dict]:
    """
    Stage 3: Filter results by relevance score.
    Remove documents below relevance threshold.
    """

    filtered = []

    for result in results:
        similarity = result.get("similarity_score", 0)
        if similarity >= threshold:
            filtered.append(result)

    # Sort by similarity score
    filtered.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

    return filtered


def assemble_context(
    results: List[Dict],
    query: str,
    max_chars: int = 8000
) -> Dict[str, Any]:
    """
    Stage 4: Assemble context with token budget allocation.

    Token budget:
    40% primary data (filings, financials)
    30% supporting evidence (news, transcripts)
    20% system prompt space (reserved)
    10% generation space (reserved)

    Available for context: 70% of max_chars
    """

    available = int(max_chars * 0.7)
    primary_budget = int(available * 0.57)    # 40/70
    supporting_budget = int(available * 0.43)  # 30/70

    primary_sources = ["sec_filing", "financial_api", "research_report"]
    supporting_sources = ["news", "earnings_transcript", "web_search"]

    primary_chunks = []
    supporting_chunks = []

    for result in results:
        source_type = result.get("source_type", result.get("metadata", {}).get("source_type", ""))
        if any(s in source_type for s in primary_sources):
            primary_chunks.append(result)
        else:
            supporting_chunks.append(result)

    # Build context text
    context_parts = []
    chars_used = 0

    # Add primary sources first
    for chunk in primary_chunks:
        content = chunk.get("content", "")
        if chars_used + len(content) <= primary_budget:
            source = chunk.get("metadata", {}).get("source_type", "unknown")
            ticker = chunk.get("metadata", {}).get("ticker", "")
            date = chunk.get("metadata", {}).get("date", "")
            context_parts.append(
                f"[Source: {source} | Company: {ticker} | Date: {date}]\n{content}"
            )
            chars_used += len(content)

    # Add supporting sources
    for chunk in supporting_chunks:
        content = chunk.get("content", "")
        if chars_used + len(content) <= primary_budget + supporting_budget:
            source = chunk.get("metadata", {}).get("source_type", "unknown")
            ticker = chunk.get("metadata", {}).get("ticker", "")
            context_parts.append(
                f"[Source: {source} | Company: {ticker}]\n{content}"
            )
            chars_used += len(content)

    context_text = "\n\n---\n\n".join(context_parts)

    return {
        "text": context_text,
        "total_chunks": len(results),
        "primary_chunks": len(primary_chunks),
        "supporting_chunks": len(supporting_chunks),
        "chars_used": chars_used,
        "query": query,
        "has_memory_results": len(results) > 0
    }


def store_research_findings(
    content: str,
    ticker: str,
    source_type: str,
    confidence: float = 0.7
) -> bool:
    """
    Store research findings in ChromaDB after chunking and embedding.

    Args:
        content: Research content to store
        ticker: Company ticker
        source_type: Type of source
        confidence: Confidence score 0-1

    Returns:
        True if stored successfully
    """

    from rag.chunking import chunk_document
    from memory.vector_store import vector_db_store
    from datetime import datetime

    metadata = {
        "ticker": ticker,
        "source_type": source_type,
        "date": datetime.now().isoformat(),
        "confidence": confidence,
        "session_id": "rag_pipeline"
    }

    # Chunk the content
    chunks = chunk_document(content, source_type, metadata)

    # Store each chunk
    stored = 0
    for chunk in chunks:
        result = vector_db_store(
            content=chunk["content"],
            metadata={
                "ticker": ticker,
                "source_type": source_type,
                "date": metadata["date"],
                "confidence": confidence,
                "session_id": metadata["session_id"]
            }
        )
        if result.get("success"):
            stored += 1

    print(f"[RAG Pipeline] Stored {stored}/{len(chunks)} chunks for {ticker}")
    return stored > 0