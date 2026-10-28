#!/usr/bin/env python3
from doi2bib3 import fetch_bibtex, format_bibtex_to_aps_bibitem
from doi2bib3._bibtex import dump_entries, parse_entries
from doi2bib3.normalize import protect_author_surnames


def get_bibtex_for_doi(doi: str):
    try:
        bibtex = fetch_bibtex(doi)
        return True, bibtex, None
    except Exception as e:
        return False, "", str(e)


def protect_bibtex_author_names(bibtex: str) -> str:
    """Wrap author surnames in \\mbox{} so LaTeX never breaks them across lines."""
    entries = parse_entries(bibtex)
    for entry in entries:
        if "author" in entry:
            entry["author"] = protect_author_surnames(entry["author"])
    return dump_entries(entries)


def get_aps_bibitem_for_bibtex(bibtex: str, mbox: bool = False) -> tuple[bool, str, str | None]:
    try:
        bibitem = format_bibtex_to_aps_bibitem(bibtex, mbox=mbox)
        return True, bibitem, None
    except Exception as e:
        return False, "", str(e)


def copy_to_clipboard(text: str) -> bool:
    try:
        from PyQt6.QtGui import QGuiApplication

        app = QGuiApplication.instance()
        if app is None:
            return False
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        return True
    except Exception:
        return False
