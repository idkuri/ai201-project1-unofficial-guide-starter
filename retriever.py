import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

# Load embedding model once at module import. First run downloads ~90 MB;
# subsequent runs use the local cache.
_model = SentenceTransformer(EMBEDDING_MODEL)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
# No embedding_function — we pass pre-computed vectors via embeddings= / query_embeddings=
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks):
    """
    Embed a list of chunks and store them in the vector database.

    Uses SentenceTransformer to compute embeddings, then passes them explicitly
    to ChromaDB via collection.add(embeddings=...).
    """
    if not chunks:
        print("No chunks to embed.")
        return

    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts, show_progress_bar=True).tolist()

    _collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {k: v for k, v in c.items() if k not in ("text", "chunk_id")}
            for c in chunks
        ],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")


def retrieve(query, n_results=N_RESULTS):
    """
    Find the most relevant chunks for a user's question.

    Encodes the query with SentenceTransformer, then searches ChromaDB by
    cosine distance. Lower distance = more similar.
    """
    if _collection.count() == 0:
        return []

    query_embedding = _model.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        meta = results["metadatas"][0][i]
        entry = {
            "text": results["documents"][0][i],
            "source": meta.get("source", "unknown"),
            "distance": results["distances"][0][i],
        }
        for key in ("course", "date", "chunk_index"):
            if key in meta:
                entry[key] = meta[key]
        chunks.append(entry)
    return chunks


EVAL_QUERIES = [
    "Does Paul Fodor record his lectures for CSE 114?",
    "What Rate My Professor tags do students assign to Christopher Kane for CSE 307?",
    "What do students say about I.V. Ramakrishnan's CSE 596 class?",
]


def _print_retrieval_results(query, results):
    print(f"\nQuery: {query}")
    print("-" * 80)
    if not results:
        print("  (no results)")
        return
    for rank, chunk in enumerate(results, start=1):
        course = chunk.get("course", "unknown")
        print(
            f"\n  [{rank}] source={chunk['source']} | course={course} | "
            f"distance={chunk['distance']:.4f}"
        )
        print(chunk["text"])


def run_retrieval_tests():
    """Run evaluation queries and print chunks with distance scores."""
    for query in EVAL_QUERIES:
        results = retrieve(query)
        _print_retrieval_results(query, results)


if __name__ == "__main__":
    from ingest import chunk_document, load_documents

    if _collection.count() == 0:
        print("Vector store empty — embedding all chunks...")
        documents = load_documents()
        all_chunks = []
        for doc in documents:
            all_chunks.extend(chunk_document(doc["text"], doc["source"]))
        embed_and_store(all_chunks)
    else:
        print(f"Vector store already has {_collection.count()} chunks.")

    print("\n" + "=" * 80)
    print("RETRIEVAL TESTS")
    print("=" * 80)
    run_retrieval_tests()
