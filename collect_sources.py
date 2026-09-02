"""
Milestone 3 — source collection.

RateMyProfessors renders its review cards client-side: the server HTML carries
only the professor summary (overall quality, difficulty, % would take again),
so a plain HTTP fetch returns no review text. This script drives a real Chrome
window with Playwright, expands every "Load More Ratings" button, and writes
each professor's reviews into documents/ in the header format ingest.py reads.

    python collect_sources.py                  # all sources in SOURCES
    python collect_sources.py --only jiang-li  # just one
    python collect_sources.py --headed         # watch it work

It requests one page at a time with a pause between pages. Re-running overwrites
the file for each source it collects.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

DOCS_DIR = Path("documents")
PAGE_PAUSE_SECONDS = 2.0

# (filename stem, display name, url)
SOURCES = [
    ("rmp_jeremy-blackstone", "Jeremy Blackstone", "https://www.ratemyprofessors.com/professor/2640220"),
    ("rmp_anamika-rupa", "Anamika Rupa", "https://www.ratemyprofessors.com/professor/2976470"),
    ("rmp_noha-hazzazi", "Noha Hazzazi", "https://www.ratemyprofessors.com/professor/2418869"),
    ("rmp_saurav-aryal", "Saurav Aryal", "https://www.ratemyprofessors.com/professor/2672438"),
    ("rmp_alex-krentsel", "Alex Krentsel", "https://www.ratemyprofessors.com/professor/2725790"),
    ("rmp_jiang-li", "Jiang Li", "https://www.ratemyprofessors.com/professor/2323879"),
    ("rmp_gloria-washington", "Gloria Washington", "https://www.ratemyprofessors.com/professor/2084505"),
    ("rmp_moses-garuba", "Moses Garuba", "https://www.ratemyprofessors.com/professor/287385"),
    ("rmp_anil-jain", "Anil Jain", "https://www.ratemyprofessors.com/professor/548120"),
    ("rmp_linwei-niu", "Linwei Niu", "https://www.ratemyprofessors.com/professor/2719629"),
    ("rmp_danny-harris", "Danny Harris", "https://www.ratemyprofessors.com/professor/956152"),
    ("rmp_nicki-washington", "A. Nicki Washington", "https://www.ratemyprofessors.com/professor/997067"),
]

# Not collected:
#   - coursicle.com/howard/courses/CSCI blocks automated browsers outright
#     ("You don't smell human..."), headless or not. Save it by hand if you want it.
#   - ratemyprofessors.com/school/421 is campus-level review (food, dorms, safety),
#     which is off-domain for a CS professor system and would add retrieval noise.

CARD_SELECTOR = "div[class*='Rating__StyledRating']"
COMMENT_SELECTOR = "div[class*='Comments__StyledComments']"
COURSE_SELECTOR = "div[class*='RatingHeader__StyledClass']"
DATE_SELECTOR = "div[class*='TimeStamp__StyledTimeStamp']"
NUMBER_SELECTOR = "div[class*='CardNumRating__CardNumRatingNumber']"
META_SELECTOR = "div[class*='MetaItem__StyledMetaItem']"
TAG_SELECTOR = "span[class*='Tag-']"
LOAD_MORE = "button:has-text('Load More Ratings')"

COURSE_CODE_RE = re.compile(r"([A-Z]{2,4})\s*-?\s*(\d{3}[A-Z]?)")


def dismiss_banners(page) -> None:
    """Close the cookie banner and any modal that blocks the Load More button."""
    for selector in ("#onetrust-accept-btn-handler", "button:has-text('Accept')", "button:has-text('Close')"):
        try:
            page.click(selector, timeout=2000)
        except Exception:
            pass


def expand_all_ratings(page, limit: int = 40) -> int:
    """Click 'Load More Ratings' until every review is on the page."""
    clicks = 0
    while clicks < limit:
        try:
            button = page.query_selector(LOAD_MORE)
            if not button or not button.is_visible():
                break
            button.scroll_into_view_if_needed()
            button.click()
            clicks += 1
            page.wait_for_timeout(1200)
        except Exception:
            break
    return clicks


def text_of(element, selector: str) -> str | None:
    node = element.query_selector(selector)
    if not node:
        return None
    value = node.inner_text().strip()
    return value or None


def parse_card(card) -> str | None:
    """Turn one rendered review card into the plain-text block ingest.py chunks."""
    comment = text_of(card, COMMENT_SELECTOR)
    if not comment:
        return None  # a rating with no written review carries no opinion to retrieve

    numbers = [n.inner_text().strip() for n in card.query_selector_all(NUMBER_SELECTOR)]
    quality, difficulty = (numbers + [None, None])[:2]

    lines: list[str] = []
    if quality:
        lines.append(f"Quality: {quality}")
    if difficulty:
        lines.append(f"Difficulty: {difficulty}")

    course = text_of(card, COURSE_SELECTOR)
    if course:
        # "CSCI-100" -> "CSCI 100", the form the course regex in ingest.py reads.
        # Keep this out of the f-string: {3,4} in an f-string is a format field.
        normalized = COURSE_CODE_RE.sub(r"\1 \2", course)
        lines.append(f"Course: {normalized}")

    date = text_of(card, DATE_SELECTOR)
    if date:
        lines.append(f"Date: {date}")

    for meta in card.query_selector_all(META_SELECTOR):
        value = re.sub(r"\s+", " ", meta.inner_text().strip())
        if value and ":" in value:
            lines.append(value)

    lines.append(comment)

    tags = [t.inner_text().strip().title() for t in card.query_selector_all(TAG_SELECTOR)]
    if tags:
        lines.append("Tags: " + ", ".join(dict.fromkeys(tags)))

    return "\n".join(lines)


def collect_professor(page, stem: str, name: str, url: str) -> int:
    print(f"\n{name} — {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)
    dismiss_banners(page)

    clicks = expand_all_ratings(page)
    page.wait_for_timeout(800)

    cards = page.query_selector_all(CARD_SELECTOR)
    blocks = [block for block in (parse_card(c) for c in cards) if block]
    print(f"  expanded {clicks}x, {len(cards)} cards on page, {len(blocks)} with written reviews")

    if not blocks:
        print("  ! nothing captured — leaving the existing file alone", file=sys.stderr)
        return 0

    header = (
        f"SOURCE: {url}\n"
        f"PROFESSOR: {name}\n"
        "DEPARTMENT: Computer Science\n"
        "SCHOOL: Howard University\n"
        "---\n"
    )
    (DOCS_DIR / f"{stem}.txt").write_text(header + "\n\n".join(blocks) + "\n", encoding="utf-8")
    return len(blocks)




def main() -> None:
    parser = argparse.ArgumentParser(description="Collect review text into documents/ (Milestone 3).")
    parser.add_argument("--only", help="substring of a source stem, e.g. jiang-li")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    args = parser.parse_args()

    targets = [s for s in SOURCES if not args.only or args.only in s[0]]
    if not targets:
        raise SystemExit(f"No source matching {args.only!r}")

    DOCS_DIR.mkdir(exist_ok=True)
    total = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=not args.headed)
        page = browser.new_page(viewport={"width": 1280, "height": 2400})
        try:
            for stem, name, url in targets:
                total += collect_professor(page, stem, name, url)
                time.sleep(PAGE_PAUSE_SECONDS)
        finally:
            browser.close()

    print(f"\nCollected {total} written reviews into {DOCS_DIR}/")
    print("Next: python ingest.py --inspect   then   python ingest.py --random 5 --update-readme")


if __name__ == "__main__":
    main()
