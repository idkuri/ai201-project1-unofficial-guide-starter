# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This guide is about **CS professor reviews at Stony Brook**. SOLAR tells you who's teaching this semester, but it won't tell you who students actually recommend, whether a professor is an easy grader vs someone who helps you learn, or which courses they tend to teach. A high RMP rating alone doesn't tell the full story either. Students care about different things: tough grading, lecture quality, workload, group projects, office hours, and whether they'd take the class again.

That info is spread across Rate My Professors. You have to open each professor's page, scroll through reviews, and match comments to specific courses like CSE 114 or CSE 316. It's useful for picking classes and planning ahead, but annoying to dig through manually. This project collects those reviews in one place so you can ask questions like "Does Fodor record lectures for CSE 114?", "What tags do students give Kane for CSE 307?", or "What do reviews say about Ramakrishnan's CSE 596 class?" instead of clicking through ten different profiles.

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

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Sample Chunks

<!-- Paste 5 representative chunks from your document collection after running your ingestion pipeline.
     For each chunk, note which source document it came from.
     These must be actual text, not screenshots. -->

| # | Source document | Chunk text |
|---|----------------|------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Retrieval Test Results

<!-- Run these 3 queries through your retrieval system and record the top returned chunks.
     For at least 2 of the 3, explain why the returned chunks are relevant to the query.
     Results must be text, not screenshots. -->

**Query 1:**

Top returned chunks:
-
-
-

Relevance explanation:

---

**Query 2:**

Top returned chunks:
-
-
-

Relevance explanation:

---

**Query 3:**

Top returned chunks:
-
-
-

Relevance explanation:

---

## Generation Approach

<!-- Describe how you prompt the LLM to generate grounded answers.
     Include:
     - How you format retrieved chunks into the prompt context
     - Any instructions you give the model about staying within retrieved context
     - How you handle cases where retrieval returns nothing relevant
     - Any choices you made (e.g., how you formatted the context, whether you filtered low-relevance chunks). -->

---

## Evaluation Report

<!-- Run your 5 evaluation questions (from planning.md) through the full system.
     For each question, record:
     - The question you asked
     - The system's response
     - Whether the response was correct, partially correct, or wrong — and why
     - What you would change to improve it (if anything) -->

**Question 1:**

Response:

Assessment:

---

**Question 2:**

Response:

Assessment:

---

**Question 3:**

Response:

Assessment:

---

**Question 4:**

Response:

Assessment:

---

**Question 5:**

Response:

Assessment:

---

## Reflection

<!-- Answer these three questions honestly. Short paragraphs are fine. -->

**What worked well in your pipeline?**

**What didn't work, and what would you change?**

**How did you use AI tools during this project? Give one specific example where an AI suggestion was wrong and how you caught or fixed it.**

---

## AI Tool Usage Log

<!-- For each milestone, note which AI tool you used, what you asked it to do,
     and whether the output was useful as-is or needed modification.
     "I used ChatGPT" is not enough — describe a specific interaction. -->

| Milestone | Tool | What you asked | Outcome |
|-----------|------|----------------|---------|
| Planning | | | |
| Ingestion & chunking | | | |
| Embedding & retrieval | | | |
| Generation & interface | | | |
