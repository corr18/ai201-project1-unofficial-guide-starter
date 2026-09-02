# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors — Howard University Computer Science professor index | Listing page (used to find every CS professor with written reviews) | https://www.ratemyprofessors.com/search/professors/421?q=*&did=11 |
| 2 | Jeremy Blackstone — Computer Science, Howard University | Student reviews (12 written) | https://www.ratemyprofessors.com/professor/2640220 — `documents/rmp_jeremy-blackstone.txt` |
| 3 | Anamika Rupa — Computer Science, Howard University | Student reviews (6 written) | https://www.ratemyprofessors.com/professor/2976470 — `documents/rmp_anamika-rupa.txt` |
| 4 | Noha Hazzazi — Computer Science, Howard University | Student reviews (14 written) | https://www.ratemyprofessors.com/professor/2418869 — `documents/rmp_noha-hazzazi.txt` |
| 5 | Saurav Aryal — Computer Science, Howard University | Student reviews (8 written) | https://www.ratemyprofessors.com/professor/2672438 — `documents/rmp_saurav-aryal.txt` |
| 6 | Alex Krentsel — Computer Science, Howard University | Student reviews (2 written) | https://www.ratemyprofessors.com/professor/2725790 — `documents/rmp_alex-krentsel.txt` |
| 7 | Jiang Li — Computer Science, Howard University | Student reviews (26 written) | https://www.ratemyprofessors.com/professor/2323879 — `documents/rmp_jiang-li.txt` |
| 8 | Gloria Washington — Computer Science, Howard University | Student reviews (18 written) | https://www.ratemyprofessors.com/professor/2084505 — `documents/rmp_gloria-washington.txt` |
| 9 | Moses Garuba — Computer Science, Howard University | Student reviews (11 written) | https://www.ratemyprofessors.com/professor/287385 — `documents/rmp_moses-garuba.txt` |
| 10 | Anil Jain — Computer Science, Howard University | Student reviews (11 written) | https://www.ratemyprofessors.com/professor/548120 — `documents/rmp_anil-jain.txt` |
| 11 | Linwei Niu — Computer Science, Howard University | Student reviews (8 written) | https://www.ratemyprofessors.com/professor/2719629 — `documents/rmp_linwei-niu.txt` |
| 12 | Danny Harris — Computer Science, Howard University | Student reviews (7 written) | https://www.ratemyprofessors.com/professor/956152 — `documents/rmp_danny-harris.txt` |
| 13 | A. Nicki Washington — Computer Science, Howard University | Student reviews (6 written) | https://www.ratemyprofessors.com/professor/997067 — `documents/rmp_nicki-washington.txt` |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One complete RateMyProfessors review card per chunk — the rating header (quality, difficulty, course, date, attendance, grade), the student's written comment, and the tags they selected. Measured across the corpus: 20–133 estimated tokens, median 92. I set a 350-token hard ceiling for safety, but no real review reached it.

**Overlap:** 0 tokens. Each review is already a self-contained opinion by one student, so carrying text across a boundary would attribute one student's words to another student's review.

**Why these choices fit your documents:** RateMyProfessors is not prose — it is a stack of independent review cards, so the document's own structure already marks where one retrievable thought ends and the next begins. A fixed-size window would cut mid-review and merge the end of one student's complaint with the start of another's praise, which is exactly the confusion this domain punishes. Chunking on the card boundary means every retrieved chunk answers with one student's full experience plus the ratings that contextualize it.

**Preprocessing before chunking:** Collected with `collect_sources.py` (Playwright drives Chrome, since RateMyProfessors renders reviews client-side and a plain HTTP fetch returns none). Each source is normalized to plain text in `raw_text/` before cleaning. Cleaning then strips HTML tags and entities, nav menus, cookie banners, footers, "Load More Ratings"/"Helpful"/"Share" chrome, and zero-width copy-paste characters, and normalizes course codes (`CSCI201`, `CSCI-201` → `CSCI 201`) so a question that spaces the code matches a review that didn't. Ratings with no written comment are dropped at collection — a star with no text carries no opinion to retrieve.

**Final chunk count:** 129

---

## Sample Chunks

<!-- Paste 5 representative chunks from your document collection after running your ingestion pipeline.
     For each chunk, note which source document it came from.
     These must be actual text — not screenshots. -->

| # | Source document | Chunk text |
|---|----------------|------------|
| 1 | rmp_gloria-washington.txt | Quality: 1.0<br>Difficulty: 3.0<br>Course: CSCI 135<br>Date: Apr 26th, 2023<br>For Credit: Yes<br>Attendance: Mandatory<br>Grade: A<br>Textbook: N/A<br>She never gives clear instructions and is an absolute nightmare to have a civil conversation with. Not recommended.<br>Tags: Group Projects |
| 2 | rmp_anamika-rupa.txt | Quality: 2.0<br>Difficulty: 2.0<br>Course: CSCI 120<br>Date: Mar 19th, 2024<br>For Credit: Yes<br>Attendance: Mandatory<br>Grade: A<br>Textbook: N/A<br>She was new when I had her, and for the most part it seemed like she didn't know what she was doing. It was an easy class, but I can't really say that I learned anything from her. She was very lenient with her grading though. Also, for a class called exploring computer science, we didn't really learn much about computer science.<br>Tags: Participation Matters, Lots Of Homework, Lecture Heavy |
| 3 | rmp_jiang-li.txt | Quality: 3.0<br>Difficulty: 5.0<br>Course: CS 201<br>Date: Dec 1st, 2022<br>For Credit: Yes<br>Attendance: Mandatory<br>Would Take Again: Yes<br>Grade: A<br>Textbook: N/A<br>Online Class: Yes<br>this class is hard and the homework/projects require a lot of time. dr li's lectures are boring but he's helpful especially if you go to office hours. he is considerate if you meet him with a legitimate reason. overall, the workload is excessive but makes you learn the material. he gives quizzes in class based on the previous lecture<br>Tags: Clear Grading Criteria, Lots Of Homework, Lecture Heavy |
| 4 | rmp_jiang-li.txt | Quality: 5.0<br>Difficulty: 1.0<br>Course: CS 201<br>Date: Jun 17th, 2025<br>For Credit: Yes<br>Attendance: Not Mandatory<br>Would Take Again: Yes<br>Grade: C+<br>Textbook: Yes<br>I LOVE Dr. Li hes the GOAT i would take him again<br>Tags: Inspirational, Caring, Respected |
| 5 | rmp_jiang-li.txt | Quality: 1.0<br>Difficulty: 5.0<br>Course: CSCI 201<br>Date: May 4th, 2026<br>For Credit: Yes<br>Attendance: Mandatory<br>Grade: D+<br>Textbook: N/A<br>Do not take this class if you love your life. He will drain you and drain your GPA. He does not care about his students at all, no opportunity for extra credit. He decides Willy nilly if you cheated on a project and make you interview for a grade on a project. Take the other professor, wait as long as you need to take another professor.<br>Tags: Tough Grader, Graded By Few Things |

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
     Results must be text — not screenshots. -->

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

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Example Responses

<!-- Provide at least 2 grounded responses (query + response + source attribution)
     and 1 out-of-scope query showing your system's refusal.
     All entries must be text — not screenshots. -->

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
     Must be text — not a screenshot. -->

> **User:** 

> **System:** 

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
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
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

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
