"""
Milestone 3 — Document ingestion and chunking.

Implements stages 1 and 2 of the pipeline in planning.md:

    1. DOCUMENT INGESTION -> 2. CHUNKING -> (3. embedding, handled in embed.py)

Pipeline order, matching the milestone instructions:

    documents/        your saved source pages (.txt, .md, .html, .pdf)
      |  load
    raw_text/         every source normalized to plain .txt, BEFORE cleaning
      |  clean        (drop nav, cookie banners, footers, HTML entities)
      |  chunk        one review card per chunk, 100-250 tokens, overlap 0
    chunks.json       what embed.py reads next

Chunking strategy from planning.md:
    - One complete RateMyProfessors review card per chunk (typically 100-250 tokens)
    - Overlap = 0, because each review is already self-contained; splitting or
      overlapping reviews would blur one student's experience into another's
    - Every chunk carries professor, course, and source URL so the generation
      stage can cite where each claim came from

Usage:
    python ingest.py                       # documents/ -> raw_text/ + chunks.json
    python ingest.py --inspect             # print one full cleaned document and stop
    python ingest.py --sample 5            # print 5 representative chunks
    python ingest.py --update-readme       # write those 5 chunks + the count into README.md

Input file conventions (documents/):
    Put an optional header at the top of a text file so its chunks inherit the
    metadata:

        SOURCE: https://www.ratemyprofessors.com/professor/2640220
        PROFESSOR: Jane Doe
        COURSE: CSCI 135
        ---
        <paste the review cards here, one review per block>

    Reviews are separated by a blank line or by a --- / === separator line.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import statistics
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# --- Chunk size guardrails, from the Chunking Strategy section of planning.md ---
TARGET_MIN_TOKENS = 100
TARGET_MAX_TOKENS = 250
# A block smaller than this isn't a review — it's a stray rating line or tag row
# that belongs to the review next to it.
FRAGMENT_TOKENS = 40
# Hard ceiling. A single review should never exceed this; if one does, it gets
# split at a sentence boundary with NO overlap (overlap = 0 per the spec).
HARD_MAX_TOKENS = 350

# Corpus-level sanity check from the milestone instructions.
MIN_HEALTHY_CORPUS = 50
MAX_HEALTHY_CORPUS = 2000

SUPPORTED_SUFFIXES = {".txt", ".md", ".html", ".htm", ".pdf"}

# Navigation / chrome that comes along when you save a RateMyProfessors or
# Coursicle page. These lines carry no student opinion, so they're dropped
# before chunking to keep chunks clean.
BOILERPLATE_PATTERNS = [
    r"^rate my professors?$",
    r"^ratemyprofessors\.com$",
    r"^coursicle$",
    r"^log ?in$",
    r"^sign ?up$",
    r"^help$",
    r"^about( us)?$",
    r"^menu$",
    r"^search$",
    r"^professors?$",
    r"^schools?$",
    r"^cookie[s]? (policy|preferences|settings)",
    r"^(we use|this site uses) cookies",
    r"^accept (all )?cookies$",
    r"^privacy policy$",
    r"^terms of (use|service)$",
    r"^copyright \d{4}",
    r"^©",
    r"^rate (this )?professor",
    r"^compare$",
    r"^jump to ratings$",
    r"^i'?m professor",
    r"^i'?d rather not say$",
    r"^submit a correction$",
    r"^report (this )?rating$",
    r"^(thumbs up|thumbs down|helpful|not helpful)$",
    r"^share$",
    r"^read more$",
    r"^show more$",
    r"^load more ratings$",
    r"^\d+ (ratings?|comments?|replies)$",
    r"^all courses?$",
    r"^similar professors$",
    r"^advertisement$",
    r"^ad$",
    r"^skip to (main )?content$",
    r"^>>> paste",  # the placeholder line in a fresh documents/ stub file
    r"^follow us",
    r"^download the app",
    r"^app store$",
    r"^google play$",
]
BOILERPLATE_RE = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)

# Leftovers that mean cleaning didn't finish. Checked after chunking so you get
# told to clean further instead of embedding junk.
ARTIFACT_CHECKS = [
    (re.compile(r"<[a-zA-Z/][^>\n]{0,80}>"), "HTML tags"),
    (re.compile(r"&(?:amp|nbsp|quot|lt|gt|#x?\d*[0-9a-fA-F]+);"), "HTML entities"),
    (re.compile(r"\b(?:class|href|src|style)="), "HTML attributes"),
    (re.compile(r"(?im)^(?:log ?in|sign ?up|helpful|share|read more)$"), "leftover nav text"),
    (re.compile(r"(?i)cookie"), "cookie banner text"),
]

# --- Metadata patterns -------------------------------------------------------
COURSE_RE = re.compile(r"\b([A-Z]{2,4})\s*-?\s*(\d{3})\b")
QUALITY_RE = re.compile(r"quality[:\s]*([0-5](?:\.\d)?)", re.IGNORECASE)
DIFFICULTY_RE = re.compile(r"difficult(?:y|ies)?[:\s]*([0-5](?:\.\d)?)", re.IGNORECASE)
TAKE_AGAIN_RE = re.compile(r"would take again[:\s]*(yes|no)", re.IGNORECASE)
GRADE_RE = re.compile(r"grade(?: received)?[:\s]*([A-F][+-]?|Not sure yet|Audit(?:/No Grade)?)", re.IGNORECASE)
DATE_RE = re.compile(
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
    r"|\d{1,2}/\d{1,2}/\d{2,4})\b"
)
URL_RE = re.compile(r"https?://\S+|(?:www\.)?ratemyprofessors\.com/\S+|(?:www\.)?coursicle\.com/\S+")
# "CSCI201" / "CSCI-201" -> "CSCI 201", so a question that spaces the course code
# the normal way matches the review that didn't.
COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4})\s*-?\s*(\d{3}[A-Z]?)\b")
SEPARATOR_RE = re.compile(r"^\s*(?:[-=*_]{3,}|#{1,6}\s.*)\s*$")
# A block that opens with its rating line is a complete card, however short the
# student's comment is. "Excellent" is a whole review, not a fragment.
CARD_START_RE = re.compile(r"^\s*Quality:\s*[0-5]", re.IGNORECASE)


@dataclass
class Document:
    """One source file from documents/, with its text before and after cleaning."""

    path: Path
    raw: str  # normalized plain text, saved to raw_text/ before any cleaning
    text: str  # cleaned text, what actually gets chunked
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """One complete review card, ready to embed."""

    id: str
    text: str
    professor: str | None
    course: str | None
    source: str | None
    quality: float | None
    difficulty: float | None
    would_take_again: str | None
    grade: str | None
    date: str | None
    source_file: str
    token_estimate: int
    char_count: int


# ---------------------------------------------------------------------------
# Stage 1: Document ingestion
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Rough token count (~1.3 tokens per whitespace word).

    Good enough to police the 100-250 token target from planning.md without
    loading a tokenizer. embed.py uses the real all-MiniLM-L6-v2 tokenizer.
    """
    words = len(text.split())
    return max(1, round(words * 1.3))


def strip_html(raw: str) -> str:
    """Turn a saved RateMyProfessors/Coursicle page into plain text."""
    raw = re.sub(r"(?is)<(script|style|noscript|svg|head|nav|header|footer|form)\b.*?</\1>", " ", raw)
    # Keep block boundaries so separate review cards stay separate.
    raw = re.sub(r"(?i)</(p|div|li|tr|section|article|h[1-6])>", "\n\n", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?s)<!--.*?-->", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    # Unescape twice: saved pages often contain double-encoded entities
    # (&amp;#39; -> &#39; -> ').
    return html.unescape(html.unescape(raw))


def read_pdf(path: Path) -> str:
    try:
        import pdfplumber  # optional, only needed if documents/ has PDFs
    except ImportError:
        print(
            f"  ! skipping {path.name}: uncomment pdfplumber in requirements.txt to read PDFs",
            file=sys.stderr,
        )
        return ""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def parse_header(text: str) -> tuple[dict, str]:
    """Pull `KEY: value` lines off the top of a file, before the first `---`.

    Returns (metadata, remaining_body). Files without a header are unaffected.
    """
    metadata: dict = {}
    lines = text.splitlines()
    consumed = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            consumed = i + 1
            continue
        if SEPARATOR_RE.match(stripped):
            consumed = i + 1
            break
        # A key with no value is allowed (e.g. `PROFESSOR:` on a school page).
        match = re.match(r"^([A-Za-z_ ]{3,20}):\s*(.*)$", stripped)
        key = match.group(1).strip().lower().replace(" ", "_") if match else None
        if key not in {"source", "url", "professor", "course", "department", "school"}:
            # Not front matter. Return the body from here, keeping any keys
            # already parsed so their lines don't leak into the chunks.
            return metadata, "\n".join(lines[i:]) if metadata else text
        value = match.group(2).strip()
        if value:
            metadata["source" if key == "url" else key] = value
        consumed = i + 1
    return metadata, "\n".join(lines[consumed:])


def normalize_whitespace(raw: str) -> str:
    """Consistent plain-text form: real spaces, no zero-width junk, LF newlines."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    raw = re.sub(r"[\u200b-\u200d\ufeff]", "", raw)  # zero-width junk from copy/paste
    raw = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in raw.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def clean_text(raw: str) -> str:
    """Drop page chrome line by line, preserving the blank lines between cards."""
    kept = []
    for line in raw.split("\n"):
        if line and BOILERPLATE_RE.match(line):
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return COURSE_CODE_RE.sub(r"\1 \2", text).strip()


def professor_from_filename(path: Path) -> str | None:
    """`rmp_legand-burge.txt` -> `Legand Burge`. Fallback when no header."""
    stem = re.sub(r"^(rmp|ratemyprofessors|coursicle|reviews?)[_\-]*", "", path.stem, flags=re.IGNORECASE)
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    if not stem or stem.isdigit():
        return None
    return stem.title()


def load_documents(docs_dir: Path) -> list[Document]:
    """Stage 1: read every supported file in documents/, normalize, then clean."""
    if not docs_dir.is_dir():
        raise SystemExit(f"No such directory: {docs_dir}")

    documents: list[Document] = []
    files = sorted(p for p in docs_dir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)

    if not files:
        raise SystemExit(
            f"No documents found in {docs_dir}/.\n"
            "Save your 10 sources there as .txt, .md, .html, or .pdf first "
            "(see the Documents table in planning.md)."
        )

    for path in files:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            raw = read_pdf(path)
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
            # Strip markup from .html files, and from .txt/.md pastes that
            # dragged tags along with them from the page.
            if suffix in {".html", ".htm"} or re.search(r"<[a-zA-Z/][^>\n]{0,80}>", raw):
                raw = strip_html(raw)

        metadata, body = parse_header(raw)
        raw_text = normalize_whitespace(body)
        cleaned = clean_text(raw_text)
        if not cleaned:
            print(f"  ! {path.name} is empty after cleaning — skipped", file=sys.stderr)
            continue

        metadata.setdefault("professor", professor_from_filename(path))
        if "source" not in metadata:
            found = URL_RE.search(raw)
            metadata["source"] = found.group(0).rstrip(".,)") if found else path.name

        documents.append(Document(path=path, raw=raw_text, text=cleaned, metadata=metadata))

    return documents


def save_raw(documents: list[Document], raw_dir: Path) -> None:
    """Persist every source as plain .txt BEFORE cleaning, in one shared format.

    This is the checkpoint to diff against when a chunk looks wrong: it shows
    what the page actually said versus what cleaning removed.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    for document in documents:
        header = "\n".join(
            f"{key.upper()}: {value}" for key, value in document.metadata.items() if value
        )
        out = raw_dir / f"{document.path.stem}.txt"
        out.write_text(f"{header}\n---\n{document.raw}\n", encoding="utf-8")
    print(f"Saved {len(documents)} raw text files to {raw_dir}/")


# ---------------------------------------------------------------------------
# Stage 2: Chunking — one review card per chunk, overlap 0
# ---------------------------------------------------------------------------


def split_into_blocks(text: str) -> list[str]:
    """Split a cleaned document on review-card boundaries.

    Prefers explicit separator lines (--- / === / ***) when the file uses them,
    otherwise falls back to blank-line separated blocks, which is how review
    cards land when you copy them off the page.
    """
    if any(SEPARATOR_RE.match(line) for line in text.splitlines()):
        blocks = re.split(r"(?m)^\s*[-=*_]{3,}\s*$", text)
    else:
        blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


def merge_fragments(blocks: list[str]) -> list[str]:
    """Re-attach stray rating/tag lines to the review card they belong to.

    On a RateMyProfessors card the numbers ("Quality 4.0", the course code, the
    date) sit above the student's comment, so a too-small block is joined to the
    block that FOLLOWS it. A trailing fragment (tags, "Would Take Again: Yes")
    joins the block before it. This is what keeps one card in one chunk, and
    what prevents the "Professor Smith's exams are heavily" fragment problem.
    """
    merged: list[str] = []
    pending: list[str] = []

    for block in blocks:
        if estimate_tokens(block) < FRAGMENT_TOKENS and not CARD_START_RE.match(block):
            pending.append(block)
            continue
        merged.append("\n".join(pending + [block]))
        pending = []

    if pending:
        tail = "\n".join(pending)
        if merged:
            merged[-1] = merged[-1] + "\n" + tail
        else:
            merged.append(tail)

    return merged


def split_oversized(block: str) -> list[str]:
    """Last resort for a block above HARD_MAX_TOKENS.

    Splits at sentence boundaries with ZERO overlap, per the spec. Usually this
    firing means two review cards weren't separated by a blank line in the
    source file — the run summary flags it so you can fix the file.
    """
    if estimate_tokens(block) <= HARD_MAX_TOKENS:
        return [block]

    sentences = re.split(r"(?<=[.!?])\s+", block)
    parts: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = current + [sentence]
        if current and estimate_tokens(" ".join(candidate)) > TARGET_MAX_TOKENS:
            parts.append(" ".join(current))
            current = [sentence]  # overlap = 0: no sentence is carried forward
        else:
            current = candidate
    if current:
        parts.append(" ".join(current))
    return parts


def extract_metadata(block: str, doc_metadata: dict) -> dict:
    """Read per-review metadata off the card, falling back to the file header."""
    course_match = COURSE_RE.search(block)
    course = f"{course_match.group(1)} {course_match.group(2)}" if course_match else doc_metadata.get("course")

    def _num(pattern: re.Pattern) -> float | None:
        match = pattern.search(block)
        return float(match.group(1)) if match else None

    def _text(pattern: re.Pattern) -> str | None:
        match = pattern.search(block)
        return match.group(1).strip() if match else None

    return {
        "professor": doc_metadata.get("professor"),
        "course": course,
        "source": doc_metadata.get("source"),
        "quality": _num(QUALITY_RE),
        "difficulty": _num(DIFFICULTY_RE),
        "would_take_again": (_text(TAKE_AGAIN_RE) or "").capitalize() or None,
        "grade": _text(GRADE_RE),
        "date": _text(DATE_RE),
    }


def chunk_document(document: Document) -> list[Chunk]:
    """Stage 2 for a single file: cleaned text -> list of review chunks."""
    blocks = merge_fragments(split_into_blocks(document.text))

    chunks: list[Chunk] = []
    for block in blocks:
        for part in split_oversized(block):
            text = part.strip()
            if not text:
                continue
            metadata = extract_metadata(text, document.metadata)
            chunks.append(
                Chunk(
                    id=f"{document.path.stem}::{len(chunks):03d}",
                    text=text,
                    source_file=document.path.name,
                    token_estimate=estimate_tokens(text),
                    char_count=len(text),
                    **metadata,
                )
            )
    return chunks


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        doc_chunks = chunk_document(document)
        print(f"  {document.path.name}: {len(doc_chunks)} chunks")
        chunks.extend(doc_chunks)
    return chunks


# ---------------------------------------------------------------------------
# Inspection — the checks the milestone asks you to do by eye
# ---------------------------------------------------------------------------


def find_artifacts(text: str) -> list[str]:
    """Name whatever cleaning missed in this text."""
    return [label for pattern, label in ARTIFACT_CHECKS if pattern.search(text)]


def inspect_document(documents: list[Document], which: str | None) -> None:
    """Print one full cleaned document so you can read it end to end."""
    document = documents[0]
    if which:
        matches = [d for d in documents if which.lower() in d.path.name.lower()]
        if not matches:
            raise SystemExit(f"No document matching {which!r}. Have: {[d.path.name for d in documents]}")
        document = matches[0]

    print("=" * 72)
    print(f"CLEANED DOCUMENT: {document.path.name}")
    print(f"source: {document.metadata.get('source')}")
    print(f"professor: {document.metadata.get('professor')}")
    print(f"{len(document.raw)} chars raw -> {len(document.text)} chars cleaned "
          f"({100 - 100 * len(document.text) // max(1, len(document.raw))}% removed)")
    print("=" * 72)
    print(document.text)
    print("=" * 72)

    artifacts = find_artifacts(document.text)
    if artifacts:
        print(f"! Still present after cleaning: {', '.join(artifacts)}")
        print("  Add a pattern to BOILERPLATE_PATTERNS (or fix the saved file) and re-run.")
    else:
        print("No HTML tags, entities, or known nav text detected. Read it anyway —")
        print("if anything above isn't a student's opinion, it shouldn't be in the corpus.")


def representative_chunks(chunks: list[Chunk], count: int) -> list[Chunk]:
    """Pick N chunks spread across the corpus, not N from the first file.

    Prefers chunks inside the target token range that carry a source URL, so the
    samples are the ones you'd actually want a grader to see.
    """
    good = [
        c for c in chunks
        if TARGET_MIN_TOKENS <= c.token_estimate <= TARGET_MAX_TOKENS and c.source and not find_artifacts(c.text)
    ]
    pool = good or chunks
    if len(pool) <= count:
        return pool
    # One from each of N evenly spaced positions, biased toward distinct files.
    picked: list[Chunk] = []
    seen_files: set[str] = set()
    step = len(pool) / count
    for i in range(count):
        start = int(i * step)
        for j in range(start, len(pool)):
            if pool[j].source_file not in seen_files and pool[j] not in picked:
                picked.append(pool[j])
                seen_files.add(pool[j].source_file)
                break
        else:
            for j in range(start, len(pool)):
                if pool[j] not in picked:
                    picked.append(pool[j])
                    break
    return picked[:count]


def random_chunks(chunks: list[Chunk], count: int, seed: int | None = None) -> list[Chunk]:
    """Pick N chunks at random — an unbiased look at what the chunker produced.

    Unlike representative_chunks(), this does NOT filter out short, dirty, or
    metadata-less chunks. That's the point: random sampling is how you find the
    fragments, HTML leftovers, and empty strings you'd otherwise embed blind.
    Pass a seed to reproduce the same draw when you re-run after a fix.
    """
    rng = random.Random(seed)
    return rng.sample(chunks, min(count, len(chunks)))


def diagnose(chunks: list[Chunk]) -> list[str]:
    """Map the sampled chunks onto the known chunker failure modes."""
    problems: list[str] = []

    empty = [c for c in chunks if not c.text.strip()]
    if empty:
        problems.append(
            f"{len(empty)} EMPTY chunks. The splitter is emitting zero-length strings — "
            "check that the source files actually loaded (compare against raw_text/)."
        )

    dirty = [c for c in chunks if find_artifacts(c.text)]
    if dirty:
        labels = sorted({label for c in dirty for label in find_artifacts(c.text)})
        problems.append(
            f"{len(dirty)} chunks contain {', '.join(labels)}. Cleaning missed them — "
            "diff the chunk against its file in raw_text/ and add a BOILERPLATE_PATTERNS entry."
        )

    fragments = [c for c in chunks if c.token_estimate < FRAGMENT_TOKENS]
    if fragments:
        problems.append(
            f"{len(fragments)} chunks under {FRAGMENT_TOKENS} tokens are fragments, not reviews — "
            "a card boundary was detected mid-review; check blank lines in that source file."
        )

    lengths = [c.token_estimate for c in chunks]
    if len(lengths) > 2 and statistics.pstdev(lengths) < 5:
        problems.append(
            "Every chunk is nearly the same length. That means the chunker is splitting "
            "mechanically instead of on review-card boundaries — check split_into_blocks()."
        )

    mismatched = [c for c in chunks if not c.id.startswith(Path(c.source_file).stem)]
    if mismatched:
        problems.append(
            f"{len(mismatched)} chunks have an id that doesn't match their source_file — "
            "metadata is being attached to the wrong document."
        )

    no_source = [c for c in chunks if not c.source or not URL_RE.match(c.source)]
    if no_source:
        problems.append(
            f"{len(no_source)} chunks fall back to a filename instead of a source URL, so "
            "generation can't cite them — add a `SOURCE:` header to those files."
        )

    return problems


def print_chunks(chunks: list[Chunk], label: str) -> None:
    print(f"\n{'=' * 72}\n{label}\n{'=' * 72}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} --- [{chunk.id}] from {chunk.source_file}")
        print(f"professor: {chunk.professor or '?'} | course: {chunk.course or '?'} | ~{chunk.token_estimate} tokens")
        print(f"source: {chunk.source}")
        artifacts = find_artifacts(chunk.text)
        if artifacts:
            print(f"! artifacts: {', '.join(artifacts)}")
        print(chunk.text)
    print("\nRead each one and ask: could someone answer a question from this chunk alone?")

    problems = diagnose(chunks)
    if problems:
        print("\n! Problems in this sample — fix these BEFORE embedding:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("No empty chunks, HTML artifacts, fragments, or metadata mismatches in this sample.")


def report(chunks: list[Chunk]) -> None:
    """The numbers the README's Chunking Strategy section asks for."""
    tokens = [c.token_estimate for c in chunks]
    in_range = [t for t in tokens if TARGET_MIN_TOKENS <= t <= TARGET_MAX_TOKENS]
    undersized = [c for c in chunks if c.token_estimate < TARGET_MIN_TOKENS]
    oversized = [c for c in chunks if c.token_estimate > TARGET_MAX_TOKENS]

    print("\n--- Chunk report ---")
    print(f"Total chunks:        {len(chunks)}")
    print(f"Tokens min/med/max:  {min(tokens)} / {round(statistics.median(tokens))} / {max(tokens)}")
    print(f"Within 100-250:      {len(in_range)}/{len(chunks)} ({100 * len(in_range) // len(chunks)}%)")
    print("Overlap:             0 tokens (one review per chunk)")

    missing_source = [c for c in chunks if not c.source]
    missing_prof = [c for c in chunks if not c.professor]
    dirty = [c for c in chunks if find_artifacts(c.text)]

    if missing_source:
        print(f"! {len(missing_source)} chunks have no source URL — add a `SOURCE:` header to those files")
    if missing_prof:
        print(f"! {len(missing_prof)} chunks have no professor — add a `PROFESSOR:` header to those files")
    if dirty:
        labels = sorted({label for c in dirty for label in find_artifacts(c.text)})
        print(f"! {len(dirty)} chunks still contain: {', '.join(labels)} — clean further before embedding")
    if undersized:
        print(f"! {len(undersized)} chunks under {TARGET_MIN_TOKENS} tokens (short reviews, or a card split too early)")
    if oversized:
        print(f"! {len(oversized)} chunks over {TARGET_MAX_TOKENS} tokens (two cards likely ran together)")

    if len(chunks) < MIN_HEALTHY_CORPUS:
        print(f"! Only {len(chunks)} chunks. Under {MIN_HEALTHY_CORPUS} across 10 documents usually means")
        print("  chunks are too coarse, or some pages were saved without their reviews expanded.")
    elif len(chunks) > MAX_HEALTHY_CORPUS:
        print(f"! {len(chunks)} chunks. Over {MAX_HEALTHY_CORPUS} usually means cards are being split apart —")
        print("  raise FRAGMENT_TOKENS so rating lines merge into their comment.")


# ---------------------------------------------------------------------------
# README writeback
# ---------------------------------------------------------------------------


def _cell(text: str) -> str:
    """Make chunk text safe for a markdown table cell."""
    return text.replace("|", "\\|").replace("\n", "<br>")


def update_readme(readme: Path, samples: list[Chunk], total: int) -> None:
    """Fill in the Sample Chunks table and the final chunk count."""
    if not readme.exists():
        raise SystemExit(f"{readme} not found")

    content = readme.read_text(encoding="utf-8")

    rows = "\n".join(
        f"| {i} | {c.source_file} | {_cell(c.text)} |" for i, c in enumerate(samples, 1)
    )
    table = "| # | Source document | Chunk text |\n|---|----------------|------------|\n" + rows

    pattern = re.compile(
        r"(## Sample Chunks\n(?:.*?\n)*?)\| # \| Source document \| Chunk text \|\n\|[-| ]+\|\n(?:\|.*\n)*",
        re.MULTILINE,
    )
    if not pattern.search(content):
        raise SystemExit("Could not find the Sample Chunks table in README.md — was it edited?")
    content = pattern.sub(lambda m: m.group(1) + table + "\n", content, count=1)

    content = re.sub(
        r"\*\*Final chunk count:\*\*.*",
        f"**Final chunk count:** {total}",
        content,
        count=1,
    )

    readme.write_text(content, encoding="utf-8")
    print(f"Wrote {len(samples)} sample chunks and a final count of {total} into {readme}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and chunk the review corpus (Milestone 3).")
    parser.add_argument("--docs-dir", type=Path, default=Path("documents"))
    parser.add_argument("--raw-dir", type=Path, default=Path("raw_text"))
    parser.add_argument("--out", type=Path, default=Path("chunks.json"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--inspect", nargs="?", const="", metavar="FILENAME",
                        help="print one full cleaned document and exit")
    parser.add_argument("--sample", type=int, default=0, metavar="N",
                        help="print N representative chunks from across the corpus")
    parser.add_argument("--random", type=int, default=0, metavar="N",
                        help="print N chunks chosen at random (unfiltered — use this to hunt for bad chunks)")
    parser.add_argument("--seed", type=int, default=None, help="seed for --random, so a draw is reproducible")
    parser.add_argument("--preview", type=int, default=0, metavar="N", help="print the first N chunks")
    parser.add_argument("--update-readme", action="store_true",
                        help="write the printed sample chunks and total count into README.md")
    args = parser.parse_args()

    print(f"Loading documents from {args.docs_dir}/ ...")
    documents = load_documents(args.docs_dir)
    print(f"Loaded {len(documents)} documents.")
    save_raw(documents, args.raw_dir)

    if args.inspect is not None:
        inspect_document(documents, args.inspect or None)
        return

    print("\nChunking ...")
    chunks = chunk_documents(documents)
    if not chunks:
        raise SystemExit("No chunks produced — check that your files contain review text.")

    args.out.write_text(
        json.dumps([asdict(c) for c in chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    report(chunks)
    print(f"\nWrote {len(chunks)} chunks to {args.out}")

    if args.preview:
        print_chunks(chunks[: args.preview], f"FIRST {args.preview} CHUNKS")

    if args.random:
        samples = random_chunks(chunks, args.random, args.seed)
        print_chunks(samples, f"{len(samples)} RANDOM CHUNKS" + (f" (seed {args.seed})" if args.seed else ""))
    else:
        samples = representative_chunks(chunks, args.sample or 5)
        if args.sample:
            print_chunks(samples, f"{len(samples)} REPRESENTATIVE CHUNKS")

    if args.update_readme:
        update_readme(args.readme, samples, len(chunks))


if __name__ == "__main__":
    main()
