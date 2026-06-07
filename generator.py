import re

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

_FOLLOW_UP_PRONOUNS = re.compile(
    r"\b(he|she|they|him|her|them|his|hers|their|"
    r"that professor|this professor|same professor|"
    r"that class|this class|same class)\b",
    re.I,
)

_PROFESSOR_NAMES = (
    "i.v. ramakrishnan",
    "christopher kane",
    "dimitris samaras",
    "himanshu gupta",
    "michael ferdman",
    "scott stoller",
    "eugene stark",
    "amir rahmati",
    "paul fodor",
    "ali raza",
    "iv ramakrishnan",
)

_PROFESSOR_DISPLAY = {
    "i.v. ramakrishnan": "I.V. Ramakrishnan",
    "iv ramakrishnan": "I.V. Ramakrishnan",
}


def _content_to_text(content) -> str:
    """Extract plain text from Gradio message content (str, dict, or list)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            text for item in content if (text := _content_to_text(item))
        )
    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        if "text" in content:
            return str(content["text"])
    return ""


def _history_to_text(history) -> str:
    """Flatten Gradio chat history (tuple or message dict format) to plain text."""
    if not history:
        return ""

    parts = []
    for turn in history:
        if isinstance(turn, dict):
            content = _content_to_text(turn.get("content", ""))
            if content:
                parts.append(content)
        elif isinstance(turn, (list, tuple)):
            user_msg = _content_to_text(turn[0] if len(turn) > 0 else "")
            assistant_msg = _content_to_text(turn[1] if len(turn) > 1 else "")
            if user_msg:
                parts.append(f"User: {user_msg}")
            if assistant_msg:
                parts.append(f"Assistant: {assistant_msg}")
    return "\n".join(parts)


def _user_history_text(history) -> str:
    """Text from user turns only — assistant answers often list many course codes."""
    if not history:
        return ""

    parts = []
    for turn in history:
        if isinstance(turn, dict):
            if turn.get("role") == "user":
                content = _content_to_text(turn.get("content", ""))
                if content:
                    parts.append(content)
        elif isinstance(turn, (list, tuple)):
            user_msg = _content_to_text(turn[0] if len(turn) > 0 else "")
            if user_msg:
                parts.append(user_msg)
    return "\n".join(parts)


def _find_most_recent_professor(text: str) -> str | None:
    normalized = text.lower().replace("i.v.", "iv").replace("i. v.", "iv")
    best_idx = -1
    best_name = None
    for name in _PROFESSOR_NAMES:
        idx = normalized.rfind(name)
        if idx > best_idx:
            best_idx = idx
            best_name = name
    if not best_name:
        return None
    return _PROFESSOR_DISPLAY.get(best_name, best_name.title())


def _find_most_recent_course(text: str) -> str | None:
    matches = list(re.finditer(r"\b((?:CSE|ISE|CS)\s*\d{2,4})\b", text, re.I))
    if not matches:
        return None
    return matches[-1].group(1).upper().replace(" ", "")


def _is_follow_up(query: str, has_professor: bool, has_course: bool) -> bool:
    if _FOLLOW_UP_PRONOUNS.search(query):
        return True
    if not has_professor or not has_course:
        return True
    return False


def resolve_query_for_retrieval(query: str, history=None) -> str:
    """
    Expand follow-up questions with professor/course context from prior turns
    so retrieval and metadata filters can resolve pronouns like "he" or "that class".
    """
    if not history:
        return query

    from retriever import _detect_course_code, _detect_professor_slug

    has_professor = _detect_professor_slug(query) is not None
    has_course = _detect_course_code(query) is not None
    if has_professor and has_course:
        return query

    if not _is_follow_up(query, has_professor, has_course):
        return query

    history_text = _history_to_text(history)
    professor = None if has_professor else _find_most_recent_professor(history_text)
    # Only inherit a course the user actually asked about — not codes listed in
    # the assistant's summary (which would wrongly narrow retrieval).
    course = None if has_course else _find_most_recent_course(_user_history_text(history))

    expanded = query
    if professor:
        expanded = f"{professor}: {expanded}"
    if course:
        expanded = f"{expanded} (course {course})"
    return expanded


def _format_conversation(history, max_turns: int = 3) -> str:
    """Format recent chat turns for the LLM prompt."""
    if not history:
        return ""

    lines = []
    for turn in history[-max_turns:]:
        if isinstance(turn, dict):
            role = turn.get("role", "user").capitalize()
            content = _content_to_text(turn.get("content", ""))
            if content:
                lines.append(f"{role}: {content}")
        elif isinstance(turn, (list, tuple)):
            user_msg = _content_to_text(turn[0] if len(turn) > 0 else "")
            assistant_msg = _content_to_text(turn[1] if len(turn) > 1 else "")
            if user_msg:
                lines.append(f"User: {user_msg}")
            if assistant_msg:
                # Strip citation blocks from prior answers to save tokens.
                answer = assistant_msg.split("\n---\n")[0].strip()
                lines.append(f"Assistant: {answer}")
    return "\n".join(lines)


def _format_source(chunk: dict) -> str:
    """Build a human-readable source label from chunk metadata."""
    source = chunk["source"].replace("_", " ").title()
    course = chunk.get("course")
    if course:
        return f"{source} ({course})"
    return source


def _format_citation(chunk: dict, index: int) -> str:
    """Format a retrieved chunk as a numbered review citation."""
    header = f"Review {index} — {_format_source(chunk)}"
    if chunk.get("date"):
        header += f" — {chunk['date']}"
    return f"{header}\n{chunk['text']}"


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        label = _format_source(chunk)
        parts.append(f"[Review {i} — {label}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _filter_chunks(chunks: list[dict]) -> list[dict]:
    """Keep chunks close to the best match; allow farther hits when several are relevant."""
    if not chunks:
        return []
    best = min(chunk["distance"] for chunk in chunks)
    threshold = max(MAX_DISTANCE, best + 0.35)
    strong = [chunk for chunk in chunks if chunk["distance"] <= threshold]
    return strong if strong else chunks[:1]


def generate_response(
    query: str, retrieved_chunks: list[dict], history=None
) -> dict:
    """
    Generate a grounded answer from retrieved document chunks.

    Returns a dict with:
    - "answer"     : the LLM response (grounded in retrieved context only)
    - "citations"  : numbered review excerpts passed to the LLM, for display
    """
    if not retrieved_chunks:
        return {"answer": NO_CHUNKS_MESSAGE, "citations": []}

    chunks = _filter_chunks(retrieved_chunks)
    if chunks[0]["distance"] > MAX_DISTANCE and len(chunks) == 1:
        return {"answer": WEAK_MATCH_MESSAGE, "citations": []}

    citations = [_format_citation(chunk, i) for i, chunk in enumerate(chunks, start=1)]
    context = _build_context(chunks)

    if not GROQ_API_KEY:
        return {
            "answer": "GROQ_API_KEY is not set. Copy .env.example to .env and add your key.",
            "citations": citations,
        }

    conversation = _format_conversation(history)
    user_parts = []
    if conversation:
        user_parts.append(
            "CONVERSATION (use only to resolve follow-up references like "
            "'he', 'that class', or 'same professor'):\n"
            f"{conversation}\n"
        )
    user_parts.append(f"RETRIEVED REVIEWS:\n{context}\n")
    user_parts.append(
        f"QUESTION: {query}\n\n"
        "Answer using only the reviews above. Resolve pronouns from the "
        "conversation when the question refers to a prior professor or course."
    )

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer, "citations": citations}


def ask(query: str, retrieval_mode: str | None = None, history=None) -> dict:
    """End-to-end: retrieve relevant chunks, then generate a grounded answer."""
    from retriever import retrieve

    retrieval_query = resolve_query_for_retrieval(query, history)
    chunks = retrieve(retrieval_query, mode=retrieval_mode)
    return generate_response(query, chunks, history=history)


def format_response(result: dict) -> str:
    """Combine answer with programmatically guaranteed source attribution."""
    answer = result["answer"]
    if not result.get("citations"):
        return answer
    citation_block = "\n\n".join(result["citations"])
    return f"{answer}\n\n---\n**Retrieved from:**\n\n{citation_block}"


def format_context_log_entry(turn_num: int, message: str, history=None) -> str:
    """Build a markdown block showing what context the model used for one chat turn."""
    retrieval_query = resolve_query_for_retrieval(message, history)
    conversation = _format_conversation(history)

    lines = [f"### Turn {turn_num}", f"**You asked:** {message}"]
    if conversation:
        lines.append(
            "**Prior turns sent to the LLM** _(last 3, citations stripped)_:\n"
            f"```\n{conversation}\n```"
        )
    else:
        lines.append("**Prior turns sent to the LLM:** _(none — first message)_")

    if retrieval_query != message:
        lines.append(
            "**Retrieval query** _(expanded to resolve follow-up pronouns)_:\n"
            f"`{retrieval_query}`"
        )
    else:
        lines.append(f"**Retrieval query:** `{retrieval_query}`")
    return "\n\n".join(lines)


if __name__ == "__main__":
    follow_up_history = [
        (
            "What do students say about Paul Fodor for CSE 114?",
            "Students describe Paul Fodor as helpful with clear lectures for CSE 114.",
        )
    ]
    follow_up = "Does he record his lectures?"
    expanded = resolve_query_for_retrieval(follow_up, follow_up_history)
    print("Follow-up expansion demo")
    print(f"  Original:  {follow_up!r}")
    print(f"  Retrieval: {expanded!r}")

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
