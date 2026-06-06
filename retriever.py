import re

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS
from ingest import build_embedding_text

# Map spoken names in queries to document source slugs.
_PROFESSOR_SLUGS = (
    ("christopher kane", "christopher_kane"),
    ("i.v. ramakrishnan", "iv_ramakrishnan"),
    ("i v ramakrishnan", "iv_ramakrishnan"),
    ("iv ramakrishnan", "iv_ramakrishnan"),
    ("dimitris samaras", "dimitris_samaras"),
    ("himanshu gupta", "himanshu_gupta"),
    ("michael ferdman", "michael_ferdman"),
    ("scott stoller", "scott_stoller"),
    ("eugene stark", "eugene_stark"),
    ("amir rahmati", "amir_rahmati"),
    ("paul fodor", "paul_fodor"),
    ("ali raza", "ali_raza"),
)

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

    Uses compact review text for embeddings while storing the full chunk for
    retrieval display. Passes pre-computed vectors to ChromaDB via embeddings=.
    """
    if not chunks:
        print("No chunks to embed.")
        return

    texts = [c["text"] for c in chunks]
    embed_texts = [build_embedding_text(c) for c in chunks]
    embeddings = _model.encode(embed_texts, show_progress_bar=True).tolist()

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


def _normalize_query(query: str) -> str:
    return query.lower().replace("i.v.", "iv").replace("i. v.", "iv")


def _detect_professor_slug(query: str) -> str | None:
    q = _normalize_query(query)
    for name, slug in _PROFESSOR_SLUGS:
        if name in q:
            return slug
    return None


def _normalize_course_code(course: str) -> str:
    code = course.upper().replace(" ", "")
    match = re.fullmatch(r"(CSE|ISE|CS)(\d+)", code)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    if re.fullmatch(r"\d+", code):
        return f"CSE{code}"
    return code


def _detect_course_code(query: str) -> str | None:
    match = re.search(r"\b((?:CSE|ISE|CS)\s*\d{2,4})\b", query, re.IGNORECASE)
    if match:
        return _normalize_course_code(match.group(1))
    return None


def _course_variants(course: str) -> list[str]:
    normalized = _normalize_course_code(course)
    variants = {normalized, course.upper().replace(" ", "")}
    match = re.fullmatch(r"(CSE|ISE|CS)(\d+)", normalized)
    if match:
        variants.add(match.group(2))
        if match.group(1) == "CS":
            variants.add(f"CSE{match.group(2)}")
    return sorted(variants)


def _build_where_filter(query: str) -> dict | None:
    source = _detect_professor_slug(query)
    course = _detect_course_code(query)
    if not source and not course:
        return None

    clauses = []
    if source:
        clauses.append({"source": source})
    if course:
        variants = _course_variants(course)
        if len(variants) == 1:
            clauses.append({"course": variants[0]})
        else:
            clauses.append({"$or": [{"course": variant} for variant in variants]})

    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _is_courses_list_query(query: str) -> bool:
    return bool(re.search(r"\bcourses\b", query, re.I) and _detect_professor_slug(query))


def _dedupe_by_course(chunks: list[dict]) -> list[dict]:
    """Keep the closest chunk for each course code."""
    best_by_course: dict[str, dict] = {}
    for chunk in chunks:
        course_key = _normalize_course_code(chunk.get("course") or "unknown")
        current = best_by_course.get(course_key)
        if current is None or chunk["distance"] < current["distance"]:
            best_by_course[course_key] = chunk
    return sorted(best_by_course.values(), key=lambda chunk: chunk["distance"])


def _results_to_chunks(results) -> list[dict]:
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


def retrieve(query, n_results=N_RESULTS):
    """
    Find the most relevant chunks for a user's question.

    Encodes the query with SentenceTransformer, then searches ChromaDB by
    cosine distance. When a professor or course is named in the query, search
    is scoped to matching metadata first.
    """
    if _collection.count() == 0:
        return []

    where = _build_where_filter(query)
    query_embedding = _model.encode([query]).tolist()

    if _is_courses_list_query(query) and where:
        pool_size = _collection.count()
        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=pool_size,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return _dedupe_by_course(_results_to_chunks(results))[:n_results]

    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return _results_to_chunks(results)


EVAL_QUERIES = [
    "Does Paul Fodor record his lectures for CSE 114?",
    "What Rate My Professor tags do students assign to Christopher Kane for CSE 307?",
    "What courses does Scott Stoller teach according to student reviews?",
    "What do students say about I.V. Ramakrishnan's CSE 596 class?",
    "How does Ali Raza prepare students for exams in ISE 218?",
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
