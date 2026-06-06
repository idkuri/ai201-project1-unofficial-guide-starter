# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Rate My Professor and course planning at Stony Brook University (CS department)**

I'm building a guide for picking CS professors and planning courses ahead of time. SOLAR tells you who's teaching this semester, but it won't tell you who students actually recommend, if someone is an easy grader or actually helps you learn, or which courses they usually teach. That info lives on Rate My Professors, and you have to click through each professor, scroll tons of reviews, and figure out which comments match courses like CSE 114 or CSE 316 on your own.

A high rating doesn't say much by itself. Students care about grading, lecture quality, workload, group projects, office hours, and whether they'd take the class again. Having all that in one place lets you plan semesters ahead instead of scrambling at registration and ending up in a bad section.

**Questions this system will answer:**

- Does a specific professor record lectures or offer flexible office hours for a course?
- What Rate My Professor tags and ratings do students give a professor for a particular class?
- Which courses does a professor usually teach, based on review history?
- What do students say about a professor's grading difficulty, workload, or teaching style?
- How does a professor prepare students for exams or handle course logistics (group projects, attendance, etc.)?

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Scott Stoller | Full Rate My Professor review history (CSE308, CSE535, distributed systems/project courses) | `raw/Scott Stoller at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 2 | Christopher Kane | Full Rate My Professor review history (CSE215, CSE307, CSE316, software design and theory) | `raw/Christopher Kane at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 3 | Ali Raza | Full Rate My Professor review history (ISE218, CSE312, intro and systems courses) | `raw/Ali Raza at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 4 | Amir Rahmati | Full Rate My Professor review history (CSE524, security and grad-level CS courses) | `raw/Amir Rahmati at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 5 | Dimitris Samaras | Full Rate My Professor review history (CSE327 computer vision, grad-level courses) | `raw/Dimitris Samaras at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 6 | Eugene Stark | Full Rate My Professor review history (CSE306, CSE320, systems and architecture courses) | `raw/Eugene Stark at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 7 | Himanshu Gupta | Full Rate My Professor review history (networking and upper-level CS courses) | `raw/Himanshu Gupta at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 8 | I.V. Ramakrishnan | Full Rate My Professor review history (CSE596, grad courses; mixed grading and teaching reviews) | `raw/I.V. Ramakrishnan at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 9 | Michael Ferdman | Full Rate My Professor review history (CSE356, CSE502, computer architecture and systems) | `raw/Michael Ferdman at Stony Brook University (SUNY) _ Rate My Professors.pdf` |
| 10 | Paul Fodor | Full Rate My Professor review history (CSE114, CSE214, CSE316; largest review count in corpus) | `raw/Paul Fodor at Stony Brook University (SUNY) _ Rate My Professors.pdf` |

**Coverage:** Intro programming (Fodor), software design/theory (Kane), systems/architecture (Stark, Ferdman), distributed systems (Stoller), security/grad courses (Rahmati), computer vision (Samaras), networking (Gupta), and a mix of strongly positive and strongly negative grad-level reviews (Ramakrishnan). All sources are manually saved Rate My Professor PDFs because the site blocks automated scraping.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Does Paul Fodor record his lectures for CSE 114? | Yes. Multiple reviews explicitly state he records lectures (e.g., "he records his lectures" in Dec 2025 and Nov 2024 CSE114 reviews). |
| 2 | What Rate My Professor tags do students assign to Christopher Kane for CSE 307? | TOUGH GRADER, LECTURE HEAVY, ACCESSIBLE OUTSIDE CLASS. The Mar 2026 review also gives Quality 5.0 and Difficulty 5.0. |
| 3 | What courses does Scott Stoller teach according to student reviews? | CSE308, CSE535, and CSE302. Reviews describe distributed systems content, research papers, and group/project-based coursework. |
| 4 | What do students say about I.V. Ramakrishnan's CSE 596 class? | Overwhelmingly negative: Quality 1.0, Difficulty 5.0, tagged TOUGH GRADER. Reviews describe him as disrespectful, toxic, and berating students. At least one review says "NEVER TAKE HIS COURSE." |
| 5 | How does Ali Raza prepare students for exams in ISE 218? | He gives topics or questions prior to exams and quizzes. Reviews note tough exams but clear expectations, and that he checks whether the class understands before moving on. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
