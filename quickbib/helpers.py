#!/usr/bin/env python3
from doi2bib3 import fetch_bibtex


def get_bibtex_for_doi(doi: str):
    try:
        bibtex = fetch_bibtex(doi)
        return True, bibtex, None
    except Exception as e:
        return False, "", str(e)


def copy_to_clipboard(text: str) -> bool:
    try:
        from .qt import QGuiApplication

        app = QGuiApplication.instance()
        if app is None:
            return False
        cb = QGuiApplication.clipboard()
        cb.setText(text)
        return True
    except Exception:
        return False
