"""A small, dependency-free BibTeX (.bib) parser.

It is deliberately lenient: real-world ``.bib`` files contain all kinds of
quirks, and for reference verification we only need the citation key plus a
handful of fields (title, author, year, doi, eprint). Anything it cannot
parse is skipped rather than raising.
"""

import re
from dataclasses import dataclass, field

from .matching import clean

# arXiv identifiers: new style (1501.00001) and old style (hep-th/9901001).
_ARXIV_NEW = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
_ARXIV_OLD = re.compile(r"\b([a-z][a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b")
_DOI_IN_TEXT = re.compile(r"10\.\d{4,9}/[^\s{}\"<>]+", re.IGNORECASE)


@dataclass
class BibEntry:
    """A single parsed BibTeX entry (``@article{key, ...}``)."""

    entry_type: str
    key: str
    fields: dict[str, str] = field(default_factory=dict)
    line: int = 0

    def get(self, name: str) -> str:
        """Case-insensitive field lookup; returns ``""`` when absent."""
        return self.fields.get(name.lower(), "")

    @property
    def title(self) -> str:
        return clean(self.get("title"))

    @property
    def year(self) -> str:
        for name in ("year", "date"):
            m = re.search(r"\d{4}", self.get(name))
            if m:
                return m.group(0)
        return ""

    @property
    def authors(self) -> list[str]:
        """Author surnames-and-names split on the BibTeX ``and`` separator."""
        raw = self.get("author") or self.get("editor")
        if not raw:
            return []
        raw = clean(raw)
        return [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]

    @property
    def doi(self) -> str:
        """Normalized DOI from the ``doi`` field, or extracted from a URL."""
        doi = self.get("doi")
        if not doi:
            for name in ("url", "note", "howpublished"):
                m = _DOI_IN_TEXT.search(self.get(name))
                if m:
                    doi = m.group(0)
                    break
        return normalize_doi(doi)

    @property
    def arxiv_id(self) -> str:
        """arXiv identifier from ``eprint``/``archiveprefix`` or a URL/journal."""
        prefix = self.get("archiveprefix").lower() or self.get("eprinttype").lower()
        eprint = self.get("eprint").strip()
        if eprint and ("arxiv" in prefix or not prefix):
            cand = re.sub(r"(?i)^arxiv:", "", eprint).strip()
            if _ARXIV_NEW.search(cand) or _ARXIV_OLD.search(cand):
                return cand
        for name in ("journal", "url", "note", "eprint"):
            text = self.get(name)
            if "arxiv" in text.lower():
                m = _ARXIV_NEW.search(text) or _ARXIV_OLD.search(text)
                if m:
                    return m.group(0)
        return ""


def normalize_doi(doi: str) -> str:
    """Strip URL/`doi:` prefixes and surrounding noise; lowercase the result."""
    if not doi:
        return ""
    doi = doi.strip().strip("{}").strip()
    doi = re.sub(r"(?i)^\s*(https?://)?(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"(?i)^\s*doi:\s*", "", doi)
    return doi.strip().rstrip(".").lower()


def parse_bibtex(text: str) -> list[BibEntry]:
    """Parse BibTeX source into a list of :class:`BibEntry`.

    ``@string`` definitions are collected and substituted; ``@comment`` and
    ``@preamble`` blocks are ignored.
    """
    strings: dict[str, str] = {}
    entries: list[BibEntry] = []
    i, n = 0, len(text)

    while i < n:
        at = text.find("@", i)
        if at == -1:
            break
        j = at + 1
        while j < n and (text[j].isalnum() or text[j] in "_-"):
            j += 1
        etype = text[at + 1:j].strip().lower()
        while j < n and text[j] in " \t\r\n":
            j += 1
        if j >= n or text[j] not in "{(":
            i = at + 1
            continue

        opener = text[j]
        body, end = _read_block(text, j, opener)
        line = text.count("\n", 0, at) + 1
        i = end

        if etype in ("comment", "preamble") or not etype:
            continue
        if etype == "string":
            name, value = _parse_string_def(body, strings)
            if name:
                strings[name.lower()] = value
            continue

        key, fields = _parse_entry_body(body, strings)
        if key or fields:
            entries.append(BibEntry(etype, key, fields, line))

    return entries


def _read_block(text: str, open_idx: int, opener: str) -> tuple[str, int]:
    """Return (inner-body, index-after-close) for a brace/paren delimited block."""
    closer = "}" if opener == "{" else ")"
    depth = 1
    k = open_idx + 1
    n = len(text)
    while k < n and depth > 0:
        c = text[k]
        if c == "\\":
            k += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and opener == "{":
                return text[open_idx + 1:k], k + 1
        elif c == closer and opener == "(" and depth == 1:
            return text[open_idx + 1:k], k + 1
        k += 1
    return text[open_idx + 1:k], k


def _split_top_level(body: str, sep: str) -> list[str]:
    """Split on ``sep`` only where it is outside braces and quotes."""
    parts: list[str] = []
    depth = 0
    in_quote = False
    start = 0
    i = 0
    while i < len(body):
        c = body[i]
        if c == "\\":
            i += 2
            continue
        if c == '"' and depth == 0:
            in_quote = not in_quote
        elif not in_quote:
            if c == "{":
                depth += 1
            elif c == "}":
                depth = max(0, depth - 1)
            elif c == sep and depth == 0:
                parts.append(body[start:i])
                start = i + 1
        i += 1
    parts.append(body[start:])
    return parts


def _parse_entry_body(body: str, strings: dict[str, str]) -> tuple[str, dict[str, str]]:
    """Split an entry body into its citation key and field dictionary."""
    chunks = _split_top_level(body, ",")
    key = chunks[0].strip() if chunks else ""
    fields: dict[str, str] = {}
    for chunk in chunks[1:]:
        if "=" not in chunk:
            continue
        eq = _first_equals(chunk)
        if eq < 0:
            continue
        name = chunk[:eq].strip().lower()
        if name:
            fields[name] = _parse_value(chunk[eq + 1:], strings)
    return key, fields


def _first_equals(chunk: str) -> int:
    """Index of the first ``=`` outside braces/quotes, or -1."""
    depth = 0
    in_quote = False
    i = 0
    while i < len(chunk):
        c = chunk[i]
        if c == "\\":
            i += 2
            continue
        if c == '"' and depth == 0:
            in_quote = not in_quote
        elif not in_quote:
            if c == "{":
                depth += 1
            elif c == "}":
                depth = max(0, depth - 1)
            elif c == "=" and depth == 0:
                return i
        i += 1
    return -1


def _parse_value(raw: str, strings: dict[str, str]) -> str:
    """Parse a (possibly ``#``-concatenated) field value into a plain string."""
    out: list[str] = []
    for token in _split_top_level(raw, "#"):
        token = token.strip()
        if not token:
            continue
        if token[0] == "{" or token[0] == '"':
            out.append(token[1:-1] if len(token) >= 2 else token)
        elif token.lower() in strings:
            out.append(strings[token.lower()])
        else:
            out.append(token)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _parse_string_def(body: str, strings: dict[str, str]) -> tuple[str, str]:
    """Parse the body of an ``@string{ name = "value" }`` definition."""
    eq = _first_equals(body)
    if eq < 0:
        return "", ""
    return body[:eq].strip(), _parse_value(body[eq + 1:], strings)
