"""Command-line interface for the QuickBib reference verifier.

Runs entirely offline of any AI service. Examples::

    python -m quickbib.verify references.bib
    python -m quickbib.verify ./paper-folder --email you@example.com
    python -m quickbib.verify --overleaf 65xxxxxxxxxxxxxxxxxxxxxx --token olp_xxx
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .bibparser import parse_bibtex
from .citecheck import check_cite_keys
from .overleaf import OverleafError, clone_or_pull, find_bib_files, find_tex_files
from .verifier import STATUS_ICON, VERIFIED, summary, verify_entries


def main(argv: list[str] | None = None) -> int:
    # Keep output crash-free when a reference title contains characters the
    # console encoding cannot represent (common on Windows code pages).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    args = _build_parser().parse_args(argv)
    try:
        entries, tex_sources, label = _gather(args)
    except (OverleafError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not entries:
        print(f"No BibTeX entries found in {label}.", file=sys.stderr)
        return 1

    show_progress = not args.json
    results = verify_entries(
        entries,
        timeout=args.timeout,
        email=args.email or os.environ.get("CROSSREF_EMAIL"),
        max_workers=args.workers,
        progress=_progress if show_progress else None,
    )
    if show_progress:
        print("", file=sys.stderr)

    cite = None
    if tex_sources:
        cite = check_cite_keys(tex_sources, {e.key for e in entries if e.key})

    if args.json:
        _print_json(label, results, cite)
    else:
        _print_report(label, results, cite)

    flagged = any(r.suspicious for r in results)
    bad_keys = bool(cite and cite.undefined)
    return 1 if (flagged or bad_keys) else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quickbib-verify",
        description="Verify that BibTeX references are authentic, not hallucinated.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a .bib file or a folder containing .bib/.tex files.",
    )
    parser.add_argument(
        "--overleaf",
        metavar="PROJECT_ID",
        help="Verify an Overleaf project directly via its Git bridge.",
    )
    parser.add_argument(
        "--token",
        help="Overleaf Git token (or set the OVERLEAF_GIT_TOKEN env var).",
    )
    parser.add_argument(
        "--email",
        help="Contact email for CrossRef's faster 'polite pool' (optional).",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Concurrent lookups (default: 4)."
    )
    parser.add_argument(
        "--timeout", type=int, default=20, help="Per-request timeout in seconds."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def _gather(args) -> tuple[list, list[str], str]:
    """Collect BibTeX entries and LaTeX sources from the requested location."""
    entries: list = []
    tex_sources: list[str] = []

    if args.overleaf:
        token = args.token or os.environ.get("OVERLEAF_GIT_TOKEN", "")
        repo = clone_or_pull(args.overleaf, token)
        for bib in find_bib_files(repo):
            entries += parse_bibtex(_read(bib))
        tex_sources = [_read(t) for t in find_tex_files(repo)]
        return entries, tex_sources, f"Overleaf project {args.overleaf}"

    if not args.source:
        raise OSError("Provide a .bib file/folder, or use --overleaf PROJECT_ID.")

    path = Path(args.source)
    if not path.exists():
        raise OSError(f"No such file or folder: {path}")

    if path.is_dir():
        for bib in sorted(path.rglob("*.bib")):
            entries += parse_bibtex(_read(bib))
        tex_sources = [_read(t) for t in sorted(path.rglob("*.tex"))]
        return entries, tex_sources, str(path)

    text = _read(path)
    if path.suffix.lower() == ".tex":
        tex_sources.append(text)
    else:
        entries = parse_bibtex(text)
    return entries, tex_sources, str(path)


def _read(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _progress(done: int, total: int) -> None:
    print(f"\rVerifying references... {done}/{total}", end="", file=sys.stderr)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def _print_report(label: str, results: list, cite) -> None:
    counts = summary(results)
    print("QuickBib Reference Verifier")
    print(f"Source: {label}")
    print(
        f"Checked {counts['total']} references - "
        f"{counts['verified']} OK, {counts['mismatch']} mismatch, "
        f"{counts['not_found']} not found, "
        f"{counts['unverified'] + counts['error']} unverified"
    )
    print()

    flagged = [r for r in results if r.status != VERIFIED]
    if not flagged:
        print("  [OK] All references verified against CrossRef / arXiv.")
    for r in flagged:
        print(f"  [{STATUS_ICON.get(r.status, r.status)}] {r.key}")
        if r.title:
            print(f"      title : {r.title}")
        print(f"      {r.reason}")
        for issue in r.issues:
            print(f"      - {issue}")
        print()

    if cite is not None:
        print(f"Cite-key check: {len(cite.cited)} cited, {len(cite.defined)} defined")
        if cite.undefined:
            print(
                "  Cited but NOT defined in any .bib (possibly invented keys): "
                + ", ".join(sorted(cite.undefined))
            )
        if cite.unused:
            print("  Defined but never cited: " + ", ".join(sorted(cite.unused)))
        if not cite.undefined and not cite.unused:
            print("  [OK] Every cited key is defined.")


def _print_json(label: str, results: list, cite) -> None:
    payload = {
        "source": label,
        "summary": summary(results),
        "results": [r.to_dict() for r in results],
    }
    if cite is not None:
        payload["citeCheck"] = cite.to_dict()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
