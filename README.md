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

<!-- Run these 3 queries through your retrieval system and record the top returned chunks.
     For at least 2 of the 3, explain why the returned chunks are relevant to the query.
     Results must be text, not screenshots. -->

**Query 1:** Does Paul Fodor record his lectures for CSE 114?

Top returned chunks:
- [1] `paul_fodor` | CSE114 | distance: 0.4110 — CSE114 review praising Fodor as a helpful, brilliant instructor (Apr 2015)
- [2] `paul_fodor` | CSE114 | distance: 0.4128 — CSE114 review: lectures well organized and super clear (Nov 2013)
- [3] `paul_fodor` | CSE114 | distance: 0.4195 — CSE114 review: respectable, helpful professor (Jan 2015)
- [4] `paul_fodor` | CSE307 | distance: 0.4196 — Tags: TOUGH GRADER, RESPECTED; discusses lecture quality
- [5] `paul_fodor` | CSE114 | distance: 0.4253 — CSE114 review: helpful, passionate, available outside class

Relevance explanation: All top results are Paul Fodor reviews, and four of five are specifically for CSE114. They discuss lecture quality and teaching style, which is on-topic for a question about how Fodor runs CSE114 lectures. The exact "he records his lectures" review ranks lower (~24th) because many CSE114 reviews praise lectures generally without mentioning recording — a known limitation when one professor dominates the corpus.

---

**Query 2:** What Rate My Professor tags do students assign to Christopher Kane for CSE 307?

Top returned chunks:
- [1] `christopher_kane` | CSE215 | distance: 0.3740 — Tags: EXTRA CREDIT, AMAZING LECTURES, LOTS OF HOMEWORK
- [2] `christopher_kane` | CSE310 | distance: 0.3876 — Tags: GIVES GOOD FEEDBACK, RESPECTED, ACCESSIBLE OUTSIDE CLASS
- [3] `christopher_kane` | CSE215 | distance: 0.3939 — Tags: EXTRA CREDIT, CLEAR GRADING CRITERIA, LECTURE HEAVY
- [4] `christopher_kane` | CSE215 | distance: 0.4161 — Tags: EXTRA CREDIT, AMAZING LECTURES, ACCESSIBLE OUTSIDE CLASS
- [5] `christopher_kane` | CSE215 | distance: 0.4279 — Tags: GIVES GOOD FEEDBACK, RESPECTED, HILARIOUS

Relevance explanation: Every result is a Christopher Kane review that includes RMP tags in the chunk text, directly answering the "what tags" part of the query. The top results skew toward CSE215 rather than CSE307 because Kane has more CSE215 reviews and the embedding model weights tag vocabulary similarity. The Mar 2026 CSE307 review with TOUGH GRADER / LECTURE HEAVY / ACCESSIBLE OUTSIDE CLASS is in the corpus but ranks outside the top 5.

---

**Query 3:** What do students say about I.V. Ramakrishnan's CSE 596 class?

Top returned chunks:
- [1] `iv_ramakrishnan` | CSE537 | distance: 0.3216 — tough grader, hard to understand accent, lectures were nightmares
- [2] `iv_ramakrishnan` | CSE596 | distance: 0.3221 — Quality 1.0; not helpful, unprepared for lectures, bad attitude
- [3] `iv_ramakrishnan` | RESCH000 | distance: 0.3238 — Quality 1.0; hard to talk to, possessive, secretive
- [4] `iv_ramakrishnan` | CSE537 | distance: 0.3313 — unorganized lectures, poor accent, do not recommend
- [5] `iv_ramakrishnan` | CSE537 | distance: 0.3607 — accent hard to understand, poorly organized slides

Relevance explanation: All five results are negative I.V. Ramakrishnan reviews — exactly the kind of student sentiment the query asks about. Result #2 is a direct CSE596 review describing an unpleasant experience (Quality 1.0, unprepared lectures). Adding the professor name to each chunk header during ingestion fixed an earlier failure where Paul Fodor reviews drowned out Ramakrishnan because the review text never contained the professor's name.

---

## Grounded Generation

<!-- Explain how your system enforces grounding. How does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents." Show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Example Responses

<!-- Provide at least 2 grounded responses (query + response + source attribution)
     and 1 out-of-scope query showing your system's refusal.
     All entries must be text, not screenshots. -->

**Grounded response 1**

Query:

Response:

Source attribution:

---

**Grounded response 2**

Query:

Response:

Source attribution:

---

**Out-of-scope query**

Query:

System response (refusal):

---

## Query Interface

<!-- Describe your query interface: what are the input fields, what does the output look like?
     Then provide a complete sample interaction transcript showing a real exchange. -->

**Input fields:**

**Output format:**

---

**Sample Interaction Transcript**

<!-- Show a complete query → response exchange as it actually appears in your interface.
     Must be text, not a screenshot. -->

> **User:** 

> **System:** 

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest. A partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context, so the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2-3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
