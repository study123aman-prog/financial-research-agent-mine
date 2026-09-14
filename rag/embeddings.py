"""
Embeddings
Generates vector embeddings for document chunks
"""

from typing import List, Dict, Any
import os


def get_embedder():
    """Get the sentence transformer embedding model"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        print(f"[Embeddings] Error loading model: {e}")
        return None


def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate embeddings for a list of chunks.

    Args:
        chunks: List of chunk dicts with 'content' field

    Returns:
        Chunks with 'embedding' field added
    """

    embedder = get_embedder()
    if not embedder:
        print("[Embeddings] No embedder available")
        return chunks

    texts = [chunk["content"] for chunk in chunks]

    try:
        embeddings = embedder.encode(texts, show_progress_bar=False)

        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()

        print(f"[Embeddings] Generated {len(chunks)} embeddings")
        return chunks

    except Exception as e:
        print(f"[Embeddings] Error: {e}")
        return chunks


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a search query.

    Args:
        query: Query text

    Returns:
        Embedding vector as list of floats
    """

    embedder = get_embedder()
    if not embedder:
        return []

    try:
        embedding = embedder.encode(query)
        return embedding.tolist()
    except Exception as e:
        print(f"[Embeddings] Query embedding error: {e}")
        return []