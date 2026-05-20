import json
import os
from pathlib import Path

from .qt import QLocale


_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_DEFAULT_LOCALE = "en"
_cache: dict[str, dict[str, str]] = {}


def _load_locale(locale_code: str) -> dict[str, str]:
    normalized = locale_code.replace("-", "_").lower()
    if normalized in _cache:
        return _cache[normalized]

    path = _LOCALES_DIR / f"{normalized}.json"
    if not path.exists():
        _cache[normalized] = {}
        return _cache[normalized]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    if not isinstance(data, dict):
        data = {}

    # Keep only string keys/values.
    cleaned: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            cleaned[key] = value

    _cache[normalized] = cleaned
    return cleaned


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


def tr(key: str, **kwargs) -> str:
    """
    Translate a key using JSON locale files.
    Falls back to English, then to the key itself if missing.
    """
    value: str | None = None
    for locale_code in _preferred_locales():
        table = _load_locale(locale_code)
        if key in table:
            value = table[key]
            break

    if value is None:
        value = key

    if kwargs:
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value
