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

Student reviews of Computer Science professors at Howard University. The system answers questions about what students actually say about a professor's teaching style, exam difficulty, workload, grading, and availability outside class.

This knowledge is valuable because it is not in any official channel. The course catalog lists titles and credit hours; it says nothing about whether a professor's exams cover material that was never lectured, whether homework takes eight hours, or whether asking a question in class gets you help or ridicule. Students normally get this by asking around, which depends on knowing the right people, and the answers you get in person are often softened — nobody wants to trash a professor to your face. An anonymous review corpus captures the blunt version, and 129 of those reviews across 12 professors say more together than any single conversation would.

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

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, producing 384-dimensional vectors, stored in a persistent ChromaDB collection configured with `hnsw:space = "cosine"`. It runs locally with no API key and no rate limit, and it handles the core problem in this domain: students phrase questions differently from the way reviews are written. Nobody writes "is the workload heavy" in a review — they write "assignments were unrealistic in load and very time-consuming" — and MiniLM matches those.

One thing I changed after seeing results: I do not embed the raw review card. A card is mostly identical form fields (`For Credit: Yes`, `Textbook: N/A`, a date, a letter grade) and it never contains the professor's name, which lives in the file header. Embedding the card verbatim meant "workload for CSCI 201 with Jiang Li" returned **Gloria Washington** reviews at distance 0.53. I now embed a written-out context sentence ("Student review of Professor Jiang Li for the course CSCI 201 in the Computer Science department at Howard University. The student rated quality 1.0 out of 5 and difficulty 5.0 out of 5.") followed by the student's comment and tags. The full card is still what gets stored and cited. Same query now returns Jiang Li at 0.45.

**Production tradeoff reflection:** If cost weren't a constraint I'd weigh a larger API-hosted model (OpenAI `text-embedding-3-large`, Voyage, Cohere) against MiniLM on four axes. **Accuracy on domain-specific text** matters most here: my corpus is slang-heavy, misspelled, and sarcastic ("hes the GOAT", "do not take this class if you love your life"), and a bigger model trained on more informal text would likely separate "tough but fair" from "tough and unfair" better than MiniLM does — that distinction is exactly what a student asking "is he hard?" wants. **Context length** matters least: my chunks top out at 133 tokens, far under MiniLM's 256-token window, so a 8k-token window buys me nothing. **Latency and cost** would get worse — MiniLM embeds all 129 chunks in about a second locally, and an API model adds a network round trip to every single query, which for a UI that people click through is a real regression. **Multilingual support** is irrelevant for this corpus but would matter if I expanded to international student reviews. The honest summary is that my retrieval failures (see Failure Case Analysis) come from chunk granularity and top-k, not from MiniLM's ceiling, so a bigger embedding model would not have fixed them.

---

## Retrieval Test Results

<!-- Run these 3 queries through your retrieval system and record the top returned chunks.
     For at least 2 of the 3, explain why the returned chunks are relevant to the query.
     Results must be text — not screenshots. -->

**Query 1:** "What do students say about the difficulty of Jiang Li's exams?"

Top returned chunks (cosine distance, lower is closer):

- **0.303** — Jiang Li, CSCI 201 (`rmp_jiang-li.txt`, chunk 16): "This is a difficult class! The lectures are long and packed with information. They are difficult to sit through as well. The homework system is horrible and takes hours to complete. His exams are extremely difficult in comparison to the homework and example problems. As a professor Li is very monotonous and inconsiderate."
- **0.327** — Jiang Li, CS 201 (`rmp_jiang-li.txt`, chunk 11): "Just a horrible teacher, and he created his own website for homeworks and exams which is filled with difficult problems that he has never gone over during lecture and will never no matter how many times you ask."
- **0.345** — Jiang Li, CSCI 201 (`rmp_jiang-li.txt`, chunk 25): "This class was HARD. Period. The worst part was the online homework. The questions are not from any text book & it can take 8 hours to pass a single hw. If you want any hope of understanding material, YOU MUST GO TO HIM. He does respond to email quickly though. Exams are exactly like hw, but different numbers. Mips projects are graded with script."

Relevance explanation: All five results are Jiang Li reviews, and the top three are specifically about his exams rather than about him generally. The best result at 0.303 contains the sentence "His exams are extremely difficult in comparison to the homework and example problems," which is a direct answer to the question and not a keyword coincidence — the review never uses the word "difficulty" as the question does. The second at 0.327 adds *why* they're hard (problems never covered in lecture), and the third at 0.345 adds that exams mirror the homework with different numbers. Three independent students, three different semesters, one consistent picture.

---

**Query 2:** "What is the workload like for CSCI 201 with Jiang Li?"

Top returned chunks (cosine distance, lower is closer):

- **0.452** — Jiang Li, CSCI 450 (`rmp_jiang-li.txt`, chunk 13): "Terrible professor tbh. I'd advise taking it at another school."
- **0.482** — Jiang Li, CSCI 201 (`rmp_jiang-li.txt`, chunk 15): "Teacher is proud of saying nobody has ever gotten an A. Isn't flexible and won't help you if your failing. Homework takes hours and the test are even harder. Do not take this class it's extremely stressful and not worth your time!"
- **0.501** — Jiang Li, CSCI 450 (`rmp_jiang-li.txt`, chunk 5): "Hard but good"

Relevance explanation: Every result is Jiang Li, and the top result at 0.452 is a CSCI 450 review describing homework load rather than a CSCI 201 review, which is the honest weakness here: the course filter is soft, so the model gets workload evidence from the right professor but not always the right course number. Results 2, 4 and 5 are CSCI 201, and they carry the specific claims the answer used — "takes hours," "unrealistic in load," the homework website. This query is also the one that exposed the embedding bug: before I added the professor and course into the embedded text, the top result here was a Gloria Washington CSCI 136 review at 0.529.

---

**Query 3:** "Which professors give useful feedback on assignments or projects?"

Top returned chunks (cosine distance, lower is closer):

- **0.546** — Moses Garuba, CSCI 401 (`rmp_moses-garuba.txt`, chunk 2): "This is a cs professor that likes to see students succeed. But you have to put forth the effort. He notices when you miss class and will make a mental note when determining your final grade. The assignments are not always easy but he is there to answer your questions if you come to class. Best professor in explaining complex concepts in simple term"
- **0.557** — Noha Hazzazi, CSCI 100 (`rmp_noha-hazzazi.txt`, chunk 10): "Honestly, her class was really boring so I didn't listen to any of her lectures. But other than that she was really nice and helped people a lot. There are a lot of group projects which is kinda annoying. The test and quizzes are really easy just use your resources. Final was hard but I think she curved it."
- **0.561** — Gloria Washington, CSCI 580 (`rmp_gloria-washington.txt`, chunk 5): "Dr. Washington is super dope! The only professor in the department that i can really relate too! and thats saying alot."

Relevance explanation: This is the query that does **not** work, and I'm documenting it rather than hiding it. The top result at 0.546 is a Moses Garuba review that says he "is there to answer your questions if you come to class" — related to feedback, but not actually about feedback on assignments. Results 2 and 3 are simply positive reviews ("she was really nice and helped people a lot", "Dr. Washington is super dope") that share sentiment with the query but not substance. Meanwhile 15 chunks in the corpus literally contain the word "feedback," and the one tagged "Gives Good Feedback" for Jeremy Blackstone ranks **46th at distance 0.620**; Saurav Aryal's feedback review ranks **129th of 129**. See Failure Case Analysis for why.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

Grounding is enforced in three places, because the system prompt alone is a request, not a guarantee.

**1. System prompt** (verbatim, from [`generate.py`](generate.py)):

```
You answer questions about Howard University Computer Science professors using ONLY the
student reviews provided in the CONTEXT block of each message.

Rules, in order of priority:
1. Every claim you make must be supported by a specific review in the CONTEXT. Do not use
anything you know about these professors, these courses, or Howard University from outside
the CONTEXT.
2. If the CONTEXT is empty, or does not contain enough to answer, reply with exactly this
sentence and nothing else: "I don't have enough information on that."
3. Cite as you go. After each claim, name the review you took it from as [S1], [S2], etc.,
matching the source numbers in the CONTEXT.
4. When reviews disagree, say so and give both sides. Do not average conflicting opinions
into a single verdict, and do not smooth over a negative review because other reviews are
positive.
5. Attribute opinions to students, not to yourself: "students describe...", "one reviewer
says...".
6. Never invent a professor, course number, rating, or quotation that is not in the CONTEXT.
7. Be concise: 2-5 sentences unless the question asks you to compare several professors.
```

Rule 4 is domain-specific and it earns its place: this corpus contains professors rated 5.0 and 1.0 by different students in the same course, and a model that averages them produces a bland verdict that is true of nobody's actual experience.

**2. A relevance cutoff before the prompt is built.** Retrieved chunks above cosine distance 0.62 are dropped in Python. If everything is dropped, the model is never called at all — the refusal is returned directly. This is what makes the out-of-scope case airtight: for the dining-hall question the closest review was 0.737, so nothing reached the model and there was nothing for it to be creative with.

**3. Programmatic source attribution.** The `[S1]…[S5]` list under each answer is built from ChromaDB metadata (`professor`, `course`, `source_file`, `position`, `source_url`), not parsed out of the model's text. The model is *also* told to cite inline, so you can see which specific review each claim came from, but even if it cited nothing the source list would still be correct and complete.

**How source attribution is surfaced in the response:** every answer is returned with a source list naming the professor, course, source file, chunk position, and the RateMyProfessors URL for each retrieved review, plus the cosine distance. The Gradio UI shows this under the answer, and an expandable panel below it holds the full text of every review that was fed to the model — so a reader can check any claim against the review it came from without leaving the page.

---

## Example Responses

<!-- Provide at least 2 grounded responses (query + response + source attribution)
     and 1 out-of-scope query showing your system's refusal.
     All entries must be text — not screenshots. -->

**Grounded response 1**

Query: What do students say about the difficulty of Jiang Li's exams?

Response:

> Students describe Professor Jiang Li’s exams as extremely difficult, often harder than the homework and example problems [S1]. One reviewer notes that the exam questions are “filled with difficult problems that he has never gone over during lecture” [S2]. Another student adds that the exams are essentially the same as the very time‑consuming homework, just with different numbers [S3].

Source attribution:

- [S1] Jiang Li — CSCI 201 — rmp_jiang-li.txt (chunk 16) — https://www.ratemyprofessors.com/professor/2323879
- [S2] Jiang Li — CS 201 — rmp_jiang-li.txt (chunk 11) — https://www.ratemyprofessors.com/professor/2323879
- [S3] Jiang Li — CSCI 201 — rmp_jiang-li.txt (chunk 25) — https://www.ratemyprofessors.com/professor/2323879

Cosine distances: 0.303, 0.327, 0.345, 0.357, 0.365

---

**Grounded response 2**

Query: How do Jiang Li and Jeremy Blackstone compare on workload and exam difficulty?

Response:

> Students describe Professor Jiang Li’s courses as having a very heavy workload—homework can take many hours (up to eight for a single assignment) and projects are time‑intensive—and his exams as “extremely difficult” and tougher than the homework problems [S1][S2][S3].  
In contrast, reviewers of Professor Jeremy Blackstone note that his classes have few, easy assignments and “take up little time,” with exams that simply follow the homework structure, making them relatively easy [S5].

Source attribution:

- [S1] Jiang Li — CSCI 201 — rmp_jiang-li.txt (chunk 16) — https://www.ratemyprofessors.com/professor/2323879
- [S2] Jiang Li — CSCI 201 — rmp_jiang-li.txt (chunk 25) — https://www.ratemyprofessors.com/professor/2323879
- [S3] Jiang Li — CS 201 — rmp_jiang-li.txt (chunk 14) — https://www.ratemyprofessors.com/professor/2323879
- [S4] Jeremy Blackstone — CSCI 454 — rmp_jeremy-blackstone.txt (chunk 3) — https://www.ratemyprofessors.com/professor/2640220
- [S5] Jeremy Blackstone — CSCI 135 — rmp_jeremy-blackstone.txt (chunk 0) — https://www.ratemyprofessors.com/professor/2640220

Cosine distances: 0.441, 0.462, 0.463, 0.536, 0.544 — note that sources 4 and 5 (Blackstone) are only there because retrieval balances across professors when a question names more than one. Without that, all five results were Jiang Li and the comparison had only one side.

---

**Out-of-scope query**

Query: What are the best dining halls on Howard's campus and what are the wait times at lunch?

System response (refusal):

> I don't have enough information on that. None of the student reviews in this collection cover it (closest review was 0.737 away).

No sources are listed, because none were passed to the model: every retrieved chunk was above the 0.62 distance cutoff, so the refusal was returned without an LLM call.

---

## Query Interface

<!-- Describe your query interface: what are the input fields, what does the output look like?
     Then provide a complete sample interaction transcript showing a real exchange. -->

**Input fields:** a single free-text question box (submit with Enter or the Ask button), and a top-k slider (3–10, default 5) controlling how many reviews are retrieved. Five example questions are one click away so a first-time viewer knows what the system takes.

**Output format:** three stacked panels — **Answer** (the grounded response with inline `[S1]`-style citations), **Retrieved from** (one line per source: professor, course, source file, chunk position, RateMyProfessors URL), and a collapsed **The full reviews behind this answer** panel holding the complete text of every retrieved review with its distance. The last panel is what makes the system auditable: you can read the raw student review and check the answer against it.

Run it with `python app.py` and open http://localhost:7860.

---

**Sample Interaction Transcript**

<!-- Show a complete query → response exchange as it actually appears in your interface.
     Must be text — not a screenshot. -->

> **User:** What do students say about Gloria Washington's teaching style in CSCI 135?

> **System:**
>
> Students describe Professor Washington’s teaching style in CSCI 135 as unclear and difficult to follow—one reviewer says she “never gives clear instructions” and is “an absolute nightmare to have a civil conversation with” [S1]. Another reviewer calls her a “terrible professor,” noting that the class is “lecture‑heavy” and that she is a “tough grader” [S4].
>
> **Retrieved from:**
>
> [S1] Gloria Washington — CSCI 135 — rmp_gloria-washington.txt (chunk 2) — https://www.ratemyprofessors.com/professor/2084505
> [S2] Gloria Washington — CSCI 136 — rmp_gloria-washington.txt (chunk 13) — https://www.ratemyprofessors.com/professor/2084505
> [S3] Gloria Washington — CSCI 410 — rmp_gloria-washington.txt (chunk 0) — https://www.ratemyprofessors.com/professor/2084505
> [S4] Gloria Washington — CSCI 135 — rmp_gloria-washington.txt (chunk 3) — https://www.ratemyprofessors.com/professor/2084505
> [S5] Gloria Washington — CSCI 410 — rmp_gloria-washington.txt (chunk 17) — https://www.ratemyprofessors.com/professor/2084505
>
> distances: 0.334, 0.346, 0.35, 0.369, 0.376

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about the difficulty of Jiang Li's exams? | Summarize whether students describe his exams as easy, medium or hard, with any comments about preparation or exam material. | Exams are extremely difficult, harder than the homework and example problems; questions cover material never gone over in lecture; exams mirror the homework with different numbers. Cited 3 reviews. | Relevant (0.303–0.365, all Jiang Li, all about exams) | **Accurate** |
| 2 | What is the workload like for CSCI 201 with Jiang Li? | Describe the workload as manageable/heavy/etc., mentioning homework, projects, or study time. | Workload is extremely heavy: homework \"takes hours\", assignments \"unrealistic in load and very time-consuming\", the homework website called \"torture\". Cited 3 reviews. | Partially relevant (0.452–0.516, all Jiang Li, but the top hit is CSCI 450 rather than CSCI 201) | **Accurate** |
| 3 | Which professors give useful feedback on assignments or projects? | Identify professors whose reviews mention detailed, helpful, or constructive feedback, citing the supporting reviews. | Named only Moses Garuba, and stated that no other professor in the provided reviews is described as giving feedback — which is true of the 5 chunks it was given and false of the corpus. | Off-target (0.546–0.570; the reviews that actually say \"feedback\" rank 46th, 74th, 85th, 111th and 129th) | **Partially accurate** — grounded in what it was given, but the retrieval under-reports the corpus |
| 4 | What do students say about Gloria Washington's teaching style in CSCI 135? | Summarize comments on her lectures, explanations, availability, and communication, not just her overall rating. | Teaching style described as unclear and hard to follow — \"never gives clear instructions\", \"an absolute nightmare to have a civil conversation with\", lecture-heavy with tough grading. Cited 2 CSCI 135 reviews. | Relevant (0.334–0.376, all Gloria Washington; 2 of 5 are CSCI 135, the rest are her other courses) | **Accurate** |
| 5 | How do Jiang Li and Jeremy Blackstone compare on workload and exam difficulty? | Compare the two professors on workload and exam difficulty using evidence from each one's reviews, citing sources. | Jiang Li: very heavy workload (up to eight hours per assignment), exams \"extremely difficult\" and harder than homework. Blackstone: few assignments, not difficult, exams follow the homework format. Cited 3 reviews for Li and 2 for Blackstone. | Relevant (0.441–0.544), and balanced across both professors only because retrieval splits top-k when a question names two | **Accurate** |

Plus an out-of-scope control: *"What are the best dining halls on Howard's campus and what are the wait times at lunch?"* → refused, closest review 0.737, no LLM call made.

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

**Question that failed:** "Which professors give useful feedback on assignments or projects?" (evaluation question 3)

**What the system returned:** *"Students note that Professor Moses Garuba is available to answer questions about assignments, indicating he provides useful feedback on coursework [S1]. No other professor in the provided reviews is described as giving feedback on assignments or projects."*

That second sentence is the tell. It is true of the five chunks the model received and false of the corpus: **15 of my 129 chunks contain the word "feedback"**, spread across six professors — Jeremy Blackstone (5 reviews), Noha Hazzazi (4), Moses Garuba (3), Alex Krentsel, Gloria Washington, and Saurav Aryal.

**Root cause (tied to a specific pipeline stage): the retrieval stage, and specifically the interaction between top-k and a corpus-wide question.** I measured where the feedback reviews actually rank for this query by retrieving all 129 chunks and reading off their positions:

| Chunk | Contains | Rank | Distance |
|---|---|---|---|
| `rmp_jeremy-blackstone::005` | tagged "Gives Good Feedback" | **46th** | 0.620 |
| `rmp_noha-hazzazi::002` | mentions feedback | 74th | 0.645 |
| `rmp_alex-krentsel::000` | tagged "Gives Good Feedback" | 85th | 0.651 |
| `rmp_jeremy-blackstone::010` | mentions feedback | 111th | 0.678 |
| `rmp_saurav-aryal::003` | mentions feedback | **129th of 129** | 0.746 |

Two things are going wrong at once, and both are structural rather than random:

1. **My chunks are one review each, and a review is *about a professor*, not *about feedback*.** The phrase "Gives Good Feedback" is three words inside a ~100-token embedding whose other 97 tokens are about exams, attendance and grading. Cosine similarity averages over the whole chunk, so that phrase is diluted below reviews that merely share the query's positive tone — which is why "Dr. Washington is super dope!" (0.561) outranks a review literally tagged as giving good feedback (0.620).
2. **top-k=5 cannot survey 12 professors.** Questions 1, 2, 4 and 5 all name a professor, so five chunks from one file is exactly the right budget. Question 3 asks about the *whole corpus*, and no five chunks can represent twelve people. The retrieval design that makes the other four questions work is the same design that makes this one fail.

Generation was not the problem. Given five chunks that did not contain the answer, the model correctly refused to invent one and said so — that is grounding working as intended. A non-grounded system would have confidently named three professors from its training data.

**What I would change to fix it:** the cheapest real fix is to **embed the tag list separately from the comment**, so "Gives Good Feedback, Amazing Lectures, Accessible Outside Class" becomes its own short vector per review instead of three words diluted inside a hundred. A short chunk whose entire content is the tag phrase would rank near the top for a query about feedback. Second, I would **detect corpus-wide questions** — ones naming no professor and no course — and answer them differently: retrieve per professor (k=2 across all 12) instead of a flat top-5, the same way I already balance retrieval when a question names two professors. Third, and least appealing, I could raise top-k for these questions, but at k=46 the context would be mostly noise and I would trade a retrieval failure for a generation one. I would not reach for a bigger embedding model here; the ranking failure is caused by chunk composition, and a stronger model would still average the same diluted chunk.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy section before any code committed me to "one review card per chunk, overlap 0" for a stated reason — each review is one student's self-contained experience. That decision then caught a bug I would otherwise have shipped. My first chunker treated any block under 40 tokens as a fragment and merged it into its neighbour, which quietly turned 129 reviews into 119 chunks by gluing short reviews onto other students' reviews. The count mismatch was only obviously *wrong* because the spec said the count should equal the number of review cards. Without that written rule I would have seen 119 chunks, assumed it was fine, and shipped chunks that attributed one student's praise to another student's rating. The spec turned an invisible defect into an arithmetic error.

**One way your implementation diverged from the spec, and why:** The spec said chunks would "typically" be 100–250 tokens. Reality came in at 20–133 tokens, median 92, with only 37% inside the predicted band — Howard CS reviews are much shorter than I assumed, and some are one sentence ("I LOVE Dr. Li hes the GOAT i would take him again"). I kept the boundary rule and abandoned the size target rather than the reverse, because the alternative — padding short reviews or merging neighbours to hit 100 tokens — would have reintroduced exactly the cross-attribution problem above. The 100–250 range now serves as a warning band in the chunk report rather than a splitting rule.

A second divergence worth recording: the spec said I'd embed the chunk text. I ended up embedding a *derived* string — a written-out context sentence naming the professor, course and ratings, followed by the comment and tags — because the review card never contains the professor's name and is otherwise mostly identical form fields. That change alone took "workload for CSCI 201 with Jiang Li" from returning Gloria Washington at 0.529 to returning Jiang Li at 0.452.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

I used Claude (Claude Code, Opus 5) throughout, driven by the sections of `planning.md` as the spec.

**Instance 1 — ingestion and chunking**

- *What I gave the AI:* my Chunking Strategy section (one review card per chunk, 100–250 tokens, overlap 0), the Documents table, and the pipeline diagram, with the requirement that every chunk carry professor, course, and source URL for later attribution.
- *What it produced:* `ingest.py` — a loader for `.txt`/`.md`/`.html`/`.pdf`, a cleaner, and a chunker that splits on review-card boundaries instead of a fixed character window. It also generated a "fragment merging" rule that attached any block under 40 tokens to its neighbour.
- *What I changed or overrode:* that merge rule was wrong for my data. It collapsed 129 reviews into 119 chunks by merging short-but-complete reviews into other students' reviews. I overrode it so that any block starting with its `Quality:` line is treated as a complete card no matter how short — "Excellent" is a whole review, not a fragment. I also rejected the assumption that HTML only appears in `.html` files, since pasted text drags tags along with it.

**Instance 2 — embedding and retrieval**

- *What I gave the AI:* my Retrieval Approach section (all-MiniLM-L6-v2, top-k=5), the chunk schema from ingestion, and the instruction to store in ChromaDB with source metadata.
- *What it produced:* `embed.py` embedding each chunk's text verbatim and storing it in Chroma with metadata.
- *What I changed or overrode:* three things, all after reading real results. (a) The generated code used Chroma's default distance space; I switched the collection to `hnsw:space = "cosine"` so distances read on the 0–1 scale the checkpoint refers to. (b) Embedding the card verbatim returned the wrong professor entirely — "workload for CSCI 201 with Jiang Li" gave Gloria Washington at 0.529 — because the card never names the professor and is padded with identical form fields. I changed what gets embedded to a context sentence plus the comment, which fixed it (0.452, correct professor) and improved every other test query. (c) A comparison question returned five Jiang Li reviews and zero Blackstone, so I added retrieval balancing when a question names two or more known professors.

**Instance 3 — collection, where the AI's first plan was wrong**

- *What I gave the AI:* the ten source URLs from my Documents table and the instruction to collect the review text.
- *What it produced:* first attempt fetched the pages over HTTP and got only the professor summary — RateMyProfessors renders reviews client-side, so the review text is not in the server HTML. Its second attempt was `collect_sources.py`, which drives Chrome with Playwright and clicks "Load More Ratings" until every review is loaded.
- *What I changed or overrode:* I dropped two of my ten planned sources rather than force them. Coursicle blocks automated browsers outright, and I chose not to work around a deliberate block; the Howard school page turned out to be campus reviews (food, dorms, wifi), which is off-domain and would have added retrieval noise. I replaced both with five more CS professors from the department index, which grew the corpus from 85 to 129 reviews and kept every source on-topic.

---

## Running this project

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chrome          # only needed to re-collect sources

cp .env.example .env               # add your GROQ_API_KEY

python collect_sources.py          # 1. scrape reviews into documents/  (optional; already collected)
python ingest.py --random 5        # 2. clean + chunk -> chunks.json, print 5 random chunks
python embed.py --rebuild          # 3. embed -> chroma_db/
python embed.py --test             # 4. retrieval only, with distances
python generate.py --test          # 5. grounded answers for all 5 eval questions + 1 out of scope
python app.py                      # 6. Gradio UI at http://localhost:7860
```

| File | Stage |
|---|---|
| [`collect_sources.py`](collect_sources.py) | Source collection (Playwright + Chrome) |
| [`ingest.py`](ingest.py) | Document ingestion and chunking |
| [`embed.py`](embed.py) | Embedding (all-MiniLM-L6-v2) and retrieval (ChromaDB) |
| [`generate.py`](generate.py) | Grounded generation (Groq) |
| [`app.py`](app.py) | Gradio query interface |

**Note on the LLM:** the course's suggested model `meta-llama/llama-4-scout-17b-16e-instruct` returns 404 `model_not_found` on my Groq account, so the default is `openai/gpt-oss-120b` (also free tier), with fallbacks and a `GROQ_MODEL` environment override.

video-https://youtu.be/aKyPVhpcfp8
