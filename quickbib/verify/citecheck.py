"""Cross-check ``\\cite`` keys in LaTeX against the keys defined in BibTeX.

This catches a distinct class of hallucination that needs no network access:
a citation command that points at a key which was never defined in any
``.bib`` file (an invented citation key), and — as a bonus — entries that are
defined but never cited.
"""

import re
from dataclasses import dataclass, field

# Matches the whole \cite family: \cite, \citep, \citet, \autocite,
# \textcite, \parencite, \footcite, \nocite, \citeauthor, ... including a
# trailing ``*`` and up to two optional ``[...]`` arguments.
_CITE_RE = re.compile(
    r"\\[a-zA-Z]*cite[a-zA-Z]*\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]+)\}"
)
_COMMENT_RE = re.compile(r"(?<!\\)%.*")


@dataclass
class CiteCheckResult:
    """Outcome of comparing cited keys against defined keys."""

    cited: set[str] = field(default_factory=set)
    defined: set[str] = field(default_factory=set)
    undefined: set[str] = field(default_factory=set)  # cited but never defined
    unused: set[str] = field(default_factory=set)     # defined but never cited

    def to_dict(self) -> dict:
        return {
            "citedCount": len(self.cited),
            "definedCount": len(self.defined),
            "undefined": sorted(self.undefined),
            "unused": sorted(self.unused),
        }


def extract_cite_keys(tex: str) -> set[str]:
    """Return every citation key referenced by ``\\cite``-style commands."""
    keys: set[str] = set()
    for stripped in (_COMMENT_RE.sub("", line) for line in tex.splitlines()):
        for match in _CITE_RE.finditer(stripped):
            for key in match.group(1).split(","):
                key = key.strip()
                if key:
                    keys.add(key)
    return keys


def check_cite_keys(tex_sources: list[str], defined_keys: set[str]) -> CiteCheckResult:
    """Compare keys cited across LaTeX sources with keys defined in BibTeX."""
    cited: set[str] = set()
    for tex in tex_sources:
        cited |= extract_cite_keys(tex)
    defined = set(defined_keys)
    return CiteCheckResult(
        cited=cited,
        defined=defined,
        undefined=cited - defined,
        unused=defined - cited,
    )
