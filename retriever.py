import re

import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_COLLECTION,
    CHROMA_PATH,
    EMBEDDING_MODEL,
    HYBRID_CANDIDATE_POOL,
    HYBRID_RRF_K,
    N_RESULTS,
    RETRIEVAL_MODE,
)
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

_model = SentenceTransformer(EMBEDDING_MODEL)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
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


def _chunk_dict_from_store(chunk_id: str, document: str, meta: dict) -> dict:
    chunk = {
        "chunk_id": chunk_id,
        "text": document,
        "source": meta.get("source", "unknown"),
    }
    for key in ("course", "date", "chunk_index"):
        if key in meta:
            chunk[key] = meta[key]
    return chunk


def _results_to_chunks(results) -> list[dict]:
    chunks = []
    for i, chunk_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        entry = _chunk_dict_from_store(
            chunk_id, results["documents"][0][i], meta
        )
        entry["distance"] = results["distances"][0][i]
        chunks.append(entry)
    return chunks


def _fetch_corpus(where: dict | None) -> list[dict]:
    """Load all chunks matching a metadata filter (or entire collection)."""
    kwargs = {"include": ["documents", "metadatas"]}
    if where:
        kwargs["where"] = where
    data = _collection.get(**kwargs)
    return [
        _chunk_dict_from_store(chunk_id, doc, meta)
        for chunk_id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
    ]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _semantic_search(
    query: str, where: dict | None, n_results: int
) -> list[dict]:
    query_embedding = _model.encode([query]).tolist()
    pool = min(_collection.count(), max(n_results, HYBRID_CANDIDATE_POOL))
    if _is_courses_list_query(query) and where:
        pool = _collection.count()

    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=pool,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return _results_to_chunks(results)


def _bm25_search(query: str, where: dict | None, n_results: int) -> list[dict]:
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise ImportError(
            "Hybrid retrieval requires rank-bm25. Run: pip install rank-bm25"
        ) from exc

    corpus = _fetch_corpus(where)
    if not corpus:
        return []

    tokenized = [_tokenize(build_embedding_text(chunk)) for chunk in corpus]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(_tokenize(query))

    ranked = sorted(
        zip(corpus, scores),
        key=lambda pair: pair[1],
        reverse=True,
    )[:n_results]

    chunks = []
    max_score = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
    for chunk, score in ranked:
        entry = dict(chunk)
        # Lower pseudo-distance so hybrid chunks pass the same filters as semantic.
        entry["distance"] = 1.0 - (score / max_score)
        entry["bm25_score"] = float(score)
        chunks.append(entry)
    return chunks


def _rrf_merge(
    semantic_chunks: list[dict],
    keyword_chunks: list[dict],
    n_results: int,
) -> list[dict]:
    """Reciprocal Rank Fusion over semantic and BM25 rankings."""
    scores: dict[str, float] = {}
    refs: dict[str, dict] = {}

    for rank, chunk in enumerate(semantic_chunks, start=1):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (HYBRID_RRF_K + rank)
        refs[cid] = chunk

    for rank, chunk in enumerate(keyword_chunks, start=1):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (HYBRID_RRF_K + rank)
        refs.setdefault(cid, chunk)

    merged = []
    for cid in sorted(scores, key=scores.get, reverse=True)[:n_results]:
        entry = dict(refs[cid])
        entry["rrf_score"] = scores[cid]
        merged.append(entry)
    return merged


def retrieve(query, n_results=N_RESULTS, mode: str | None = None):
    """
    Find the most relevant chunks for a user's question.

    mode: "semantic" (cosine only) or "hybrid" (semantic + BM25 via RRF).
    """
    if _collection.count() == 0:
        return []

    mode = mode or RETRIEVAL_MODE
    where = _build_where_filter(query)

    if _is_courses_list_query(query) and where:
        semantic = _semantic_search(query, where, _collection.count())
        if mode == "hybrid":
            keyword = _bm25_search(query, where, HYBRID_CANDIDATE_POOL)
            merged = _rrf_merge(semantic, keyword, _collection.count())
            return _dedupe_by_course(merged)[:n_results]
        return _dedupe_by_course(semantic)[:n_results]

    if mode == "hybrid":
        semantic = _semantic_search(query, where, HYBRID_CANDIDATE_POOL)
        keyword = _bm25_search(query, where, HYBRID_CANDIDATE_POOL)
        return _rrf_merge(semantic, keyword, n_results)

    results = _collection.query(
        query_embeddings=_model.encode([query]).tolist(),
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

# Short label for whether top result looks on-target for comparison reports.
_EVAL_EXPECTED_HINT = {
    "Does Paul Fodor record his lectures for CSE 114?": "record",
    "What Rate My Professor tags do students assign to Christopher Kane for CSE 307?": "TOUGH GRADER",
    "What courses does Scott Stoller teach according to student reviews?": "CSE535",
    "What do students say about I.V. Ramakrishnan's CSE 596 class?": "CSE596",
    "How does Ali Raza prepare students for exams in ISE 218?": "topics",
}


def _print_retrieval_results(query, results, label=""):
    title = f"\nQuery: {query}"
    if label:
        title += f" [{label}]"
    print(title)
    print("-" * 80)
    if not results:
        print("  (no results)")
        return
    for rank, chunk in enumerate(results, start=1):
        course = chunk.get("course", "unknown")
        dist = chunk.get("distance", 0)
        print(
            f"\n  [{rank}] source={chunk['source']} | course={course} | "
            f"distance={dist:.4f}"
        )
        print(chunk["text"][:200] + ("..." if len(chunk["text"]) > 200 else ""))


def compare_retrieval_modes():
    """Compare semantic-only vs hybrid top-1 on all eval queries."""
    print("\n" + "=" * 80)
    print("HYBRID vs SEMANTIC COMPARISON (top-1)")
    print("=" * 80)
    print(f"{'Query':<55} {'Semantic':<12} {'Hybrid':<12} {'Winner'}")
    print("-" * 80)

    for query in EVAL_QUERIES:
        hint = _EVAL_EXPECTED_HINT.get(query, "").lower()
        sem = retrieve(query, mode="semantic")
        hyb = retrieve(query, mode="hybrid")

        sem_ok = bool(sem and hint in sem[0]["text"].lower())
        hyb_ok = bool(hyb and hint in hyb[0]["text"].lower())

        if sem_ok and not hyb_ok:
            winner = "semantic"
        elif hyb_ok and not sem_ok:
            winner = "hybrid"
        elif sem_ok and hyb_ok:
            winner = "tie"
        else:
            winner = "neither"

        short_q = query[:52] + "..." if len(query) > 55 else query
        print(f"{short_q:<55} {str(sem_ok):<12} {str(hyb_ok):<12} {winner}")

        if sem:
            s0 = sem[0]
            print(
                f"  semantic #1: {s0.get('source')} ({s0.get('course')}) "
                f"{s0.get('date', '')}"
            )
        if hyb:
            h0 = hyb[0]
            print(
                f"  hybrid   #1: {h0.get('source')} ({h0.get('course')}) "
                f"{h0.get('date', '')}"
            )
        print()


def run_retrieval_tests(mode: str | None = None):
    """Run evaluation queries and print chunks with distance scores."""
    label = mode or RETRIEVAL_MODE
    for query in EVAL_QUERIES:
        results = retrieve(query, mode=label)
        _print_retrieval_results(query, results, label=label)


if __name__ == "__main__":
    import sys

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

    if "--compare" in sys.argv:
        compare_retrieval_modes()
    else:
        print("\n" + "=" * 80)
        print("RETRIEVAL TESTS")
        print("=" * 80)
        run_retrieval_tests()
