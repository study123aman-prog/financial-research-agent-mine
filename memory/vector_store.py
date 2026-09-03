"""
Vector Store - Long-Term Memory
Uses ChromaDB to store and retrieve research findings
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def _get_client():
    """Get or create ChromaDB client"""
    import chromadb
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)


def _get_collection():
    """Get or create the research collection"""
    client = _get_client()
    return client.get_or_create_collection(
        name="ara1_research",
        metadata={"description": "ARA-1 long-term research memory"}
    )


def _get_embedder():
    """Get sentence transformer embedder"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        print(f"[Vector Store] Embedder error: {e}")
        return None


def vector_db_store(
    content: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store research findings in ChromaDB.

    Args:
        content: Text content to store
        metadata: Dict with ticker, source_type, date, confidence

    Returns:
        Storage confirmation with document ID
    """

    try:
        collection = _get_collection()
        embedder = _get_embedder()

        if not embedder:
            return {
                "success": False,
                "error": "Embedder not available",
                "document_id": None
            }

        # Generate unique ID
        doc_id = f"{metadata.get('ticker', 'unknown')}-{metadata.get('source_type', 'unknown')}-{uuid.uuid4().hex[:8]}"

        # Generate embedding
        embedding = embedder.encode(content).tolist()

        # Clean metadata - ChromaDB only accepts str, int, float, bool
        clean_metadata = {
            "ticker": str(metadata.get("ticker", "unknown")),
            "source_type": str(metadata.get("source_type", "unknown")),
            "date": str(metadata.get("date", datetime.now().isoformat())),
            "confidence": float(metadata.get("confidence", 0.7)),
            "verified": bool(metadata.get("verified", False)),
            "session_id": str(metadata.get("session_id", "unknown")),
            "stored_at": datetime.now().isoformat()
        }

        # Store in ChromaDB
        collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[clean_metadata],
            ids=[doc_id]
        )

        print(f"[Vector Store] Stored: {doc_id}")

        return {
            "success": True,
            "document_id": doc_id,
            "ticker": clean_metadata["ticker"],
            "source_type": clean_metadata["source_type"],
            "source": "ChromaDB",
            "reliability_tier": 1
        }

    except Exception as e:
        print(f"[Vector Store] Store error: {e}")
        return {
            "success": False,
            "error": str(e),
            "document_id": None
        }


def vector_db_search(
    query: str,
    top_k: int = 5,
    filter: Dict = None
) -> Dict[str, Any]:
    """
    Search ChromaDB for relevant research findings.

    Args:
        query: Search query text
        top_k: Number of results to return
        filter: Optional metadata filter dict

    Returns:
        Relevant document chunks with similarity scores
    """

    try:
        collection = _get_collection()
        embedder = _get_embedder()

        if not embedder:
            return {
                "results": [],
                "total_found": 0,
                "message": "Embedder not available"
            }

        # Check if collection has any documents
        count = collection.count()
        if count == 0:
            return {
                "results": [],
                "total_found": 0,
                "message": "Memory is empty - no previous research found"
            }

        # Generate query embedding
        query_embedding = embedder.encode(query).tolist()

        # Build query params
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, count)
        }

        if filter:
            query_params["where"] = filter

        # Search
        results = collection.query(**query_params)

        # Format results
        formatted = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1 - dist  # Convert distance to similarity
            formatted.append({
                "content": doc,
                "metadata": meta,
                "similarity_score": round(float(similarity), 3),
                "ticker": meta.get("ticker", "unknown"),
                "source_type": meta.get("source_type", "unknown"),
                "date": meta.get("date", "unknown")
            })

        print(f"[Vector Store] Found {len(formatted)} results for: {query[:50]}")

        return {
            "results": formatted,
            "total_found": len(formatted),
            "query": query,
            "source": "ChromaDB",
            "reliability_tier": 1
        }

    except Exception as e:
        print(f"[Vector Store] Search error: {e}")
        return {
            "results": [],
            "total_found": 0,
            "error": str(e)
        }


def get_memory_stats() -> Dict[str, Any]:
    """Get statistics about what is stored in memory"""
    try:
        collection = _get_collection()
        count = collection.count()
        return {
            "total_documents": count,
            "collection_name": "ara1_research",
            "status": "active"
        }
    except Exception as e:
        return {
            "total_documents": 0,
            "error": str(e)
        }