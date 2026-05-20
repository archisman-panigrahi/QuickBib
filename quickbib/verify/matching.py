"""Text normalization and fuzzy similarity helpers for reference verification.

These functions are deterministic and dependency-free. They are used to
compare the metadata written in a BibTeX entry against the authoritative
record returned by CrossRef / arXiv, so the verifier can decide whether the
two describe the same publication.
"""

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


def strip_latex(text: str) -> str:
    """Remove LaTeX markup so plain words remain.

    Drops control sequences (``\\emph``, ``\\textbf`` ...) but keeps their
    arguments, unwraps braces, and resolves a handful of escaped characters.
    """
    if not text:
        return ""
    for src, dst in _ESCAPED.items():
        text = text.replace(src, dst)
    # Drop control sequences but leave the following text/argument in place.
    text = re.sub(r"\\[a-zA-Z]+\*?\s*", " ", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace("\\", " ")
    return text


def clean(text: str) -> str:
    """Human-readable cleanup: strip LaTeX and collapse whitespace."""
    return re.sub(r"\s+", " ", strip_latex(text or "")).strip()


def normalize(text: str) -> str:
    """Aggressive normalization for comparison.

    Lowercased, LaTeX stripped, reduced to ``a-z0-9`` words. Two strings that
    normalize to the same value describe, for our purposes, the same thing.
    """
    if not text:
        return ""
    text = strip_latex(text).lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    """Return a 0.0-1.0 similarity score between two free-text strings.

    Blends a character-sequence ratio with a word-set Jaccard score so the
    result is robust both to small typos and to re-ordered words.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return round(0.4 * seq + 0.6 * jaccard, 4)


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
