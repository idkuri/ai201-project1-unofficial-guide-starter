from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

# Drop chunks with weak cosine distance before sending to the LLM.
MAX_DISTANCE = 0.55

SYSTEM_PROMPT = """You are a research assistant that answers questions about Stony Brook CS professors using ONLY the student review excerpts provided by the user.

STRICT RULES — you MUST follow all of these:
1. Use ONLY facts explicitly stated in the RETRIEVED REVIEWS. Do not add outside knowledge.
2. Do NOT guess, generalize, or rely on what is "typical" for professors, courses, or universities.
3. If the reviews do not contain enough information to answer the question, respond with EXACTLY this sentence and nothing else:
   I don't have enough information in the loaded documents to answer that.
4. Do NOT list sources, filenames, or citations — source attribution is added separately by the system.
5. When the reviews do contain the answer, quote or closely paraphrase specific details (course codes, tags, ratings, dates, student comments).
6. Never invent professor names, courses, tags, or review content not present in the reviews."""

NO_CHUNKS_MESSAGE = (
    "I don't have enough information in the loaded documents to answer that. "
    "No relevant reviews were retrieved — try rephrasing your question."
)

WEAK_MATCH_MESSAGE = (
    "I don't have enough information in the loaded documents to answer that. "
    "The retrieved reviews did not closely match your question."
)


def _format_source(chunk: dict) -> str:
    """Build a human-readable source label from chunk metadata."""
    source = chunk["source"].replace("_", " ").title()
    course = chunk.get("course")
    if course:
        return f"{source} ({course})"
    return source


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        label = _format_source(chunk)
        parts.append(f"[Review {i} — {label}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _filter_chunks(chunks: list[dict]) -> list[dict]:
    """Keep chunks with strong semantic match; fall back to top result if all are weak."""
    strong = [c for c in chunks if c["distance"] <= MAX_DISTANCE]
    return strong if strong else chunks[:1]


def generate_response(query: str, retrieved_chunks: list[dict]) -> dict:
    """
    Generate a grounded answer from retrieved document chunks.

    Returns a dict with:
    - "answer"  : the LLM response (grounded in retrieved context only)
    - "sources" : deduplicated source labels, appended programmatically by the caller
    """
    if not retrieved_chunks:
        return {"answer": NO_CHUNKS_MESSAGE, "sources": []}

    chunks = _filter_chunks(retrieved_chunks)
    if chunks[0]["distance"] > MAX_DISTANCE and len(chunks) == 1:
        return {"answer": WEAK_MATCH_MESSAGE, "sources": []}

    sources = list(dict.fromkeys(_format_source(c) for c in chunks))
    context = _build_context(chunks)

    if not GROQ_API_KEY:
        return {
            "answer": "GROQ_API_KEY is not set. Copy .env.example to .env and add your key.",
            "sources": sources,
        }

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"RETRIEVED REVIEWS:\n{context}\n\n"
                    f"QUESTION: {query}\n\n"
                    "Answer using only the reviews above."
                ),
            },
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer, "sources": sources}


def ask(query: str) -> dict:
    """End-to-end: retrieve relevant chunks, then generate a grounded answer."""
    from retriever import retrieve

    chunks = retrieve(query)
    return generate_response(query, chunks)


def format_response(result: dict) -> str:
    """Combine answer with programmatically guaranteed source attribution."""
    answer = result["answer"]
    if not result["sources"]:
        return answer
    source_lines = "\n".join(f"- {s}" for s in result["sources"])
    return f"{answer}\n\n---\n**Retrieved from:**\n{source_lines}"


if __name__ == "__main__":
    TEST_QUERIES = [
        "Does Paul Fodor record his lectures for CSE 114?",
        "What do students say about I.V. Ramakrishnan's CSE 596 class?",
        "What's the best dining hall at Stony Brook?",
    ]

    for q in TEST_QUERIES:
        print("\n" + "=" * 80)
        print(f"Q: {q}")
        print("=" * 80)
        print(format_response(ask(q)))
