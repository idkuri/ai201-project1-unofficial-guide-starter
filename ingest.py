import glob
import html
import os
import random
import re

import pdfplumber

from config import DOCS_PATH, RAW_PATH, RAW_TEXT_PATH

# Lines to drop during cleaning (navigation, ads, footers).
NOISE_LINE_PATTERNS = [
    r"^Help Site Guidelines",
    r"Rate My Professors, LLC",
    r"Do Not Sell My Personal Information",
    r"Copyright Compliance Policy",
    r"CA Notice at Collection",
    r"Terms & Conditions",
    r"Privacy Policy",
    r"All Rights Reserved",
    r"^Rate$",
    r"^Compare$",
    r"^Log In",
    r"^Sign Up",
    r"^Help\t",
    r"^Help Professors",
    r"^Rate Compare$",
    r"^I'm Professor ",
    r"^Rating Distribution$",
    r"^Similar Professors$",
    r"^Awesome 5 ",
    r"^Great 4 ",
    r"^Good 3 ",
    r"^OK 2 ",
    r"^Awful 1 ",
    r"^Helpful \d+ \d+",
    r"^-- \d+ of \d+ --$",
    r"^/ 5$",
    r"^Would take again$",
    r"^Level of Difficulty$",
    r"^All$",
    r"^courses$",
    r"^\d+%$",
    r"^Professor name Your school",
    r"^Stony Brook University \(SUNY\)$",
    r"^Computer Science$",
    r"^Load More Ratings$",
    r"^Write a Review$",
    r"^Claim this professor$",
]

COURSE_DATE_RE = re.compile(
    r"^([A-Z]{0,5}\d{2,4})\s+"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+(?:st|nd|rd|th)?,?\s+\d{4})",
    re.IGNORECASE,
)

TAG_RE = re.compile(
    r"^[A-Z][A-Z0-9'?.! ]+$"
)

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
    return "\n\n".join(pages)


def professor_name_from_filename(filename: str) -> str:
    """Parse professor name from RMP PDF filename."""
    stem = filename.replace(".pdf", "")
    match = re.match(r"^(.+?) at Stony Brook University", stem)
    return match.group(1).strip() if match else stem


def slugify(name: str) -> str:
    """Convert professor name to a filename slug."""
    slug = name.lower().replace(".", "").replace(" ", "_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def _is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pattern in NOISE_LINE_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return True
    return False


def clean_rmp_raw_text(text: str) -> str:
    """Remove navigation, ads, footers, and other non-review noise."""
    text = html.unescape(text)
    lines = text.splitlines()
    cleaned = [line for line in lines if not _is_noise_line(line)]
    return "\n".join(cleaned)


def save_raw_text(slug: str, text: str) -> str:
    """Persist unmodified pdfplumber output before cleaning."""
    os.makedirs(RAW_TEXT_PATH, exist_ok=True)
    output_path = os.path.join(RAW_TEXT_PATH, f"{slug}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path


def parse_profile_header(text: str, professor_name: str) -> dict:
    """Extract overall rating, rating count, and department from profile header."""
    profile = {
        "name": professor_name,
        "department": "Unknown",
        "overall_rating": None,
        "rating_count": None,
    }

    count_match = re.search(
        r"Overall Quality Based on (\d+) ratings?",
        text,
        re.IGNORECASE,
    )
    if count_match:
        profile["rating_count"] = count_match.group(1)

    for pattern in (
        r"(\d+\.\d+)\s*Overall Quality",
        r"Overall Quality\s*(\d+\.\d+)",
        r"(\d+\.\d+)\s*\nOverall Quality",
    ):
        rating_match = re.search(pattern, text, re.IGNORECASE)
        if rating_match:
            profile["overall_rating"] = rating_match.group(1)
            break

    dept_match = re.search(
        r"Professor in the (.+?) department at",
        text,
        re.IGNORECASE,
    )
    if dept_match:
        profile["department"] = dept_match.group(1).strip()

    return profile


def _is_tag_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) < 4:
        return False
    if not TAG_RE.match(stripped):
        return False
    words = stripped.split()
    if len(words) < 1:
        return False
    return all(w.isupper() or w in {"?", ".", "!"} for w in words)


def _parse_review_block(block: str) -> dict | None:
    """
    Parse a single review block in pdfplumber layout:

    QUALITY -> course/date -> quality score -> metadata -> DIFFICULTY -> body (with
    difficulty score on its own line mid-body) -> tags
    """
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if len(lines) < 4:
        return None

    idx = 0
    if lines[idx].upper() == "QUALITY":
        idx += 1

    course_match = COURSE_DATE_RE.match(lines[idx]) if idx < len(lines) else None
    if not course_match:
        return None

    course = course_match.group(1)
    date = course_match.group(2)
    idx += 1

    quality = ""
    if idx < len(lines) and re.fullmatch(r"[\d.]+", lines[idx]):
        quality = lines[idx]
        idx += 1

    metadata_parts = []
    pre_difficulty_body = []
    while idx < len(lines) and lines[idx].upper() != "DIFFICULTY":
        line = lines[idx]
        if line.startswith("Reviewed:"):
            idx += 1
            continue
        if any(
            line.startswith(prefix)
            for prefix in ("For Credit:", "Textbook:", "Attendance:", "Grade:", "Online Class:")
        ) or "For Credit:" in line or "Would Take Again:" in line:
            metadata_parts.append(line)
        else:
            pre_difficulty_body.append(line)
        idx += 1

    if idx < len(lines) and lines[idx].upper() == "DIFFICULTY":
        idx += 1

    body_lines = list(pre_difficulty_body)
    difficulty = ""
    tags = []
    while idx < len(lines):
        line = lines[idx]
        if line.upper() == "QUALITY":
            break
        if line.upper() == "HELPFUL":
            idx += 1
            continue
        score_prefix = re.match(r"^(\d+\.\d+)\s+(.+)", line)
        if score_prefix and not difficulty:
            difficulty = score_prefix.group(1)
            body_lines.append(score_prefix.group(2))
            idx += 1
            continue
        if re.fullmatch(r"[\d.]+", line):
            if not difficulty:
                difficulty = line
            idx += 1
            continue
        if _is_tag_line(line):
            tags.append(line)
            idx += 1
            continue
        body_lines.append(line)
        idx += 1

    while body_lines and _is_tag_line(body_lines[-1]):
        tags.insert(0, body_lines.pop())

    body = " ".join(body_lines).strip()
    body = re.sub(r"\s*Helpful\s*(?:\d+\s*){1,2}", "", body)
    body = re.sub(r"\s+\d+\s+\d+\s*$", "", body)
    body = re.sub(
        r"\s*Reviewed:\s+\w+\s+\d+(?:st|nd|rd|th)?,?\s+\d{4}(?:\s+\d+\s+\d+)?",
        "",
        body,
    )
    if difficulty:
        body = re.sub(rf"\s*{re.escape(difficulty)}\s*", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    metadata = " | ".join(metadata_parts)

    if not course and not body:
        return None

    return {
        "course": course,
        "date": date,
        "quality": quality,
        "difficulty": difficulty,
        "metadata": metadata,
        "body": body,
        "tags": tags,
    }


def parse_reviews(text: str) -> list[dict]:
    """Split cleaned text into structured review dicts."""
    ratings_marker = re.search(r"\d+\s+Student Ratings", text, re.IGNORECASE)
    review_text = text[ratings_marker.end():] if ratings_marker else text

    blocks = re.split(r"(?=QUALITY\s*\n)", review_text, flags=re.IGNORECASE)
    reviews = []

    for block in blocks:
        block = block.strip()
        if not block.upper().startswith("QUALITY"):
            continue

        parsed = _parse_review_block(block)
        if parsed and (parsed["body"] or parsed["metadata"]):
            reviews.append(parsed)

    return reviews


def format_structured_document(profile: dict, reviews: list[dict]) -> str:
    """Render a chunk-ready structured text document."""
    lines = [
        f"# Professor: {profile['name']}",
        "# Source: Rate My Professors — Stony Brook University (SUNY)",
        f"# Department: {profile['department']}",
    ]

    if profile["overall_rating"] and profile["rating_count"]:
        lines.append(
            f"# Overall rating: {profile['overall_rating']}/5 ({profile['rating_count']} ratings)"
        )
    lines.append("")

    for review in reviews:
        lines.append("=" * 80)
        lines.append("REVIEW")
        lines.append(f"Course: {review['course']}")
        lines.append(f"Date: {review['date']}")
        lines.append(
            f"Quality: {review['quality']} | Difficulty: {review['difficulty']}"
        )
        if review["metadata"]:
            lines.append(review["metadata"])
        if review["tags"]:
            tag_text = ", ".join(review["tags"])
            lines.append(f"Tags: {tag_text}")
        lines.append("")
        if review["body"]:
            lines.append(review["body"])
        lines.append("=" * 80)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def preprocess_pdfs() -> list[str]:
    """
    Extract, clean, and structure all RMP PDFs from raw/ into documents/*.txt.

    Pipeline per PDF: extract -> save raw_text/{slug}.txt -> clean -> documents/{slug}.txt

    Returns a list of output file paths written.
    """
    os.makedirs(DOCS_PATH, exist_ok=True)
    os.makedirs(RAW_TEXT_PATH, exist_ok=True)
    pdf_pattern = os.path.join(RAW_PATH, "*Rate My Professors*.pdf")
    pdf_files = sorted(glob.glob(pdf_pattern))

    if not pdf_files:
        print(f"No RMP PDFs found in {RAW_PATH}/")
        return []

    written = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        professor_name = professor_name_from_filename(filename)
        slug = slugify(professor_name)
        output_path = os.path.join(DOCS_PATH, f"{slug}.txt")

        raw_text = extract_pdf_text(pdf_path)
        save_raw_text(slug, raw_text)
        cleaned_text = clean_rmp_raw_text(raw_text)
        profile = parse_profile_header(cleaned_text, professor_name)
        reviews = parse_reviews(cleaned_text)
        structured = format_structured_document(profile, reviews)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(structured)

        written.append(output_path)
        print(
            f"  {filename} -> raw_text/{slug}.txt -> documents/{slug}.txt "
            f"({len(reviews)} reviews)"
        )

    print(f"\nProcessed {len(written)} PDF(s) into {RAW_TEXT_PATH}/ and {DOCS_PATH}/")
    return written


def load_documents():
    """Load all .txt documents from the documents folder."""
    documents = []
    if not os.path.isdir(DOCS_PATH):
        print(f"No documents folder found at {DOCS_PATH}/")
        return documents

    for filename in sorted(os.listdir(DOCS_PATH)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_PATH, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            source_name = filename.replace(".txt", "").replace("_", " ")
            documents.append({
                "source": source_name,
                "filename": filename,
                "text": text,
            })
    print(f"Loaded {len(documents)} document(s): {[d['source'] for d in documents]}")
    return documents


REVIEW_DELIMITER = "=" * 80


def chunk_document(text, source_name):
    """
    Split a document into one chunk per review block (semantic chunking).

    Returns a list of dicts, each with:
    - "text"     : the chunk text (str)
    - "source"   : the source name, e.g. "paul_fodor" (str)
    - "chunk_id"    : a unique identifier, e.g. "paul_fodor_review_0" (str)
    - "chunk_index" : 0-based position of this review in the source document (int)
    - "course"      : course code from the review, if present (str)
    - "date"        : review date, if present (str)
    """
    slug = source_name.replace(" ", "_")
    chunks = []

    for block in re.split(r"={80}\n?", text):
        block = block.strip()
        if not block.startswith("REVIEW"):
            continue

        course_match = re.search(r"^Course:\s*(.+)$", block, re.MULTILINE)
        date_match = re.search(r"^Date:\s*(.+)$", block, re.MULTILINE)
        course = course_match.group(1).strip() if course_match else None

        header = f"Professor: {source_name}"
        if course:
            header += f" | Course: {course}"
        chunk_text = (
            f"{REVIEW_DELIMITER}\n"
            f"{header}\n"
            f"{block}\n"
            f"{REVIEW_DELIMITER}"
        )

        chunk_index = len(chunks)
        chunk = {
            "text": chunk_text,
            "source": slug,
            "chunk_id": f"{slug}_review_{chunk_index}",
            "chunk_index": chunk_index,
        }
        if course:
            chunk["course"] = course
        if date_match:
            chunk["date"] = date_match.group(1).strip()
        if len(chunk_text.strip()) > 0:
            chunks.append(chunk)

    return chunks


_METADATA_PREFIXES = (
    "Professor:",
    "Course:",
    "Date:",
    "Quality:",
    "For Credit:",
    "Tags:",
    "Difficulty:",
    "Attendance:",
    "Would Take Again:",
    "Textbook:",
    "Grade:",
    "Online Class:",
    "Reviewed:",
)


def extract_review_body(text: str) -> str:
    """Return the student-written review text, without RMP headers or metadata."""
    body = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "REVIEW" or stripped.startswith("="):
            continue
        if stripped.startswith(_METADATA_PREFIXES):
            continue
        body.append(stripped)
    return " ".join(body)


def build_embedding_text(chunk: dict) -> str:
    """
    Build compact text for vector embedding.

    Full chunk text (with headers and tags) is kept in Chroma for display and
    generation. Embedding the entire formatted chunk dilutes short factual
    statements — e.g. "he records his lectures" — behind headers and unrelated
    review text. For recording mentions, embed the specific sentence instead.
    """
    body = extract_review_body(chunk["text"])
    parts = [chunk.get("source", "").replace("_", " ")]
    if chunk.get("course"):
        parts.append(chunk["course"])
    if chunk.get("date"):
        parts.append(chunk["date"])

    tags_match = re.search(r"^Tags:\s*(.+)$", chunk["text"], re.MULTILINE)
    if tags_match:
        parts.append(tags_match.group(1))

    record_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", body)
        if sentence.strip() and re.search(r"\brecord(?:s|ed|ing)?\b", sentence, re.I)
    ]
    if record_sentences:
        parts.extend(record_sentences)
    elif body:
        parts.append(body[:300])
    return " ".join(parts)


REPRESENTATIVE_CHUNK_CRITERIA = [
    {"source": "paul_fodor", "course": "CSE114", "text_contains": "records his lectures"},
    {"source": "christopher_kane", "course": "CSE307"},
    {"source": "iv_ramakrishnan", "course": "CSE596"},
    {"source": "ali_raza", "course": "ISE218"},
    {"source": "scott_stoller", "course": "CSE308"},
]


def _find_representative_chunk(chunks: list[dict], criteria: dict) -> dict | None:
    """Pick the first chunk matching source/course and optional text substring."""
    for chunk in chunks:
        if chunk.get("source") != criteria["source"]:
            continue
        if chunk.get("course", "").upper() != criteria["course"].upper():
            continue
        text_contains = criteria.get("text_contains")
        if text_contains and text_contains.lower() not in chunk["text"].lower():
            continue
        return chunk
    return None


def print_sample_document(documents: list[dict], filename: str = "scott_stoller.txt") -> None:
    """Print one full cleaned document for manual inspection."""
    doc = next((d for d in documents if d["filename"] == filename), documents[0])
    print("\n" + "=" * 80)
    print(f"SAMPLE CLEANED DOCUMENT: {doc['filename']}")
    print("=" * 80)
    print(doc["text"])
    print("=" * 80)


def print_representative_chunks(chunks: list[dict], n: int = 5) -> None:
    """Print n representative chunks spread across professors and courses."""
    print("\n" + "=" * 80)
    print(f"REPRESENTATIVE CHUNKS ({n})")
    print("=" * 80)

    selected = []
    for criteria in REPRESENTATIVE_CHUNK_CRITERIA:
        if len(selected) >= n:
            break
        match = _find_representative_chunk(chunks, criteria)
        if match and match not in selected:
            selected.append(match)

    if len(selected) < n:
        for chunk in chunks:
            if chunk not in selected:
                selected.append(chunk)
            if len(selected) >= n:
                break

    for i, chunk in enumerate(selected[:n], start=1):
        course = chunk.get("course", "unknown")
        print(f"\n--- Chunk {i} | source: {chunk['source']} | course: {course} ---")
        print(chunk["text"])


def diagnose_chunks(chunks: list[dict]) -> dict:
    """Run quality checks before embedding."""
    lengths = [len(c["text"]) for c in chunks]
    html_markers = ("<div", "&amp;", "&nbsp;", "<html")
    return {
        "total": len(chunks),
        "empty": sum(1 for c in chunks if not c["text"].strip()),
        "html_artifacts": sum(
            1 for c in chunks if any(m in c["text"] for m in html_markers)
        ),
        "min_len": min(lengths) if lengths else 0,
        "max_len": max(lengths) if lengths else 0,
        "median_len": sorted(lengths)[len(lengths) // 2] if lengths else 0,
        "unique_lengths": len(set(lengths)),
        "sources": sorted({c["source"] for c in chunks}),
    }


def print_random_chunks(chunks: list[dict], n: int = 5, seed: int = 42) -> None:
    """Print n random chunks for manual quality inspection."""
    rng = random.Random(seed)
    print("\n" + "=" * 80)
    print(f"RANDOM CHUNKS ({n})")
    print("=" * 80)

    if len(chunks) < n:
        selected = chunks
    else:
        selected = rng.sample(chunks, n)

    for i, chunk in enumerate(selected, start=1):
        course = chunk.get("course", "unknown")
        print(
            f"\n--- Random {i} | source: {chunk['source']} | "
            f"chunk_id: {chunk['chunk_id']} | course: {course} | "
            f"len: {len(chunk['text'])} ---"
        )
        print(chunk["text"])


def print_chunk_diagnostics(chunks: list[dict]) -> None:
    """Print pre-embedding chunk quality summary."""
    stats = diagnose_chunks(chunks)
    print("\n" + "=" * 80)
    print("CHUNK DIAGNOSTICS")
    print("=" * 80)
    print(f"  Total chunks:      {stats['total']}")
    print(f"  Empty chunks:      {stats['empty']}")
    print(f"  HTML artifacts:    {stats['html_artifacts']}")
    print(
        f"  Length range:      {stats['min_len']}–{stats['max_len']} "
        f"(median {stats['median_len']})"
    )
    print(f"  Unique lengths:    {stats['unique_lengths']}")
    print(f"  Sources:           {', '.join(stats['sources'])}")

    issues = []
    if stats["empty"]:
        issues.append("empty chunks detected")
    if stats["html_artifacts"]:
        issues.append("HTML artifacts detected")
    if stats["unique_lengths"] <= 3 and stats["total"] > 10:
        issues.append("chunks may be fixed-size (too few unique lengths)")

    if issues:
        print(f"\n  WARNING: {', '.join(issues)} — fix before embedding.")
    else:
        print("\n  Quality check: PASS — chunks look ready for embedding.")


def print_chunk_summary(per_doc_counts: dict[str, int], total: int) -> None:
    """Print per-document and total chunk counts with sanity check."""
    print("\n" + "=" * 80)
    print("CHUNK SUMMARY")
    print("=" * 80)
    for filename in sorted(per_doc_counts):
        slug = filename.replace(".txt", "")
        print(f"  {slug}: {per_doc_counts[filename]}")
    print(f"\nTotal chunks: {total}")
    if 50 <= total <= 2000:
        print(f"Sanity check: PASS (50 <= {total} <= 2000)")
    else:
        print(f"Sanity check: FAIL (50 <= {total} <= 2000)")


if __name__ == "__main__":
    print("Preprocessing RMP PDFs from raw/ ...\n")
    preprocess_pdfs()

    print("\nLoading documents and chunking ...\n")
    documents = load_documents()
    all_chunks = []
    per_doc_counts = {}
    for doc in documents:
        chunks = chunk_document(doc["text"], doc["source"])
        per_doc_counts[doc["filename"]] = len(chunks)
        all_chunks.extend(chunks)

    print_sample_document(documents)
    print_chunk_diagnostics(all_chunks)
    print_random_chunks(all_chunks)
    print_representative_chunks(all_chunks)
    print_chunk_summary(per_doc_counts, total=len(all_chunks))
