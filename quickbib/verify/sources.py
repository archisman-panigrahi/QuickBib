"""Authoritative-record lookups against CrossRef and arXiv.

This is the part that makes verification *deterministic*: a BibTeX entry is
checked against what these public databases actually return, not against any
model's opinion. No API key is required; supplying a contact email opts in to
CrossRef's faster "polite pool".
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

try:
    from ..app_info import APP_VERSION
except Exception:  # pragma: no cover - allows standalone use
    APP_VERSION = "0"

CROSSREF_API = "https://api.crossref.org/works"
ARXIV_API = "http://export.arxiv.org/api/query"

_ATOM = {"a": "http://www.w3.org/2005/Atom"}


class SourceError(Exception):
    """Raised when a database could not be reached or returned bad data."""


@dataclass
class Record:
    """A normalized publication record from an authoritative database."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""
    container: str = ""
    source: str = ""

    def __bool__(self) -> bool:
        return bool(self.title or self.doi)


def _user_agent(email: str | None) -> str:
    ua = (
        f"QuickBib-ReferenceVerifier/{APP_VERSION} "
        "(+https://github.com/archisman-panigrahi/QuickBib)"
    )
    if email:
        ua += f" mailto:{email}"
    return ua


_MAX_RETRIES = 3


def _http_get(
    url: str, *, timeout: int, email: str | None, accept: str, _attempt: int = 0
) -> bytes:
    """Perform a GET request, translating HTTP/network failure into SourceError.

    Returns ``b""`` for a clean 404 so callers can treat "not found" as data.
    Transient throttling (429) and outages (503) are retried with backoff.
    """
    host = urllib.parse.urlsplit(url).netloc
    req = urllib.request.Request(
        url, headers={"User-Agent": _user_agent(email), "Accept": accept}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return b""
        if exc.code in (429, 503) and _attempt < _MAX_RETRIES:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            time.sleep(_retry_delay(retry_after, _attempt))
            return _http_get(
                url, timeout=timeout, email=email, accept=accept,
                _attempt=_attempt + 1,
            )
        raise SourceError(f"HTTP {exc.code} from {host}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if _attempt < _MAX_RETRIES:
            time.sleep(_retry_delay(None, _attempt))
            return _http_get(
                url, timeout=timeout, email=email, accept=accept,
                _attempt=_attempt + 1,
            )
        raise SourceError(f"Could not reach {host}: {exc}")


def _retry_delay(retry_after: str | None, attempt: int) -> float:
    """Seconds to wait before a retry: honour Retry-After, else backoff."""
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    return float(2 ** (attempt + 1))  # 2s, 4s, 8s


# --------------------------------------------------------------------------
# CrossRef
# --------------------------------------------------------------------------

def crossref_by_doi(doi: str, *, timeout: int = 20, email: str | None = None) -> Record | None:
    """Look up a DOI in CrossRef. Returns ``None`` if the DOI does not exist."""
    if not doi:
        return None
    params = {"mailto": email} if email else {}
    url = f"{CROSSREF_API}/{urllib.parse.quote(doi, safe='')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = _http_get(url, timeout=timeout, email=email, accept="application/json")
    if not body:
        return None
    try:
        message = json.loads(body)["message"]
    except (ValueError, KeyError) as exc:
        raise SourceError(f"Unexpected CrossRef response: {exc}")
    return _record_from_crossref(message)


def crossref_search(
    title: str,
    author: str | None = None,
    *,
    rows: int = 5,
    timeout: int = 20,
    email: str | None = None,
) -> list[Record]:
    """Search CrossRef by bibliographic title (and optionally first author)."""
    if not title:
        return []
    params = {"query.bibliographic": title, "rows": str(rows)}
    if author:
        params["query.author"] = author
    if email:
        params["mailto"] = email
    url = f"{CROSSREF_API}?{urllib.parse.urlencode(params)}"
    body = _http_get(url, timeout=timeout, email=email, accept="application/json")
    if not body:
        return []
    try:
        items = json.loads(body)["message"]["items"]
    except (ValueError, KeyError) as exc:
        raise SourceError(f"Unexpected CrossRef response: {exc}")
    return [_record_from_crossref(it) for it in items]


def _record_from_crossref(message: dict) -> Record:
    title_list = message.get("title") or [""]
    container = message.get("container-title") or [""]
    authors = []
    for a in message.get("author", []) or []:
        family = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        name = f"{family}, {given}".strip(", ") or (a.get("name") or "").strip()
        if name:
            authors.append(name)
    year = ""
    for key in ("published", "published-print", "published-online", "issued"):
        parts = (message.get(key) or {}).get("date-parts") or [[]]
        if parts and parts[0] and parts[0][0]:
            year = str(parts[0][0])
            break
    return Record(
        title=(title_list[0] or "").strip(),
        authors=authors,
        year=year,
        doi=(message.get("DOI") or "").lower(),
        container=(container[0] or "").strip(),
        source="crossref",
    )


# --------------------------------------------------------------------------
# arXiv
# --------------------------------------------------------------------------

def arxiv_lookup(arxiv_id: str, *, timeout: int = 20, email: str | None = None) -> Record | None:
    """Look up an arXiv identifier. Returns ``None`` if it does not exist."""
    if not arxiv_id:
        return None
    clean_id = arxiv_id.strip()
    url = f"{ARXIV_API}?{urllib.parse.urlencode({'id_list': clean_id, 'max_results': 1})}"
    body = _http_get(url, timeout=timeout, email=email, accept="application/atom+xml")
    if not body:
        return None
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceError(f"Unexpected arXiv response: {exc}")
    entry = root.find("a:entry", _ATOM)
    if entry is None:
        return None
    entry_id = (entry.findtext("a:id", default="", namespaces=_ATOM) or "")
    title = (entry.findtext("a:title", default="", namespaces=_ATOM) or "").strip()
    # arXiv returns a placeholder "Error" entry for identifiers that do not exist.
    if "api/errors" in entry_id or title.lower() == "error":
        return None
    authors = []
    for a in entry.findall("a:author", _ATOM):
        name = (a.findtext("a:name", default="", namespaces=_ATOM) or "").strip()
        if name:
            authors.append(name)
    published = entry.findtext("a:published", default="", namespaces=_ATOM) or ""
    doi = (entry.findtext("{http://arxiv.org/schemas/atom}doi", default="") or "").lower()
    return Record(
        title=" ".join(title.split()),
        authors=authors,
        year=published[:4],
        doi=doi,
        container="arXiv",
        source="arxiv",
    )
