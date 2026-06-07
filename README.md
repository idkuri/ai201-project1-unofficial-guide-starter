# The Unofficial Guide - Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text. If a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This guide is about **CS professor reviews at Stony Brook**. SOLAR tells you who's teaching this semester, but it won't tell you who students actually recommend, whether a professor is an easy grader vs someone who helps you learn, or which courses they tend to teach. A high RMP rating alone doesn't tell the full story either. Students care about different things: tough grading, lecture quality, workload, group projects, office hours, and whether they'd take the class again.

That info is spread across Rate My Professors. You have to open each professor's page, scroll through reviews, and match comments to specific courses like CSE 114 or CSE 316. It's useful for picking classes and planning ahead, but annoying to dig through manually. This project collects those reviews in one place so you can ask questions instead of clicking through ten different profiles.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Scott Stoller | Rate My Professors (PDF) | `raw/Scott Stoller at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 2 | Christopher Kane | Rate My Professors (PDF) | `raw/Christopher Kane at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 3 | Ali Raza | Rate My Professors (PDF) | `raw/Ali Raza at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 4 | Amir Rahmati | Rate My Professors (PDF) | `raw/Amir Rahmati at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 5 | Dimitris Samaras | Rate My Professors (PDF) | `raw/Dimitris Samaras at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 6 | Eugene Stark | Rate My Professors (PDF) | `raw/Eugene Stark at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 7 | Himanshu Gupta | Rate My Professors (PDF) | `raw/Himanshu Gupta at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 8 | I.V. Ramakrishnan | Rate My Professors (PDF) | `raw/I.V. Ramakrishnan at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 9 | Michael Ferdman | Rate My Professors (PDF) | `raw/Michael Ferdman at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 10 | Paul Fodor | Rate My Professors (PDF) | `raw/Paul Fodor at Stony Brook University (SUNY) _ Rate My Professors.pdf` |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Preprocessing:** Rate My Professors blocks scraping, so I manually hit Load More Ratings on each professor page and saved the full page as a PDF in `raw/`. Run `python ingest.py` to turn those into `.txt` files in `documents/`. pdfplumber pulls the text, strips nav/footer junk, and parses each review into a block with course, scores, tags, and the comment.

**Method:** Review-boundary semantic chunking (one chunk per review)

**Chunk size:** One review block (variable length, usually 100–800 characters)

**Overlap:** 0. Each review is already a complete unit with course, scores, tags, and comment. No need to duplicate text across chunks.

**Why these choices fit your documents:** Fixed-size chunking can split a long review in half or mix two reviews in one chunk. Splitting at review boundaries keeps course, scores, tags, and comment together so retrieval always returns a complete opinion.

**Final chunk count:** 563 chunks across 10 professor documents (one review per chunk). Breakdown: ali_raza 11, amir_rahmati 22, christopher_kane 30, dimitris_samaras 8, eugene_stark 86, himanshu_gupta 36, iv_ramakrishnan 15, michael_ferdman 33, paul_fodor 312, scott_stoller 10.

---

## Sample Chunks

<!-- Paste 5 representative chunks from your document collection after running your ingestion pipeline.
     For each chunk, note which source document it came from.
     These must be actual text, not screenshots. -->

| # | Source document | Chunk text |
|---|----------------|------------|
| 1 | `paul_fodor.txt` | REVIEW / Course: 114 / Date: Apr 15th, 2026 / Quality: 5.0, Difficulty: 3.0 / Tags: AMAZING LECTURES INSPIRATIONAL RESPECTED / "Goated prof for 114" |
| 2 | `christopher_kane.txt` | REVIEW / Course: CSE307 / Date: Mar 2nd, 2026 / Quality: 5.0, Difficulty: 5.0 / Tags: TOUGH GRADER LECTURE HEAVY ACCESSIBLE OUTSIDE CLASS / "Yes. He is the goat. His lectures can be a little long-winded but he is passionate about the subject." |
| 3 | `scott_stoller.txt` | REVIEW / Course: CSE308 / Date: Dec 21st, 2025 / Quality: 4.0, Difficulty: 3.0 / Tags: GROUP PROJECTS ACCESSIBLE OUTSIDE CLASS / "For CSE 416: Good professor, project was appropriate in difficulty... Professor was very responsive to questions about the project." |
| 4 | `iv_ramakrishnan.txt` | REVIEW / Course: CSE596 / Date: Jan 14th, 2026 / Quality: 1.0, Difficulty: 5.0 / Tags: TOUGH GRADER / "He is the most direspectful and toxic professor on the stony brook campus who tortures students and berates them for pleasure." |
| 5 | `ali_raza.txt` | REVIEW / Course: ISE218 / Date: Nov 11th, 2024 / Quality: 5.0, Difficulty: 4.0 / Tags: EXTRA CREDIT CARING RESPECTED / "He always asks the class if everyone understands before moving on. Tough exams, but very clear expectations." |

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers (`SentenceTransformer("all-MiniLM-L6-v2")`). Loaded once in `retriever.py` and used to embed all 563 review chunks before storing vectors in ChromaDB. I chose this model because it runs locally with no API key or rate limits, is fast on CPU, and works well for short semantic text like student reviews.

**Production tradeoff reflection:** If cost were not a constraint, I would weigh a larger embedding model (e.g. OpenAI `text-embedding-3-large` or a domain-tuned model) for better accuracy on professor/course name matching and nuanced opinion text. Tradeoffs include API latency vs local inference, context length limits (reviews are short, so this matters less here), and multilingual support (not needed for this English-only corpus). A hosted model might improve recall on specific facts like "records lectures" but adds dependency on external uptime and billing.

---

## Retrieval Test Results

Run `python retriever.py` to reproduce. Results below are from the **final pipeline** (compact embedding text, professor/course metadata filters, top-k = 5).

**Query 1:** Does Paul Fodor record his lectures for CSE 114?

Top returned chunks:
- [1] `paul_fodor` | CSE114 | distance: 0.246 — Dec 18th, 2025 — "he records his lectures"
- [2] `paul_fodor` | CSE114 | distance: 0.271 — Dec 30th, 2022 — "Also records lectures"
- [3] `paul_fodor` | 114 | distance: 0.281 — Apr 15th, 2026
- [4] `paul_fodor` | CSE114 | distance: 0.282 — Apr 15th, 2015
- [5] `paul_fodor` | CSE114 | distance: 0.291 — May 17th, 2022

Relevance explanation: After embedding only the record-related sentence (not the full formatted chunk), the Dec 2025 and Dec 2022 reviews that explicitly mention lecture recording rank first. Course metadata filtering (`CSE114` / `114` variants) keeps results scoped to the right class.

---

**Query 2:** What Rate My Professor tags do students assign to Christopher Kane for CSE 307?

Top returned chunks:
- [1] `christopher_kane` | CSE307 | distance: 0.443 — Mar 2nd, 2026 — Tags: TOUGH GRADER LECTURE HEAVY ACCESSIBLE OUTSIDE CLASS
- [2] `christopher_kane` | CSE307 | distance: 0.518 — May 16th, 2020

Relevance explanation: Professor + course metadata filtering restricts search to Kane's CSE307 reviews only. RMP tags are included in the embedding text so tag vocabulary matches the query. Both returned chunks are directly on-target.

---

**Query 3:** What do students say about I.V. Ramakrishnan's CSE 596 class?

Top returned chunks:
- [1] `iv_ramakrishnan` | CSE596 | distance: 0.279 — Jul 17th, 2015 — Quality 1.0, not helpful, bad attitude
- [2] `iv_ramakrishnan` | CSE596 | distance: 0.404 — Jan 14th, 2026 — Tags: TOUGH GRADER, "NEVER TAKE HIS COURSE"
- [3] `iv_ramakrishnan` | CSE596 | distance: 0.518 — Jan 14th, 2026 — Quality 1.0, accused of copying work

Relevance explanation: Filtering to `iv_ramakrishnan` + `CSE596` prevents CSE537 reviews from flooding the context (an earlier failure). All three chunks are negative CSE596 reviews with the ratings and language the query asks about.

---

## Grounded Generation

**System prompt grounding instruction:**

The LLM receives a strict system prompt (`generator.py`) with six rules: use only retrieved review text, do not guess, decline with an exact sentence when context is insufficient, do not invent citations (the UI adds those separately), quote specific details when answering, and never fabricate review content.

Key decline sentence enforced by the prompt:
> I don't have enough information in the loaded documents to answer that.

**Structural choices beyond the prompt:**

1. **Chunk filtering before generation** — `_filter_chunks()` drops retrieved results whose cosine distance exceeds `max(0.55, best_distance + 0.35)`, so weak matches are not sent to the LLM unless several chunks are jointly relevant (e.g., multiple Scott Stoller courses).
2. **Single weak-chunk guard** — If only one chunk is retrieved and its distance exceeds 0.55, the system returns a refusal without calling the LLM.
3. **Numbered context block** — Retrieved chunks are formatted as `[Review N — Professor (Course)]` plus full chunk text so the model can reference specific reviews.
4. **Low temperature** — `temperature=0.1` reduces paraphrase drift.
5. **Programmatic citations** — The LLM is instructed not to list sources; the Gradio UI displays the exact chunk text in **Retrieved from**, separate from the generated answer.

**How source attribution is surfaced in the response:**

The answer appears in the left panel. The right **Retrieved from** panel lists numbered review citations (`Review 1 — Paul Fodor (CSE114) — Dec 18th, 2025`) followed by the full chunk text passed to the LLM. Citations are built in code, not generated by the model.

---

## Example Responses

**Grounded response 1**

Query: Does Paul Fodor record his lectures for CSE 114?

Response: Yes, according to the reviews, Paul Fodor records his lectures for CSE 114, as stated in Review 1: "he records his lectures" and also mentioned in Review 2: "Also records lectures."

Source attribution: Review 1 — Paul Fodor (CSE114) — Dec 18th, 2025 (full chunk shown in UI); Review 2 — Paul Fodor (CSE114) — Dec 30th, 2022.

---

**Grounded response 2**

Query: How does Ali Raza prepare students for exams in ISE 218?

Response: According to the reviews, Ali Raza prepares students for exams in ISE 218 by giving "topics of questions prior" to the exams (Review 1) and by providing "the questions beforehand" for quizzes and tests (Review 5).

Source attribution: Review 1 — Ali Raza (ISE218) — Nov 11th, 2024; additional ISE218 reviews in the Retrieved from panel.

---

**Out-of-scope query**

Query: What's the best dining hall at Stony Brook?

System response (refusal): I don't have enough information in the loaded documents to answer that. The retrieved reviews did not closely match your question.

---

## Query Interface

**Input fields:** A single **Your question** text box with example queries below it, plus an **Ask** button (Enter also submits).

**Output format:** Two side-by-side read-only panels — **Answer** (LLM response) and **Retrieved from** (numbered review chunks with full citation text). Sources are never generated by the LLM; they are appended programmatically.

---

**Sample Interaction Transcript**

> **User:** Does Paul Fodor record his lectures for CSE 114?

> **System (Answer):** Yes, according to the reviews, Paul Fodor records his lectures for CSE 114, as stated in Review 1: "he records his lectures" and also mentioned in Review 2: "Also records lectures."

> **System (Retrieved from):**
> Review 1 — Paul Fodor (CSE114) — Dec 18th, 2025
> [full review chunk with Quality/Tags/body text]
>
> Review 2 — Paul Fodor (CSE114) — Dec 30th, 2022
> [full review chunk …]

---

## Demo Video

**Link:** *(add your recorded demo URL before submitting)*

The demo shows:
1. A grounded question with answer and review citations in **Retrieved from**
2. An out-of-scope question that the system declines
3. Navigation of the Gradio UI without external explanation

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Does Paul Fodor record his lectures for CSE 114? | Yes — multiple reviews say he records lectures (Dec 2025, Nov 2024) | Yes; quotes "he records his lectures" and "Also records lectures" from top CSE114 reviews | Relevant | Accurate |
| 2 | What RMP tags for Christopher Kane in CSE 307? | TOUGH GRADER, LECTURE HEAVY, ACCESSIBLE OUTSIDE CLASS; Mar 2026 review Quality 5.0 / Difficulty 5.0 | Lists TOUGH GRADER, LECTURE HEAVY, ACCESSIBLE, OUTSIDE CLASS, plus RESPECTED and CARING from a second CSE307 review | Relevant | Partially accurate |
| 3 | What courses does Scott Stoller teach? | CSE308, CSE535, CSE302 + coursework themes | Lists all three course codes correctly; does not summarize distributed-systems/project themes | Relevant | Partially accurate |
| 4 | What do students say about I.V. Ramakrishnan's CSE 596? | Overwhelmingly negative; TOUGH GRADER; "NEVER TAKE HIS COURSE" | Negative sentiment, Quality 1.0, Difficulty 5.0, toxic/disrespectful language, "NEVER TAKE HIS COURSE" | Relevant | Accurate |
| 5 | How does Ali Raza prepare students for ISE 218 exams? | Gives topics/questions prior to exams; tough but clear | Gives "topics of questions prior" and questions beforehand for quizzes/tests | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

### Failure 1 (fixed): Paul Fodor lecture recording — retrieval / embedding stage

**Question that failed:** Does Paul Fodor record his lectures for CSE 114?

**Expected answer:** Yes — multiple reviews say he records lectures (e.g. "he records his lectures" in Dec 2025 and Nov 2024 CSE114 reviews).

**What the system returned (before fix):** "I don't have enough information in the loaded documents to answer that." The reviews were in the corpus. Retrieval even showed Paul Fodor (CSE114) as a source — but the wrong reviews, ones that never mention recording.

**What I noticed:** The test case wasn't wrong. The data was right. The system was pulling generic CSE114 reviews ("helpful professor, clear lectures") instead of the ones that literally say "he records his lectures."

**What I told the AI:** This isn't a k problem — don't just grab more chunks. Something is off with how relevance is mapped. It's not really about `record` vs `recording` as synonyms. The embedding just wasn't surfacing the right review.

**Root cause (pipeline stage):** **Embedding.** We were vectorizing the whole formatted chunk — delimiters, headers, tags, metadata, full comment. That drowned out short facts like "he records his lectures." With 312 Fodor reviews, boring generic CSE114 reviews ranked above the recording reviews at k = 5.

**Fix (kept k = 5):** `build_embedding_text()` in `ingest.py` now embeds a shorter string: professor, course, date, tags, and for recording reviews only the sentence that mentions record/records/recorded. Full chunk text still goes to Chroma for display. Had to delete `chroma_db` and re-embed. After that, Dec 2025 and Dec 2022 recording reviews rank #1 and #2 and the system answers yes.

---

### Failure 2 (fixed): Christopher Kane CSE 307 tags — retrieval metadata stage

**Question that failed:** What Rate My Professor tags do students assign to Christopher Kane for CSE 307?

**What the system returned (before fix):** Declined to answer, or listed tags from CSE215/CSE310 reviews instead of CSE307.

**Root cause:** **Retrieval without metadata filtering.** Global semantic search favored Kane's more numerous CSE215 reviews. Tags were stripped from embedding text, so the query word "tags" matched any tagged review regardless of course.

**What you would change to fix it:** Add professor + course `where` filters in `retriever.py` when names appear in the query. Include RMP tag lines in `build_embedding_text()`.

---

### Failure 3 (fixed): Scott Stoller course list — generation filtering stage

**Question that failed:** What courses does Scott Stoller teach according to student reviews?

**What the system returned (before fix):** Only CSE308, missing CSE535 and CSE302 — even after retrieval returned multiple Stoller courses.

**Root cause:** **Generation chunk filter.** `_filter_chunks()` used a fixed `MAX_DISTANCE = 0.55`. Stoller's CSE535 (distance 0.61) and CSE302 (0.73) chunks were retrieved but dropped before the LLM saw them. Only CSE308 (0.41) survived.

**What you would change to fix it:** Use a relative threshold (`best_distance + 0.35`) and, for "what courses" queries, deduplicate retrieved chunks by course code within the named professor's reviews.

---

### Remaining partial failure: Kane tag phrasing — generation stage

**Question:** What Rate My Professor tags do students assign to Christopher Kane for CSE 307?

**What the system returns now:** Correct core tags from the Mar 2026 review, but also tags from the May 2020 CSE307 review (RESPECTED, CARING) and splits "ACCESSIBLE OUTSIDE CLASS" into two tokens.

**Root cause:** **Generation.** Two CSE307 chunks are passed to the LLM; it merges tags from both reviews. The prompt does not instruct the model to prefer the most recent review or deduplicate tag strings.

**What you would change:** Retrieve only the single best-matching chunk for tag-specific questions, or post-process tag lines programmatically from chunk metadata instead of asking the LLM to list them.

---

## Spec Reflection

**One way the spec helped you during implementation:**

`planning.md` forced me to choose review-boundary chunking and top-k = 5 before writing code, which kept each retrieved unit self-contained (course + tags + comment together). The evaluation plan also gave concrete test questions — when Paul Fodor recording failed, I had an expected answer to compare against instead of guessing whether the system was "good enough."

**One way your implementation diverged from the spec, and why:**

The spec assumed pure semantic search over full review chunks would be sufficient. In practice, embedding had to use a separate compact text (`build_embedding_text()`), and retrieval needed professor/course metadata filters and course deduplication for multi-course questions. Without those changes, three of five eval questions failed despite the documents containing the answers.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* My Milestone 2 `planning.md` chunking section and a request to implement `chunk_document()` in `ingest.py` using review-boundary splitting.
- *What it produced:* A regex-based splitter on the `====` delimiter blocks with metadata fields (`course`, `date`, `chunk_id`) attached to each chunk.
- *What I changed or overrode:* I kept the review-boundary approach but wrote the PDF parsing pipeline myself (`parse_reviews`, tag extraction, noise filtering) after inspecting raw pdfplumber output — the AI did not handle the RMP page layout correctly on the first pass.

**Instance 2**

- *What I gave the AI:* The Paul Fodor eval question failed even though the Dec 2025 review says "he records his lectures." I pushed back when it tried to fix it by increasing k — I said that's not the issue, relevance just isn't mapped properly between the query and the right chunk.
- *What it produced:* Found that embedding the full chunk was the problem, not weak `record` → `recording` synonyms. Suggested compact embed text (embed the recording sentence only) instead of a bigger retrieval pool.
- *What I changed or overrode:* Kept k = 5. Used `build_embedding_text()` + re-embed. Also added professor/course filters later when Kane and Stoller queries failed for similar reasons.

---

## Extra Credit: Hybrid Search

**Feature:** Optional hybrid retrieval (`semantic` + BM25 merged with Reciprocal Rank Fusion). Toggle in the Gradio **Retrieval mode** dropdown, or set `RETRIEVAL_MODE=hybrid` in `.env`.

**How it works:** Each query runs MiniLM cosine search and BM25 keyword search over the same compact embed text (`build_embedding_text`). Top-20 from each method are merged with RRF (k = 60), then top-5 go to the LLM. Same professor/course metadata filters apply to both.

**Compare yourself:** `python retriever.py --compare`

| Eval question | Semantic top-1 on-target? | Hybrid top-1 on-target? | Winner |
|---------------|---------------------------|-------------------------|--------|
| Fodor records lectures? | Yes (Dec 2025, "records his lectures") | No (Apr 2026 review, no recording mention) | **Semantic** |
| Kane CSE307 tags? | Yes (Mar 2026, TOUGH GRADER…) | Yes (same review) | Tie |
| Stoller courses? | Partial (CSE308 only in #1) | Partial (same) | Tie |
| Ramakrishnan CSE596? | Yes (CSE596 review) | Yes (same) | Tie |
| Ali Raza ISE218 exams? | Yes ("topics of questions prior") | Yes (same) | Tie |

**Takeaway:** Hybrid helps when exact keywords matter (tags, "record", course codes) — but after the compact-embedding fix, semantic-only already ranked the right reviews for most eval questions. On the Fodor query, BM25 overweighted the token `114` from the question and pushed a newer review without "record" to #1, so **semantic-only actually wins** there. Hybrid is still useful as a fallback for tag-heavy queries and is available in the UI for side-by-side testing.

---

## Extra Credit: Conversational Memory

**Feature:** Multi-turn chat in the Gradio **Chat** tab. Follow-up questions can use pronouns or omit the professor/course when the prior turn already established them.

**How it works:**

1. **Retrieval expansion** — `resolve_query_for_retrieval()` in `generator.py` scans the last few chat turns for the most recent professor name and course code. If the new question uses follow-up language (e.g. "he", "that class") or omits those entities, the retrieval query is expanded (e.g. `"Does he record lectures?"` → `"Paul Fodor: Does he record lectures? (course CSE114)"`) so metadata filters and embeddings target the right reviews.
2. **Generation context** — Recent user/assistant turns are prepended to the LLM prompt so the model can resolve pronouns when answering, while still grounding facts only in retrieved reviews.

**Demo interaction (Chat tab):**

| Turn | User | System behavior |
|------|------|-----------------|
| 1 | What do students say about Paul Fodor for CSE 114? | Retrieves Fodor + CSE114 reviews; answers from those chunks |
| 2 | Does he record his lectures? | Expands to Paul Fodor / CSE114 for retrieval; answer cites recording reviews — not a random "he" from another professor |

The single-turn **Ask** tab is unchanged for one-off questions with explicit professor/course names.
