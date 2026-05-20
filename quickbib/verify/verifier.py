"""The verification engine: decide whether a BibTeX entry is authentic.

A verdict is reached purely by code, from corroborating evidence:

* whether the DOI / arXiv identifier resolves at all (CrossRef, and the
  registry-agnostic DOI Handle System);
* how well the registered title matches the entry's title;
* whether the authors and year corroborate.

A reference is only ``verified`` when authoritative data backs it up, and a
hard verdict (``not_found`` / ``mismatch``) is only reached when two
independent signals agree. Anything uncertain is surfaced as ``review`` or
``unverified`` rather than guessed at. This module is the shared core used by
the CLI, the GUI dialog and the MCP server.
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
    doi_exists,
)

# Verdict values.
VERIFIED = "verified"      # corroborated against an authoritative record
REVIEW = "review"          # the work exists, but metadata could not be confirmed
MISMATCH = "mismatch"      # identifier resolves, but to a clearly different paper
NOT_FOUND = "not_found"    # the identifier does not resolve anywhere
UNVERIFIED = "unverified"  # could not be checked (no identifiers, no match, offline)
ERROR = "error"            # unexpected failure

# Decision thresholds.
_TITLE_STRONG = 0.80
_TITLE_WEAK = 0.55
_AUTHOR_OK = 0.50

STATUS_ICON = {
    VERIFIED: "OK",
    REVIEW: "REVIEW",
    MISMATCH: "MISMATCH",
    NOT_FOUND: "UNRESOLVED",
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
    def needs_attention(self) -> bool:
        """Anything that is not a clean ``verified`` is worth surfacing."""
        return self.status != VERIFIED

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


def verify_entry(entry: BibEntry, *, timeout: int = 20) -> VerificationResult:
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
            _verify_by_doi(entry, result, timeout)
        elif entry.arxiv_id:
            _verify_by_arxiv(entry, result, timeout)
        else:
            _verify_by_title(entry, result, timeout)
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
    max_workers: int = 4,
    progress: Callable[[int, int], None] | None = None,
) -> list[VerificationResult]:
    """Verify many entries concurrently, preserving input order.

    ``progress`` is called with ``(completed, total)`` after each entry.
    Concurrency is capped low to stay polite to the public APIs.
    """
    total = len(entries)
    results: list[VerificationResult | None] = [None] * total
    done = 0

    def task(idx_entry):
        idx, entry = idx_entry
        return idx, verify_entry(entry, timeout=timeout)

    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 8))) as pool:
        for idx, res in pool.map(task, enumerate(entries)):
            results[idx] = res
            done += 1
            if progress:
                progress(done, total)

    return [r for r in results if r is not None]


def verify_bibtex(text: str, *, timeout: int = 20, **kwargs) -> list[VerificationResult]:
    """Convenience wrapper: parse raw ``.bib`` text and verify every entry."""
    return verify_entries(parse_bibtex(text), timeout=timeout, **kwargs)


def summary(results: list[VerificationResult]) -> dict[str, int]:
    """Count results by status, plus a ``total``."""
    counts = {s: 0 for s in (VERIFIED, REVIEW, MISMATCH, NOT_FOUND, UNVERIFIED, ERROR)}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    counts["total"] = len(results)
    return counts


# --------------------------------------------------------------------------
# Per-strategy verification
# --------------------------------------------------------------------------

def _verify_by_doi(entry, result, timeout):
    """Verify an entry that carries a DOI."""
    result.checked_via = "crossref/doi"
    record = crossref_by_doi(entry.doi, timeout=timeout)
    if record is not None:
        _score_against_record(entry, result, record, identifier="DOI")
        return

    # CrossRef has no such work - consult the registry-agnostic Handle System
    # before concluding anything, since books and datasets are not in CrossRef.
    result.checked_via = "doi.org"
    exists = doi_exists(entry.doi, timeout=timeout)
    if exists is True:
        result.status = VERIFIED
        result.confidence = 0.6
        result.reason = (
            f"The DOI '{entry.doi}' is registered with the DOI system but is "
            "not indexed by CrossRef, so its title could not be cross-checked."
        )
    elif exists is False:
        result.status = NOT_FOUND
        result.confidence = 0.9
        result.reason = (
            f"The DOI '{entry.doi}' does not resolve in CrossRef or the DOI "
            "registry. Check that it is correct."
        )
    else:
        result.status = UNVERIFIED
        result.reason = (
            f"The DOI '{entry.doi}' is not in CrossRef and the DOI registry "
            "could not be reached to confirm it. Try again later."
        )


def _verify_by_arxiv(entry, result, timeout):
    """Verify an entry that carries an arXiv identifier."""
    result.checked_via = "arxiv"
    record = arxiv_lookup(entry.arxiv_id, timeout=timeout)
    if record is None:
        result.status = NOT_FOUND
        result.confidence = 0.9
        result.reason = (
            f"The arXiv ID '{entry.arxiv_id}' does not resolve to a paper on "
            "arXiv. Check that it is correct."
        )
        return
    _score_against_record(entry, result, record, identifier="arXiv ID")


def _verify_by_title(entry, result, timeout):
    """Verify an entry that has no DOI or arXiv ID - search CrossRef by title."""
    result.checked_via = "crossref/search"
    if not entry.title:
        result.status = UNVERIFIED
        result.reason = (
            "The entry has no DOI, arXiv ID, or title, so there is nothing to "
            "verify it against."
        )
        return

    first_author = entry.authors[0] if entry.authors else None
    records = crossref_search(entry.title, first_author, timeout=timeout)
    if not records:
        result.status = UNVERIFIED
        result.reason = (
            "This entry has no DOI, and no matching record was found in "
            "CrossRef. Add a DOI so it can be verified."
        )
        return

    best = max(records, key=lambda r: similarity(entry.title, r.title))
    title_score = similarity(entry.title, best.title)
    author_score = author_overlap(entry.authors, best.authors)
    result.matched_title = best.title
    result.matched_doi = best.doi
    result.confidence = title_score

    corroborated = author_score > 0 or _years_close(entry.year, best.year)
    if title_score >= _TITLE_STRONG and corroborated:
        result.status = VERIFIED
        result.reason = (
            f"A matching publication was found in CrossRef (DOI {best.doi}). "
            f"Add 'doi = {{{best.doi}}}' to the entry to make it directly "
            "verifiable."
        )
        result.issues = _metadata_issues(entry, best)
    elif title_score >= _TITLE_STRONG:
        result.status = REVIEW
        result.reason = (
            f"A publication with a very similar title was found in CrossRef "
            f"(DOI {best.doi}), but its authors and year could not be matched "
            "to this entry. Confirm it is the same work."
        )
    else:
        result.status = UNVERIFIED
        result.reason = (
            "This entry has no DOI, and no confident match was found in "
            f"CrossRef (closest: \"{best.title}\"). Add a DOI so it can be "
            "verified."
        )


def _score_against_record(entry, result, record: Record, *, identifier: str):
    """Compare an entry against the record its DOI/arXiv identifier resolved to."""
    result.matched_title = record.title
    result.matched_doi = record.doi or entry.doi
    result.issues = _metadata_issues(entry, record)

    if not entry.title:
        result.status = VERIFIED
        result.confidence = 0.7
        result.reason = (
            f"The {identifier} resolves to a registered {record.source} "
            "record; the entry has no title to cross-check."
        )
        return

    title_score = similarity(entry.title, record.title)
    author_score = author_overlap(entry.authors, record.authors)
    result.confidence = title_score

    if title_score >= _TITLE_STRONG:
        result.status = VERIFIED
        result.reason = (
            f"The {identifier} resolves and the title matches the "
            f"{record.source} record."
        )
    elif author_score >= _AUTHOR_OK:
        # Title differs but the authors agree - same paper, different encoding.
        result.status = VERIFIED
        result.confidence = max(title_score, author_score)
        result.reason = (
            f"The {identifier} resolves and the authors match the "
            f"{record.source} record."
        )
        result.issues = result.issues + [
            f"The registered title (\"{record.title}\") is written "
            "differently from the entry - likely a formatting or source "
            "difference."
        ]
    elif (
        title_score < _TITLE_WEAK
        and entry.authors
        and record.authors
        and author_score == 0
    ):
        # Two independent signals disagree - the identifier likely belongs
        # to a different paper.
        result.status = MISMATCH
        result.reason = (
            f"The {identifier} resolves, but to a record with a different "
            f"title (\"{record.title}\") and different authors. The "
            f"{identifier} may belong to another paper - check it."
        )
    else:
        result.status = REVIEW
        result.reason = (
            f"The {identifier} resolves, but the registered title "
            f"(\"{record.title}\") could not be matched to this entry with "
            "confidence. Worth a quick check."
        )


def _metadata_issues(entry, record: Record) -> list[str]:
    """Collect secondary metadata discrepancies (year, authors)."""
    issues: list[str] = []
    if entry.year and record.year and not _years_close(entry.year, record.year):
        issues.append(
            f"Year differs: the entry says {entry.year}, the record says "
            f"{record.year}."
        )
    if entry.authors and record.authors:
        if author_overlap(entry.authors, record.authors) < 0.34:
            issues.append("Authors do not match the registered record.")
    return issues


def _years_close(a: str, b: str) -> bool:
    """True when two year strings are within one year of each other."""
    try:
        return abs(int(a) - int(b)) <= 1
    except (TypeError, ValueError):
        return False
