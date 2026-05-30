from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QLineEdit,
)
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt

from .helpers import copy_to_clipboard
from .i18n import tr


class HowToUseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Example inputs for QuickBib'))
        self.resize(700, 460)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(8)
        self.setLayout(vbox)

        header = QLabel(tr('Examples of what you can paste into QuickBib main window:'))
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        vbox.addWidget(header)

        # Intro text removed: examples are shown below as individual code widgets

        # Show individual example items as monospace, read-only code widgets
        # Choose a reliable monospace font: prefer system fixed font, fall back to Courier New
        try:
            code_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
            code_font.setPointSize(10)
        except Exception:
            code_font = QFont("Courier New", 10)

        # Ensure the font is treated as monospace/fixed-pitch
        code_font.setStyleHint(QFont.StyleHint.Monospace)
        code_font.setFixedPitch(True)

        examples = [
            (tr('DOI'), "10.1038/nphys1170"),
            (tr('DOI link'), "https://doi.org/10.1038/nphys1170"),
            (tr('arXiv URL'), "https://arxiv.org/abs/2411.08091"),
            (tr('arXiv ID'), "arXiv:2411.08091"),
            (tr('arXiv ID (short)'), "2411.08091"),
            (tr('Old arXiv ID'), "hep-th/9901001"),
            (tr('Journal URL (works with APS, AMS, ACS, PNAS, Nature, ScienceDirect...)'), "https://journals.aps.org/prl/abstract/10.1103/v6r7-4ph9"),
            (tr('Title (fuzzy search)'), "Projected Topological Branes"),
        ]

        # Create compact copyable boxes for each example
        for label_text, example_text in examples:
            lbl = QLabel(label_text)
            vbox.addWidget(lbl)
            text = example_text.strip()

            row = QHBoxLayout()
            field = QLineEdit()
            field.setReadOnly(True)
            field.setFont(code_font)
            field.setText(text)
            field.setMinimumHeight(26)
            row.addWidget(field, 1)

            copy_btn = QPushButton(tr('Copy'))
            copy_btn.setFixedHeight(26)
            copy_btn.clicked.connect(lambda _=False, t=text: copy_to_clipboard(t))
            row.addWidget(copy_btn)

            vbox.addLayout(row)

        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()
        close_btn = QPushButton(tr('✕ Close'))
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.reject)
        btn_hbox.addWidget(close_btn)
        vbox.addLayout(btn_hbox)
