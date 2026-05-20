"""The verification engine: decide whether a BibTeX entry is authentic.

A verdict is reached purely by code — fetch the authoritative record for the
entry's DOI / arXiv ID / title, then compare metadata. No AI, no guessing.
This module is the shared core used by the CLI, the GUI dialog, and the MCP
server.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from .bibparser import BibEntry, parse_bibtex
from .matching import author_overlap, similarity
from .sources import (
    Record,
    SourceError,
    arxiv_lookup,
    crossref_by_doi,
    crossref_search,
)

# Verdict values.
VERIFIED = "verified"      # confirmed against an authoritative record
MISMATCH = "mismatch"      # a record exists but its metadata does not match
NOT_FOUND = "not_found"    # nothing matching exists — likely fabricated
UNVERIFIED = "unverified"  # could not be checked (no identifiers, or network)
ERROR = "error"            # unexpected failure

# Title-similarity decision thresholds.
_TITLE_STRONG = 0.80
_TITLE_WEAK = 0.50

STATUS_ICON = {
    VERIFIED: "OK",
    MISMATCH: "MISMATCH",
    NOT_FOUND: "FABRICATED?",
    UNVERIFIED: "UNVERIFIED",
    ERROR: "ERROR",
}


@dataclass
class VerificationResult:
    """The outcome of verifying one BibTeX entry."""

    key: str
    title: str
    status: str
    reason: str
    confidence: float = 0.0
    doi: str = ""
    checked_via: str = ""
    matched_title: str = ""
    matched_doi: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def authentic(self) -> bool:
        return self.status == VERIFIED

    @property
    def suspicious(self) -> bool:
        return self.status in (MISMATCH, NOT_FOUND)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "status": self.status,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "doi": self.doi,
            "checkedVia": self.checked_via,
            "matchedTitle": self.matched_title,
            "matchedDoi": self.matched_doi,
            "issues": self.issues,
        }


def verify_entry(
    entry: BibEntry, *, timeout: int = 20, email: str | None = None
) -> VerificationResult:
    """Verify a single BibTeX entry against authoritative databases."""
    result = VerificationResult(
        key=entry.key or "(no key)",
        title=entry.title,
        status=UNVERIFIED,
        reason="",
        doi=entry.doi,
    )
    try:
        if entry.doi:
            _verify_by_doi(entry, result, timeout, email)
        elif entry.arxiv_id:
            _verify_by_arxiv(entry, result, timeout, email)
        else:
            _verify_by_title(entry, result, timeout, email)
    except SourceError as exc:
        result.status = UNVERIFIED
        result.checked_via = "network"
        result.reason = f"Could not verify - {exc}. Try again later."
    except Exception as exc:  # noqa: BLE001 - last-resort guard, surfaced to user
        result.status = ERROR
        result.reason = f"Verification error: {exc}"
    return result


def verify_entries(
    entries: list[BibEntry],
    *,
    timeout: int = 20,
    email: str | None = None,
    max_workers: int = 4,
    progress: Callable[[int, int], None] | None = None,
) -> list[VerificationResult]:
    """Verify many entries concurrently, preserving input order.

    ``progress`` is called with ``(completed, total)`` after each entry so a
    GUI or CLI can show a live count. Concurrency is capped low to stay polite
    to the public APIs.
    """
    total = len(entries)
    results: list[VerificationResult | None] = [None] * total
    done = 0

    def task(idx_entry):
        idx, entry = idx_entry
        return idx, verify_entry(entry, timeout=timeout, email=email)

    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 8))) as pool:
        for idx, res in pool.map(task, enumerate(entries)):
            results[idx] = res
            done += 1
            if progress:
                progress(done, total)

    return [r for r in results if r is not None]


def verify_bibtex(
    text: str, *, timeout: int = 20, email: str | None = None, **kwargs
) -> list[VerificationResult]:
    """Convenience wrapper: parse raw ``.bib`` text and verify every entry."""
    return verify_entries(parse_bibtex(text), timeout=timeout, email=email, **kwargs)


def summary(results: list[VerificationResult]) -> dict[str, int]:
    """Count results by status, plus a ``total``."""
    counts = {s: 0 for s in (VERIFIED, MISMATCH, NOT_FOUND, UNVERIFIED, ERROR)}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    counts["total"] = len(results)
    return counts


# --------------------------------------------------------------------------
# Per-strategy verification
# --------------------------------------------------------------------------

def _verify_by_doi(entry, result, timeout, email):
    result.checked_via = "crossref/doi"
    record = crossref_by_doi(entry.doi, timeout=timeout, email=email)
    if record is None:
        result.status = NOT_FOUND
        result.confidence = 0.95
        result.reason = (
            f"DOI '{entry.doi}' is not registered with CrossRef. "
            "A non-resolving DOI is a strong sign of a fabricated reference."
        )
        return
    _apply_record_match(entry, result, record, has_identifier=True)


def _verify_by_arxiv(entry, result, timeout, email):
    result.checked_via = "arxiv"
    record = arxiv_lookup(entry.arxiv_id, timeout=timeout, email=email)
    if record is None:
        result.status = NOT_FOUND
        result.confidence = 0.9
        result.reason = (
            f"arXiv ID '{entry.arxiv_id}' does not exist on arXiv. "
            "The reference is very likely fabricated."
        )
        return
    _apply_record_match(entry, result, record, has_identifier=True)


def _verify_by_title(entry, result, timeout, email):
    result.checked_via = "crossref/search"
    if not entry.title:
        result.status = UNVERIFIED
        result.reason = (
            "Entry has no DOI, arXiv ID, or title — there is nothing to verify "
            "it against."
        )
        return
    first_author = entry.authors[0] if entry.authors else None
    records = crossref_search(entry.title, first_author, timeout=timeout, email=email)
    if not records:
        result.status = NOT_FOUND
        result.confidence = 0.7
        result.reason = (
            "No publication matching this title was found in CrossRef. "
            "The reference may be fabricated — confirm it exists."
        )
        return
    best = max(records, key=lambda r: similarity(entry.title, r.title))
    sim = similarity(entry.title, best.title)
    result.matched_title = best.title
    result.matched_doi = best.doi
    if sim >= _TITLE_STRONG:
        result.status = VERIFIED
        result.confidence = sim
        result.reason = (
            f"A matching publication exists in CrossRef (DOI {best.doi}). "
            f"Add 'doi = {{{best.doi}}}' to make this citation verifiable."
        )
        result.issues = _metadata_issues(entry, best)
    elif sim >= _TITLE_WEAK:
        result.status = MISMATCH
        result.confidence = sim
        result.reason = (
            f"No exact match. Closest CrossRef result: \"{best.title}\" "
            f"(DOI {best.doi}). Confirm this reference is correct."
        )
    else:
        result.status = NOT_FOUND
        result.confidence = 1.0 - sim
        result.reason = (
            "No publication matching this title was found in CrossRef "
            f"(closest: \"{best.title}\"). The reference may be fabricated."
        )


def _apply_record_match(entry, result, record: Record, *, has_identifier: bool):
    """Compare an entry against a record found via its DOI/arXiv identifier."""
    result.matched_title = record.title
    result.matched_doi = record.doi or entry.doi
    if not entry.title:
        result.status = VERIFIED
        result.confidence = 0.7
        result.reason = (
            f"The {record.source} record exists, but the entry has no title "
            "to cross-check. Identifier is genuine."
        )
        result.issues = _metadata_issues(entry, record)
        return

    sim = similarity(entry.title, record.title)
    result.confidence = sim
    result.issues = _metadata_issues(entry, record)
    if sim >= _TITLE_STRONG:
        result.status = VERIFIED
        result.reason = (
            f"Identifier resolves and the title matches the {record.source} "
            "record."
        )
    elif sim <= _TITLE_WEAK:
        result.status = MISMATCH
        result.reason = (
            f"The identifier resolves but to a DIFFERENT paper: "
            f"\"{record.title}\". This identifier does not belong to this "
            "reference."
        )
    else:
        result.status = MISMATCH
        result.reason = (
            f"The identifier resolves, but its registered title only "
            f"partially matches (\"{record.title}\"). Review this reference."
        )


def _metadata_issues(entry, record: Record) -> list[str]:
    """Collect secondary metadata discrepancies (year, authors)."""
    issues: list[str] = []
    if entry.year and record.year and entry.year != record.year:
        issues.append(
            f"Year mismatch: entry says {entry.year}, record says {record.year}."
        )
    if entry.authors and record.authors:
        overlap = author_overlap(entry.authors, record.authors)
        if overlap < 0.34:
            issues.append(
                "Authors do not match the registered record."
            )
    return issues
