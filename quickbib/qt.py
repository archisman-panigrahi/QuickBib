"""Qt binding compatibility layer.

QuickBib is developed against the common Qt for Python API. Desktop builds can
keep using PyQt6, while Android builds use PySide6 through the same imports.
"""

from __future__ import annotations

import os


_REQUESTED_API = os.environ.get("QUICKBIB_QT_API", "").strip().lower()


def _use_pyside() -> bool:
    return _REQUESTED_API in {"pyside", "pyside6"}


if _use_pyside():
    from PySide6.QtCore import QLocale, QObject, Qt, QUrl, Signal
    from PySide6.QtGui import (
        QAction,
        QDesktopServices,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QIcon,
        QPixmap,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QBoxLayout,
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QTabWidget,
        QTextBrowser,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PyQt6.QtCore import QLocale, QObject, Qt, QUrl, pyqtSignal as Signal
        from PyQt6.QtGui import (
            QAction,
            QDesktopServices,
            QFont,
            QFontDatabase,
            QGuiApplication,
            QIcon,
            QPixmap,
        )
        from PyQt6.QtWidgets import (
            QApplication,
            QBoxLayout,
            QDialog,
            QFrame,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMenu,
            QMessageBox,
            QPushButton,
            QSizePolicy,
            QTabWidget,
            QTextBrowser,
            QTextEdit,
            QToolButton,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        from PySide6.QtCore import QLocale, QObject, Qt, QUrl, Signal
        from PySide6.QtGui import (
            QAction,
            QDesktopServices,
            QFont,
            QFontDatabase,
            QGuiApplication,
            QIcon,
            QPixmap,
        )
        from PySide6.QtWidgets import (
            QApplication,
            QBoxLayout,
            QDialog,
            QFrame,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMenu,
            QMessageBox,
            QPushButton,
            QSizePolicy,
            QTabWidget,
            QTextBrowser,
            QTextEdit,
            QToolButton,
            QVBoxLayout,
            QWidget,
        )
