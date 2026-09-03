"""
Milestone 5 — Grounded generation.

Stage 5 of the pipeline in planning.md:

    retrieve(question, k=5) -> grounded prompt -> Groq -> answer + cited sources

Grounding is enforced three ways, not one:

    1. The system prompt forbids outside knowledge and requires a refusal
       sentence when the reviews don't cover the question.
    2. Chunks whose distance is above MAX_DISTANCE are dropped before the prompt
       is built, so a question the corpus can't answer arrives with an empty
       context block and the model has nothing to answer from.
    3. Source attribution is appended programmatically from the retrieval
       metadata. The model is asked to cite inline as well, but the source list
       under the answer is built in Python and cannot be hallucinated.

Usage:
    python generate.py "What do students say about Jiang Li's exams?"
    python generate.py --test         # the 5 evaluation questions + 1 out of scope
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

from dotenv import load_dotenv
from groq import Groq, NotFoundError

from embed import DEFAULT_K, retrieve

load_dotenv()

# The course's suggested model, meta-llama/llama-4-scout-17b-16e-instruct, is no
# longer served on this Groq account (404 model_not_found), so this uses the
# strongest free-tier chat model the key can reach. Override with GROQ_MODEL.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODELS = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
# Above this cosine distance a review isn't really about the question. Chosen
# from the Milestone 4 runs: on-topic reviews land at 0.30-0.50, and the
# loosest genuinely relevant result seen was 0.58.
MAX_DISTANCE = 0.62
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = f"""You answer questions about Howard University Computer Science professors \
using ONLY the student reviews provided in the CONTEXT block of each message.

Rules, in order of priority:
1. Every claim you make must be supported by a specific review in the CONTEXT. Do not use anything \
you know about these professors, these courses, or Howard University from outside the CONTEXT.
2. If the CONTEXT is empty, or does not contain enough to answer, reply with exactly this sentence \
and nothing else: "{REFUSAL}"
3. Cite as you go. After each claim, name the review you took it from as [S1], [S2], etc., matching \
the source numbers in the CONTEXT.
4. When reviews disagree, say so and give both sides. Do not average conflicting opinions into a \
single verdict, and do not smooth over a negative review because other reviews are positive.
5. Attribute opinions to students, not to yourself: "students describe...", "one reviewer says...".
6. Never invent a professor, course number, rating, or quotation that is not in the CONTEXT.
7. Be concise: 2-5 sentences unless the question asks you to compare several professors."""


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise SystemExit("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return Groq(api_key=key)


def source_label(result: dict) -> str:
    """One-line citation built from metadata, not from the model's output."""
    meta = result["metadata"]
    course = meta.get("course", "course not stated")
    return (
        f"{meta.get('professor', 'Unknown professor')} — {course} — "
        f"{meta['source_file']} (chunk {meta['position']}) — {meta.get('source_url', '')}"
    )


def build_prompt(question: str, results: list[dict]) -> str:
    """Format the retrieved reviews as the CONTEXT block the system prompt refers to."""
    if not results:
        return (
            "CONTEXT:\n(no reviews matched this question)\n\n"
            f"QUESTION: {question}\n\n"
            "Follow rule 2."
        )

    blocks = []
    for i, result in enumerate(results, 1):
        meta = result["metadata"]
        blocks.append(
            f"[S{i}] Review of Professor {meta.get('professor', '?')}"
            f"{' for ' + meta['course'] if meta.get('course') else ''}"
            f" (source file: {meta['source_file']}, chunk {meta['position']}, "
            f"similarity distance {result['distance']:.3f})\n{result['text']}"
        )

    return (
        "CONTEXT:\n" + "\n\n".join(blocks) + "\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the reviews above, citing [S1]-style markers."
    )


def ask(question: str, k: int = DEFAULT_K, max_distance: float = MAX_DISTANCE) -> dict:
    """End-to-end: retrieve, filter, generate, attach sources.

    Returns {"answer", "sources", "chunks", "refused"}. app.py renders this.
    """
    retrieved = retrieve(question, k)
    results = [r for r in retrieved if r["distance"] <= max_distance]
    dropped = len(retrieved) - len(results)

    if not results:
        # Nothing in the corpus is close enough. Refuse in Python rather than
        # asking the model to refuse — it can't hallucinate its way past this.
        best = f" (closest review was {retrieved[0]['distance']:.3f} away)" if retrieved else ""
        return {
            "answer": f"{REFUSAL} None of the student reviews in this collection cover it{best}.",
            "sources": [],
            "chunks": [],
            "refused": True,
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(question, results)},
    ]
    client = _client()
    last_error: Exception | None = None
    for model in [MODEL, *FALLBACK_MODELS]:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,  # low: this is summarization of given text, not invention
                max_tokens=700,
            )
            break
        except NotFoundError as error:  # model retired or not on this key
            print(f"  ({model} unavailable, trying the next one)", file=sys.stderr)
            last_error = error
    else:
        raise SystemExit(f"No usable Groq model. Last error: {last_error}")

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": [source_label(r) for r in results],
        "chunks": results,
        "refused": answer.startswith(REFUSAL),
        "dropped_low_relevance": dropped,
    }


def print_answer(question: str, result: dict) -> None:
    print("=" * 78)
    print(f"Q: {question}")
    print("-" * 78)
    print(textwrap.fill(result["answer"], 78, replace_whitespace=False))
    if result["sources"]:
        print("\nRetrieved from:")
        for i, source in enumerate(result["sources"], 1):
            print(f"  [S{i}] {source}")
        distances = ", ".join(f"{c['distance']:.3f}" for c in result["chunks"])
        print(f"  distances: {distances}")
    if result.get("dropped_low_relevance"):
        print(f"  ({result['dropped_low_relevance']} retrieved chunk(s) dropped above distance {MAX_DISTANCE})")
    print()


TEST_QUESTIONS = [
    "What do students say about the difficulty of Jiang Li's exams?",
    "What is the workload like for CSCI 201 with Jiang Li?",
    "Which professors give useful feedback on assignments or projects?",
    "What do students say about Gloria Washington's teaching style in CSCI 135?",
    "How do Jiang Li and Jeremy Blackstone compare on workload and exam difficulty?",
]
OUT_OF_SCOPE = "What are the best dining halls on Howard's campus and what are the wait times at lunch?"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a grounded question (Milestone 5).")
    parser.add_argument("question", nargs="?", help="the question to ask")
    parser.add_argument("-k", type=int, default=DEFAULT_K)
    parser.add_argument("--test", action="store_true", help="run the 5 evaluation questions + 1 out of scope")
    args = parser.parse_args()

    if args.test:
        for question in TEST_QUESTIONS + [OUT_OF_SCOPE]:
            print_answer(question, ask(question, args.k))
        return

    if not args.question:
        parser.print_help()
        sys.exit(1)

    print_answer(args.question, ask(args.question, args.k))


if __name__ == "__main__":
    main()
