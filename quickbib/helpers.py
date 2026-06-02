#!/usr/bin/env python3
from doi2bib3 import fetch_bibtex, format_bibtex_to_aps_bibitem


def get_bibtex_for_doi(doi: str):
    try:
        bibtex = fetch_bibtex(doi)
        return True, bibtex, None
    except Exception as e:
        return False, "", str(e)


def get_aps_bibitem_for_bibtex(bibtex: str) -> tuple[bool, str, str | None]:
    try:
        bibitem = format_bibtex_to_aps_bibitem(bibtex)
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
