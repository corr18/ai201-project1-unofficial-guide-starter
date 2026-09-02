"""
Milestone 4 — Embedding and retrieval.

Stages 3 and 4 of the pipeline in planning.md:

    chunks.json -> all-MiniLM-L6-v2 -> ChromaDB -> retrieve(query, k=5)

From the Retrieval Approach section of planning.md:
    - Embedding model: all-MiniLM-L6-v2 via sentence-transformers (local, no API
      key, 384-dimensional vectors)
    - Top-k: 5 reviews per query — enough perspectives to answer without
      dragging in loosely related material

The collection is created with `hnsw:space = cosine`. Chroma's default is
squared L2, which on these vectors produces distances in the 0-2 range that
aren't comparable to the 0-1 scale the milestone checkpoint uses. Cosine
distance is 1 - cosine similarity: 0.0 is identical, 1.0 is unrelated.

Usage:
    python embed.py --rebuild              # embed chunks.json into ChromaDB
    python embed.py --test                 # run the planning.md evaluation queries
    python embed.py --query "..." -k 5     # one ad-hoc query
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("chunks.json")
CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "howard_cs_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_K = 5

# Distance bands for reading results, from the Milestone 4 checkpoint.
GOOD_DISTANCE = 0.5
WEAK_DISTANCE = 0.7

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load MiniLM once and reuse it — it costs a few seconds to initialize."""
    global _model
    if _model is None:
        print(f"Loading {MODEL_NAME} ...", file=sys.stderr)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection(reset: bool = False):
    """Open (or recreate) the persistent Chroma collection.

    PersistentClient writes to chroma_db/ on disk, so the index survives between
    runs — app.py opens the same collection without re-embedding anything.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # nothing to delete on a first run
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


KEY_VALUE_RE = re.compile(r"^[A-Za-z][A-Za-z /]{2,20}:\s")


def embedding_text(chunk: dict) -> str:
    """What actually gets embedded — not the same as what gets stored.

    A raw review card is mostly form fields ("For Credit: Yes", "Textbook: N/A",
    a date, a letter grade). Those words are identical across all 129 reviews, so
    they add no signal and crowd out the sentence that does. Worse, the
    professor's name appears nowhere in the card text — it lives in the file
    header — so "workload for CSCI 201 with Jiang Li" had nothing to match on
    and returned Gloria Washington reviews at distance 0.53.

    So the embedded text is a written-out context sentence (professor, course,
    ratings) followed by the student's actual comment and tags. The full card is
    still what gets STORED and shown, so citation and generation are unaffected.
    """
    lines = chunk["text"].splitlines()
    comment = " ".join(line for line in lines if line and not KEY_VALUE_RE.match(line))
    tags = next((line[len("Tags:"):].strip() for line in lines if line.startswith("Tags:")), "")

    professor = chunk.get("professor") or "an unnamed professor"
    context = f"Student review of Professor {professor}"
    if chunk.get("course"):
        context += f" for the course {chunk['course']}"
    context += " in the Computer Science department at Howard University."

    if chunk.get("quality") is not None:
        context += f" The student rated quality {chunk['quality']} out of 5"
        if chunk.get("difficulty") is not None:
            context += f" and difficulty {chunk['difficulty']} out of 5"
        context += "."
    if chunk.get("would_take_again"):
        context += f" Would take this professor again: {chunk['would_take_again']}."

    parts = [context, comment]
    if tags:
        parts.append(f"Other students tagged this professor: {tags}.")
    return " ".join(part for part in parts if part)


def chunk_metadata(chunk: dict, position: int) -> dict:
    """Metadata stored alongside each vector.

    source_file and position are the attribution the milestone requires; the
    rest lets generation cite ratings and lets me filter by professor later.
    Chroma rejects None, so empty fields are dropped rather than stored as null.
    """
    fields = {
        "source_file": chunk["source_file"],
        "position": position,
        "professor": chunk.get("professor"),
        "course": chunk.get("course"),
        "source_url": chunk.get("source"),
        "quality": chunk.get("quality"),
        "difficulty": chunk.get("difficulty"),
        "would_take_again": chunk.get("would_take_again"),
        "grade": chunk.get("grade"),
        "date": chunk.get("date"),
        "token_estimate": chunk.get("token_estimate"),
    }
    return {key: value for key, value in fields.items() if value is not None}


def build_index(chunks_path: Path = CHUNKS_PATH) -> int:
    """Stage 3: embed every chunk and load it into ChromaDB."""
    if not chunks_path.exists():
        raise SystemExit(f"{chunks_path} not found — run `python ingest.py` first.")

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    if not chunks:
        raise SystemExit(f"{chunks_path} is empty.")

    print(f"Embedding {len(chunks)} chunks with {MODEL_NAME} ...")
    model = get_model()
    embeddings = model.encode(
        [embedding_text(c) for c in chunks],
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    # position = this chunk's index within its own source document
    seen: dict[str, int] = {}
    metadatas = []
    for chunk in chunks:
        position = seen.get(chunk["source_file"], 0)
        seen[chunk["source_file"]] = position + 1
        metadatas.append(chunk_metadata(chunk, position))

    collection = get_collection(reset=True)
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} vectors in {CHROMA_PATH}/ (collection: {COLLECTION_NAME})")
    return collection.count()


def known_professors(collection) -> list[str]:
    """Every professor name in the store, for detecting who a question is about."""
    metadatas = collection.get(include=["metadatas"])["metadatas"]
    return sorted({m["professor"] for m in metadatas if m.get("professor")})


def professors_named_in(query: str, professors: list[str]) -> list[str]:
    """Which known professors does this question name?

    Full name always counts. A surname counts only when it belongs to exactly one
    professor — "Washington" is ambiguous here (Gloria Washington and A. Nicki
    Washington), so a bare "Washington" is deliberately not treated as a match.
    """
    lowered = query.lower()
    surnames: dict[str, list[str]] = {}
    for professor in professors:
        surnames.setdefault(professor.split()[-1].lower(), []).append(professor)

    found = []
    for professor in professors:
        surname = professor.split()[-1].lower()
        full_hit = professor.lower() in lowered
        surname_hit = (
            len(surnames[surname]) == 1
            and re.search(rf"\b{re.escape(surname)}\b", lowered) is not None
        )
        if full_hit or surname_hit:
            found.append(professor)
    return found


def _query_collection(collection, embedding, k: int, where: dict | None = None) -> list[dict]:
    response = collection.query(
        query_embeddings=embedding,
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": cid, "text": text, "metadata": meta, "distance": dist}
        for cid, text, meta, dist in zip(
            response["ids"][0], response["documents"][0], response["metadatas"][0], response["distances"][0]
        )
    ]


def retrieve(query: str, k: int = DEFAULT_K, balance: bool = True) -> list[dict]:
    """Stage 4: return the k reviews closest to the question.

    Plain similarity search, with one adjustment: when a question names two or
    more professors ("How do Jiang Li and Jeremy Blackstone compare?"), a single
    top-k is dominated by whichever professor has more reviews — all five results
    came back Jiang Li, so the model had nothing to compare against. In that case
    the search runs once per named professor with a metadata filter and the
    results are merged, guaranteeing both sides are represented.

    Pass balance=False for unmodified top-k.
    """
    collection = get_collection()
    if collection.count() == 0:
        raise SystemExit("The collection is empty — run `python embed.py --rebuild` first.")

    embedding = get_model().encode([query], normalize_embeddings=True).tolist()

    if balance:
        named = professors_named_in(query, known_professors(collection))
        if len(named) >= 2:
            per_professor = max(1, -(-k // len(named)))  # ceil, so the merge can still fill k
            merged: list[dict] = []
            for professor in named:
                merged.extend(
                    _query_collection(collection, embedding, per_professor, {"professor": professor})
                )
            merged.sort(key=lambda r: r["distance"])
            return merged[:k]

    return _query_collection(collection, embedding, k)


def format_result(result: dict, index: int, full_text: bool = True) -> str:
    meta = result["metadata"]
    distance = result["distance"]
    flag = "" if distance < GOOD_DISTANCE else ("  <- weak" if distance < WEAK_DISTANCE else "  <- POOR")
    header = (
        f"  {index}. distance {distance:.3f}{flag}\n"
        f"     {meta.get('professor', '?')} | {meta.get('course', 'course not stated')} | "
        f"quality {meta.get('quality', '?')} | difficulty {meta.get('difficulty', '?')}\n"
        f"     {meta['source_file']} (chunk {meta['position']}) — {meta.get('source_url', '?')}"
    )
    if not full_text:
        return header
    body = "\n".join(f"     | {line}" for line in result["text"].splitlines())
    return f"{header}\n{body}"


def run_query(query: str, k: int = DEFAULT_K, full_text: bool = True) -> list[dict]:
    results = retrieve(query, k)
    print(f'\nQ: "{query}"')
    for i, result in enumerate(results, 1):
        print(format_result(result, i, full_text))
    best = results[0]["distance"]
    verdict = "good" if best < GOOD_DISTANCE else ("weak" if best < WEAK_DISTANCE else "FAILING")
    print(f"  best distance {best:.3f} ({verdict})")
    return results


# The evaluation questions from planning.md, instantiated with professors and
# courses that actually appear in the corpus.
TEST_QUERIES = [
    "What do students say about the difficulty of Jiang Li's exams?",
    "What is the workload like for CSCI 201 with Jiang Li?",
    "Which professors give useful feedback on assignments or projects?",
    "What do students say about Gloria Washington's teaching style in CSCI 135?",
    "How do Jiang Li and Jeremy Blackstone compare on workload and exam difficulty?",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunks and query the vector store (Milestone 4).")
    parser.add_argument("--rebuild", action="store_true", help="re-embed chunks.json from scratch")
    parser.add_argument("--test", action="store_true", help="run the planning.md evaluation queries")
    parser.add_argument("--query", help="run a single query")
    parser.add_argument("-k", type=int, default=DEFAULT_K, help=f"chunks to retrieve (default {DEFAULT_K})")
    parser.add_argument("--brief", action="store_true", help="headers only, no review text")
    args = parser.parse_args()

    if args.rebuild:
        build_index()

    if args.query:
        run_query(args.query, args.k, not args.brief)

    if args.test:
        for query in TEST_QUERIES:
            run_query(query, args.k, not args.brief)

    if not (args.rebuild or args.query or args.test):
        parser.print_help()


if __name__ == "__main__":
    main()
