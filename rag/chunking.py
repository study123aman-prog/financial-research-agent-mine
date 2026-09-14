"""
Chunking Strategy
Splits financial documents into semantic chunks for embedding
"""

from typing import List, Dict, Any
import re


def chunk_document(
    content: str,
    source_type: str,
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Chunk a document based on its source type.

    Args:
        content: Raw document text
        source_type: sec_filing, earnings_transcript, news, financial
        metadata: Document metadata

    Returns:
        List of chunks with metadata
    """

    if source_type == "sec_filing":
        return chunk_sec_filing(content, metadata)
    elif source_type == "earnings_transcript":
        return chunk_transcript(content, metadata)
    elif source_type == "news":
        return chunk_news(content, metadata)
    else:
        return chunk_generic(content, metadata)


def chunk_sec_filing(content: str, metadata: Dict) -> List[Dict]:
    """
    Chunk SEC filings by section.
    Sections: Risk Factors, MD&A, Financial Statements
    """

    sections = {
        "risk_factors": r'(?i)(item\s+1a[\.\s]+risk\s+factors)(.*?)(?=item\s+1b|item\s+2|\Z)',
        "mda": r'(?i)(item\s+7[\.\s]+management.*?discussion)(.*?)(?=item\s+7a|item\s+8|\Z)',
        "financials": r'(?i)(item\s+8[\.\s]+financial\s+statements)(.*?)(?=item\s+9|\Z)'
    }

    chunks = []

    for section_name, pattern in sections.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_text = match.group(2).strip()
            if len(section_text) > 100:
                # Split long sections into sub-chunks of ~1000 chars
                sub_chunks = _split_by_length(section_text, 1000)
                for i, chunk in enumerate(sub_chunks):
                    chunks.append({
                        "content": chunk,
                        "chunk_id": f"{section_name}_{i}",
                        "section": section_name,
                        "source_type": "sec_filing",
                        **metadata
                    })

    # If no sections found, chunk generically
    if not chunks:
        return chunk_generic(content, metadata)

    return chunks


def chunk_transcript(content: str, metadata: Dict) -> List[Dict]:
    """
    Chunk earnings transcripts by Q&A pair.
    Each question + answer = one chunk.
    """

    chunks = []

    # Split by speaker turns
    turns = re.split(r'\n(?=[A-Z][A-Z\s]+:)', content)

    current_qa = []
    for turn in turns:
        current_qa.append(turn.strip())

        # Every 2 turns (Q + A) = one chunk
        if len(current_qa) >= 2:
            chunk_text = "\n".join(current_qa)
            if len(chunk_text) > 50:
                chunks.append({
                    "content": chunk_text,
                    "chunk_id": f"qa_{len(chunks)}",
                    "section": "earnings_qa",
                    "source_type": "earnings_transcript",
                    **metadata
                })
            current_qa = []

    # Add remaining
    if current_qa:
        chunk_text = "\n".join(current_qa)
        if len(chunk_text) > 50:
            chunks.append({
                "content": chunk_text,
                "chunk_id": f"qa_{len(chunks)}",
                "section": "earnings_closing",
                "source_type": "earnings_transcript",
                **metadata
            })

    if not chunks:
        return chunk_generic(content, metadata)

    return chunks


def chunk_news(content: str, metadata: Dict) -> List[Dict]:
    """
    Chunk news articles by paragraph.
    Headline + first paragraph always included in each chunk.
    """

    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    if not paragraphs:
        return chunk_generic(content, metadata)

    headline = paragraphs[0]
    chunks = []

    for i, para in enumerate(paragraphs[1:], 1):
        if len(para) > 30:
            # Include headline context in every chunk
            chunk_text = f"{headline}\n\n{para}"
            chunks.append({
                "content": chunk_text,
                "chunk_id": f"para_{i}",
                "section": "news_paragraph",
                "source_type": "news",
                **metadata
            })

    if not chunks:
        chunks.append({
            "content": content[:2000],
            "chunk_id": "full_article",
            "section": "news_full",
            "source_type": "news",
            **metadata
        })

    return chunks


def chunk_generic(content: str, metadata: Dict) -> List[Dict]:
    """Generic chunking by length for any document type"""

    sub_chunks = _split_by_length(content, 800)
    chunks = []

    for i, chunk in enumerate(sub_chunks):
        if chunk.strip():
            chunks.append({
                "content": chunk,
                "chunk_id": f"chunk_{i}",
                "section": "general",
                "source_type": metadata.get("source_type", "unknown"),
                **metadata
            })

    return chunks


def _split_by_length(text: str, max_length: int) -> List[str]:
    """Split text into chunks of max_length characters"""

    if len(text) <= max_length:
        return [text]

    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= max_length:
            current += " " + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_length]]