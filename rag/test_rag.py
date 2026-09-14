from rag.chunking import chunk_document
from rag.embeddings import embed_chunks, embed_query
from rag.retrieval_pipeline import run_retrieval_pipeline, store_research_findings

# Test chunking
text = (
    'Microsoft reported revenue of 211 billion dollars. '
    'The company showed strong growth in cloud services. '
    'Azure revenue grew 29 percent year over year.'
)
chunks = chunk_document(text, 'news', {'ticker': 'MSFT', 'source_type': 'news', 'session_id': 'test'})
print(f'Chunks created: {len(chunks)}')

# Test embedding
embedded = embed_chunks(chunks)
print(f'Embeddings generated: {len(embedded)}')
print(f'Embedding dimensions: {len(embedded[0]["embedding"])}')

# Test store
stored = store_research_findings(text, 'MSFT', 'news', 0.8)
print(f'Stored: {stored}')

# Test retrieval
results = run_retrieval_pipeline('Microsoft cloud revenue growth', ticker='MSFT')
print(f'Pipeline results: {results["total_chunks"]} chunks')
print(f'Context length: {results["chars_used"]} chars')
print('RAG pipeline test passed')