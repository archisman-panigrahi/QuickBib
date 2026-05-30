import os
from pathlib import Path

from PyQt6.QtCore import QLocale


_PO_DIR = Path(__file__).resolve().parent / "po"
_DEFAULT_LOCALE = "en"
_cache: dict[str, dict[str, str]] = {}


def _unescape_po_string(value: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(value):
        char = value[i]
        if char != "\\" or i + 1 >= len(value):
            result.append(char)
            i += 1
            continue

        escaped = value[i + 1]
        result.append({
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "\\": "\\",
            '"': '"',
        }.get(escaped, escaped))
        i += 2
    return "".join(result)


def _parse_po_string(line: str) -> str | None:
    start = line.find('"')
    end = line.rfind('"')
    if start == -1 or end <= start:
        return None
    return _unescape_po_string(line[start + 1:end])


def _load_po(path: Path) -> dict[str, str]:
    translations: dict[str, str] = {}
    current_field: str | None = None
    current: dict[str, str] = {}

    def commit() -> None:
        msgid = current.get("msgid")
        msgstr = current.get("msgstr")
        if msgid and msgstr is not None:
            translations[msgid] = msgstr

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            commit()
            current = {}
            current_field = None
            continue
        if line.startswith("#"):
            continue

        for field in ("msgid", "msgstr"):
            if line.startswith(field):
                current_field = field
                current[field] = _parse_po_string(line) or ""
                break
        else:
            if line.startswith('"') and current_field:
                current[current_field] += _parse_po_string(line) or ""

    commit()
    return translations


def _load_locale(locale_code: str) -> dict[str, str]:
    normalized = locale_code.replace("-", "_").lower()
    if normalized in _cache:
        return _cache[normalized]

    path = _PO_DIR / normalized / "LC_MESSAGES" / "quickbib.po"
    if not path.exists():
        _cache[normalized] = {}
        return _cache[normalized]

    try:
        data = _load_po(path)
    except Exception:
        data = {}

    _cache[normalized] = data
    return data


def _preferred_locales() -> list[str]:
    normalized = ""
    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(env_var, "").strip()
        if not raw:
            continue
        # Handle values like en_US.UTF-8@variant
        normalized = raw.split(".", 1)[0].split("@", 1)[0].replace("-", "_").lower()
        break

    if not normalized:
        normalized = QLocale.system().name().replace("-", "_").lower()

    langs: list[str] = []
    if normalized:
        langs.append(normalized)
        base = normalized.split("_", 1)[0]
        if base and base != normalized:
            langs.append(base)
    if _DEFAULT_LOCALE not in langs:
        langs.append(_DEFAULT_LOCALE)
    return langs


def tr(message: str, **kwargs) -> str:
    """
    Translate an English source string using PO locale files.
    Falls back to the English source string if missing.
    """
    value: str | None = None
    for locale_code in _preferred_locales():
        table = _load_locale(locale_code)
        if message in table:
            value = table[message]
            break

    if value is None:
        value = message

    if kwargs:
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value
