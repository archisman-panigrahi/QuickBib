#!/usr/bin/env python3
"""QuickBib MCP server - verify BibTeX references against CrossRef and arXiv.

This exposes QuickBib's deterministic reference-verification engine as Model
Context Protocol tools, so an MCP client (Claude Desktop, Claude Code, Cursor,
...) can check whether the references in a paper are authentic or hallucinated.

The verdicts are produced entirely by this server's own code. The AI client
only invokes a tool and relays the structured result back to the user - it
never decides authenticity itself.
"""

import os
import re
import sys
from pathlib import Path

# When this script is launched directly (the usual way an MCP server starts),
# make the sibling `quickbib` package importable without any install step.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from doi2bib3 import (  # noqa: E402
    BibEntry,
    STATUS_ICON,
    VERIFIED,
    check_cite_keys,
    normalize_doi,
    parse_bibtex,
    summary,
    verify_entries,
    verify_entry,
)
from quickbib.overleaf import (  # noqa: E402
    OverleafError,
    clone_or_pull,
    find_bib_files,
    find_tex_files,
)

mcp = FastMCP("quickbib-verifier")

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_ARXIV_RE = re.compile(
    r"(?i)^(arxiv:)?(\d{4}\.\d{4,5}(v\d+)?|[a-z][a-z\-]+(\.[A-Z]{2})?/\d{7})$"
)


# --------------------------------------------------------------------------
# MCP tools
# --------------------------------------------------------------------------

@mcp.tool()
def verify_overleaf_project(project_id: str = "", git_token: str = "") -> dict:
    """Verify every BibTeX reference in an Overleaf project.

    Clones the project through Overleaf's Git bridge, checks all .bib entries
    against CrossRef and arXiv, and cross-checks the \\cite keys used in the
    .tex files. Use this to catch DOIs that do not resolve, references whose
    metadata does not match, and citation keys that were never defined.

    Args:
        project_id: Overleaf project ID (from the project URL). Falls back to
            the OVERLEAF_PROJECT_ID environment variable.
        git_token: Overleaf Git token. Falls back to OVERLEAF_GIT_TOKEN.
    """
    project_id = project_id or os.environ.get("OVERLEAF_PROJECT_ID", "")
    git_token = git_token or os.environ.get("OVERLEAF_GIT_TOKEN", "")
    try:
        repo = clone_or_pull(project_id, git_token)
    except OverleafError as exc:
        return {"error": str(exc)}

    entries: list[BibEntry] = []
    for bib in find_bib_files(repo):
        entries += parse_bibtex(_read(bib))
    if not entries:
        return {"error": "No .bib entries were found in the Overleaf project."}

    tex_sources = [_read(t) for t in find_tex_files(repo)]
    results = verify_entries(entries)
    cite = None
    if tex_sources:
        cite = check_cite_keys(tex_sources, {e.key for e in entries if e.key})
    return _payload(results, f"Overleaf project {project_id}", cite)


@mcp.tool()
def verify_bib_file(path: str) -> dict:
    """Verify every BibTeX entry in a local .bib file.

    Args:
        path: Absolute path to a .bib file.
    """
    bib = Path(path)
    if not bib.is_file():
        return {"error": f"No such file: {path}"}
    entries = parse_bibtex(_read(bib))
    if not entries:
        return {"error": "No BibTeX entries found in the file."}
    results = verify_entries(entries)
    return _payload(results, str(bib))


@mcp.tool()
def verify_bibtex_text(bibtex: str) -> dict:
    """Verify BibTeX entries supplied directly as text.

    Useful for spot-checking entries pasted into the conversation.

    Args:
        bibtex: Raw BibTeX source containing one or more @entries.
    """
    entries = parse_bibtex(bibtex)
    if not entries:
        return {"error": "No BibTeX entries could be parsed from the input."}
    results = verify_entries(entries)
    return _payload(results, "pasted BibTeX")


@mcp.tool()
def verify_reference(query: str) -> dict:
    """Verify a single reference given a DOI, arXiv ID, or article title.

    Args:
        query: A DOI, an arXiv identifier, or an article title.
    """
    result = verify_entry(_entry_from_query(query))
    return result.to_dict()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _read(path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _entry_from_query(query: str) -> BibEntry:
    """Wrap a free-form query (DOI / arXiv ID / title) in a synthetic entry."""
    q = (query or "").strip()
    if _DOI_RE.match(normalize_doi(q)):
        return BibEntry("misc", "query", {"doi": q})
    if _ARXIV_RE.match(q):
        return BibEntry(
            "misc",
            "query",
            {"eprint": re.sub(r"(?i)^arxiv:", "", q), "archiveprefix": "arXiv"},
        )
    return BibEntry("misc", "query", {"title": q})


def _payload(results, label: str, cite=None) -> dict:
    """Build the structured + human-readable response returned to the client."""
    payload = {
        "source": label,
        "summary": summary(results),
        "flagged": [r.to_dict() for r in results if r.needs_attention],
        "results": [r.to_dict() for r in results],
        "report": _report_text(results, label, cite),
    }
    if cite is not None:
        payload["citeCheck"] = cite.to_dict()
    return payload


def _report_text(results, label: str, cite) -> str:
    """A compact plain-text report the AI client can relay verbatim."""
    counts = summary(results)
    lines = [
        f"Reference check - {label}",
        (
            f"{counts['total']} references: {counts['verified']} verified, "
            f"{counts['review']} review, {counts['mismatch']} mismatch, "
            f"{counts['not_found']} unresolved, "
            f"{counts['unverified'] + counts['error']} unverified."
        ),
    ]
    flagged = [r for r in results if r.status != VERIFIED]
    if flagged:
        lines.append("")
        lines.append("Needs attention:")
        for r in flagged:
            icon = STATUS_ICON.get(r.status, r.status)
            lines.append(f"  [{icon}] {r.key}: {r.reason}")
    else:
        lines.append("All references verified against CrossRef / arXiv.")
    if cite is not None and cite.undefined:
        lines.append("")
        lines.append(
            "Cited but undefined keys (possibly invented): "
            + ", ".join(sorted(cite.undefined))
        )
    return "\n".join(lines)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
