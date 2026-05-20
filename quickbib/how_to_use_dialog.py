from .qt import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QLineEdit,
        QFont,
        QFontDatabase,
        Qt,
)

from .helpers import copy_to_clipboard
from .i18n import tr


class HowToUseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("examples.window_title"))
        self.resize(700, 460)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(8)
        self.setLayout(vbox)

        header = QLabel(tr("examples.header"))
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
            (tr("examples.label.doi"), "10.1038/nphys1170"),
            (tr("examples.label.doi_link"), "https://doi.org/10.1038/nphys1170"),
            (tr("examples.label.arxiv_url"), "https://arxiv.org/abs/2411.08091"),
            (tr("examples.label.arxiv_id"), "arXiv:2411.08091"),
            (tr("examples.label.arxiv_id_short"), "2411.08091"),
            (tr("examples.label.old_arxiv_id"), "hep-th/9901001"),
            (tr("examples.label.journal_url"), "https://journals.aps.org/prl/abstract/10.1103/v6r7-4ph9"),
            (tr("examples.label.title_fuzzy"), "Projected Topological Branes"),
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

            copy_btn = QPushButton(tr("button.copy"))
            copy_btn.setFixedHeight(26)
            copy_btn.clicked.connect(lambda _=False, t=text: copy_to_clipboard(t))
            row.addWidget(copy_btn)

            vbox.addLayout(row)

        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()
        close_btn = QPushButton(tr("button.close"))
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.reject)
        btn_hbox.addWidget(close_btn)
        vbox.addLayout(btn_hbox)
