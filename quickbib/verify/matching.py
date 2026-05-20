"""Text normalization and fuzzy similarity helpers for reference verification.

These functions are deterministic and dependency-free. They are used to
compare the metadata written in a BibTeX entry against the authoritative
record returned by CrossRef / arXiv, so the verifier can decide whether the
two describe the same publication.
"""

import html
import re
from difflib import SequenceMatcher

# A few LaTeX accent / escaped characters that commonly appear inside titles.
_ESCAPED = {
    r"\&": "&",
    r"\%": "%",
    r"\_": "_",
    r"\$": "$",
    r"\#": "#",
    r"\{": "{",
    r"\}": "}",
}


def strip_markup(text: str) -> str:
    """Remove LaTeX *and* XML/HTML markup so only plain words remain.

    CrossRef routinely returns titles with embedded JATS / MathML / HTML tags
    (``<mml:math>``, ``<jats:sub>`` ...). Together with LaTeX control sequences
    in BibTeX, that markup must be stripped before two titles can be compared.
    Tags are removed (their text content kept), entities are decoded, LaTeX
    control sequences are dropped, and braces are unwrapped.
    """
    if not text:
        return ""
    text = html.unescape(text)
    # Strip XML/HTML/JATS/MathML tags, keeping the text between them.
    text = re.sub(r"<[^>]+>", "", text)
    for src, dst in _ESCAPED.items():
        text = text.replace(src, dst)
    # Drop control sequences but leave the following text/argument in place.
    text = re.sub(r"\\[a-zA-Z]+\*?\s*", " ", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace("\\", " ")
    return text


# Backwards-compatible alias.
strip_latex = strip_markup


def clean(text: str) -> str:
    """Human-readable cleanup: strip LaTeX/XML markup and collapse whitespace."""
    return re.sub(r"\s+", " ", strip_markup(text or "")).strip()


def normalize(text: str) -> str:
    """Aggressive normalization for comparison.

    Lowercased, LaTeX stripped, reduced to ``a-z0-9`` words. Two strings that
    normalize to the same value describe, for our purposes, the same thing.
    """
    if not text:
        return ""
    text = strip_markup(text).lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contained(a: str, b: str) -> bool:
    """True when the shorter of two normalized titles sits inside the longer.

    Lets a main title match "main title: subtitle" (CrossRef often stores a
    book's main title without its subtitle). The shorter side must be a real
    title (>= 4 words), not a stray fragment, to avoid spurious matches.
    """
    short, long = sorted((a, b), key=len)
    if len(short.split()) < 4:
        return False
    return short in long


def similarity(a: str, b: str) -> float:
    """Return a 0.0-1.0 similarity score between two free-text strings.

    Designed to recognise the *same* publication despite encoding differences
    between sources (LaTeX vs MathML maths, missing subtitles, re-ordered
    words). Combines: a containment check (subtitles), a whitespace-insensitive
    character ratio (maths/markup encoding), a plain character ratio, and a
    word-set Jaccard score (re-ordering).
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if contained(na, nb):
        return 0.95
    # Whitespace-insensitive: "$ABC$" and "<mml:mi>A</mml:mi>B<...>C" both
    # collapse to "abc", so tokenisation differences stop mattering.
    squashed = SequenceMatcher(
        None, na.replace(" ", ""), nb.replace(" ", "")
    ).ratio()
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    word_blend = 0.4 * seq + 0.6 * jaccard
    return round(max(squashed, word_blend), 4)


def author_overlap(bib_authors: list[str], record_authors: list[str]) -> float:
    """Fraction of record authors whose surname appears in the BibTeX entry."""
    if not bib_authors or not record_authors:
        return 0.0
    bib_surnames = {_surname(a) for a in bib_authors if _surname(a)}
    if not bib_surnames:
        return 0.0
    hits = sum(1 for a in record_authors if _surname(a) in bib_surnames)
    return round(hits / len(record_authors), 4)


def _surname(author: str) -> str:
    """Extract a normalized surname from a BibTeX/plain author string.

    Handles both BibTeX name forms: ``Surname, Given`` and ``Given Surname``.
    """
    author = (author or "").strip()
    if not author:
        return ""
    if "," in author:
        surname = author.split(",", 1)[0]
    else:
        parts = author.split()
        surname = parts[-1] if parts else ""
    return normalize(surname)
