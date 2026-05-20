"""QuickBib reference-verification engine.

A deterministic, dependency-free toolkit that decides whether the BibTeX
references in a paper are *authentic* or likely *hallucinated*. It checks each
entry against authoritative databases (CrossRef, arXiv) and never relies on an
AI model to make the judgement.

The same engine powers three front-ends:

* the ``python -m quickbib.verify`` command-line tool,
* the "Verify References" dialog in the QuickBib desktop app,
* the optional QuickBib MCP server (``quickbib_mcp``).
"""

from .bibparser import BibEntry, normalize_doi, parse_bibtex
from .citecheck import CiteCheckResult, check_cite_keys, extract_cite_keys
from .verifier import (
    ERROR,
    MISMATCH,
    NOT_FOUND,
    STATUS_ICON,
    UNVERIFIED,
    VERIFIED,
    VerificationResult,
    summary,
    verify_bibtex,
    verify_entries,
    verify_entry,
)

__all__ = [
    "BibEntry",
    "parse_bibtex",
    "normalize_doi",
    "CiteCheckResult",
    "check_cite_keys",
    "extract_cite_keys",
    "VerificationResult",
    "verify_entry",
    "verify_entries",
    "verify_bibtex",
    "summary",
    "VERIFIED",
    "MISMATCH",
    "NOT_FOUND",
    "UNVERIFIED",
    "ERROR",
    "STATUS_ICON",
]
