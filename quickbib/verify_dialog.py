"""The "Verify References" dialog for the QuickBib desktop app.

Lets the user check a local ``.bib`` file or a live Overleaf project for
references that may be incorrect or do not exist. The actual checking is done
by the deterministic engine in :mod:`quickbib.verify` on a background thread;
this module is only the PyQt6 front-end.
"""

import threading
from html import escape
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .verify import (
    ERROR,
    MISMATCH,
    NOT_FOUND,
    REVIEW,
    STATUS_ICON,
    UNVERIFIED,
    VERIFIED,
    check_cite_keys,
    parse_bibtex,
    summary,
    verify_entries,
)
from .verify.overleaf import (
    OverleafError,
    clone_or_pull,
    find_bib_files,
    find_tex_files,
)

# Light row tints; paired with dark text so they stay legible in any theme.
_ROW_BG = {
    VERIFIED: QColor(216, 243, 220),
    REVIEW: QColor(208, 228, 248),
    MISMATCH: QColor(255, 236, 199),
    NOT_FOUND: QColor(250, 211, 211),
    UNVERIFIED: QColor(228, 228, 228),
    ERROR: QColor(228, 228, 228),
}
_ROW_FG = QColor(25, 25, 25)


class VerifyWorker(QObject):
    """Runs the verification engine off the UI thread."""

    progress = pyqtSignal(int, int)            # done, total
    finished = pyqtSignal(object, object, str)  # results, cite-result|None, label
    failed = pyqtSignal(str)

    def __init__(self, mode, *, bib_path="", project_id="", token=""):
        super().__init__()
        self.mode = mode
        self.bib_path = bib_path
        self.project_id = project_id
        self.token = token

    def run(self):
        try:
            entries, tex_sources, label = self._gather()
            if not entries:
                self.failed.emit(f"No BibTeX entries found in {label}.")
                return
            results = verify_entries(
                entries,
                progress=lambda d, t: self.progress.emit(d, t),
            )
            cite = None
            if tex_sources:
                cite = check_cite_keys(
                    tex_sources, {e.key for e in entries if e.key}
                )
            self.finished.emit(results, cite, label)
        except OverleafError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.failed.emit(f"Verification failed: {exc}")

    def _gather(self):
        if self.mode == "overleaf":
            repo = clone_or_pull(self.project_id, self.token)
            entries = []
            for bib in find_bib_files(repo):
                entries += parse_bibtex(_read(bib))
            tex_sources = [_read(t) for t in find_tex_files(repo)]
            return entries, tex_sources, f"Overleaf project {self.project_id}"
        text = _read(Path(self.bib_path))
        return parse_bibtex(text), [], self.bib_path


def _read(path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


class VerifyDialog(QDialog):
    """Modal dialog that drives reference verification and shows the report."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verify References - QuickBib")
        self.resize(780, 580)
        self._worker_thread = None

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.setLayout(layout)

        intro = QLabel(
            "Check every BibTeX reference against CrossRef and arXiv to catch "
            "DOIs that do not resolve, papers that cannot be found, and DOIs "
            "that point to the wrong article."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addWidget(self._build_source_tabs())

        action_row = QHBoxLayout()
        self.verify_btn = QPushButton("Verify References")
        self.verify_btn.clicked.connect(self.start_verification)
        action_row.addWidget(self.verify_btn)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        action_row.addWidget(self.progress, 1)
        layout.addLayout(action_row)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.summary_label)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Status", "Citation key", "Title"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._show_details)
        layout.addWidget(self.table, 2)

        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        self.details.setMinimumHeight(120)
        self.details.setPlaceholderText(
            "Select a reference above to see the full finding."
        )
        layout.addWidget(self.details, 1)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._results = []

    def _build_source_tabs(self) -> QTabWidget:
        self.source_tabs = QTabWidget()

        # --- Local .bib file -------------------------------------------------
        file_tab = QWidget()
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(8, 8, 8, 8)
        file_tab.setLayout(file_layout)
        file_layout.addWidget(QLabel("BibTeX file:"))
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Path to a .bib file")
        file_layout.addWidget(self.file_edit, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        file_layout.addWidget(browse_btn)
        self.source_tabs.addTab(file_tab, "BibTeX file")

        # --- Overleaf project ------------------------------------------------
        ol_tab = QWidget()
        ol_layout = QVBoxLayout()
        ol_layout.setContentsMargins(8, 8, 8, 8)
        ol_tab.setLayout(ol_layout)

        id_row = QHBoxLayout()
        id_row.addWidget(QLabel("Project ID:"))
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText(
            "from overleaf.com/project/<PROJECT_ID>"
        )
        id_row.addWidget(self.project_edit, 1)
        ol_layout.addLayout(id_row)

        token_row = QHBoxLayout()
        token_row.addWidget(QLabel("Git token:"))
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("olp_... (Account Settings -> Git)")
        token_row.addWidget(self.token_edit, 1)
        ol_layout.addLayout(token_row)

        hint = QLabel(
            "QuickBib reads the project over Overleaf's Git bridge. Create a "
            "token under Overleaf -> Account Settings -> Git Integration. The "
            "token is used locally and never stored."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")
        ol_layout.addWidget(hint)
        self.source_tabs.addTab(ol_tab, "Overleaf project")

        return self.source_tabs

    # ----------------------------------------------------------------- events

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select BibTeX file", "", "BibTeX files (*.bib);;All files (*)"
        )
        if path:
            self.file_edit.setText(path)

    def start_verification(self):
        if self.source_tabs.currentIndex() == 0:
            bib_path = self.file_edit.text().strip()
            if not bib_path or not Path(bib_path).is_file():
                self._set_summary("Please choose an existing .bib file.", error=True)
                return
            worker = VerifyWorker("file", bib_path=bib_path)
        else:
            project_id = self.project_edit.text().strip()
            token = self.token_edit.text().strip()
            if not project_id or not token:
                self._set_summary(
                    "Enter both the Overleaf project ID and Git token.",
                    error=True,
                )
                return
            worker = VerifyWorker(
                "overleaf",
                project_id=project_id,
                token=token,
            )

        self.verify_btn.setEnabled(False)
        self.table.setRowCount(0)
        self.details.clear()
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # indeterminate until first progress tick
        self._set_summary("Connecting and reading references...")

        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)

        thread = threading.Thread(target=worker.run, daemon=True)
        self._worker_thread = (worker, thread)
        thread.start()

    def _on_progress(self, done: int, total: int):
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self._set_summary(f"Verifying references... {done}/{total}")

    def _on_failed(self, message: str):
        self.progress.setVisible(False)
        self.verify_btn.setEnabled(True)
        self._worker_thread = None
        self._set_summary(message, error=True)

    def _on_finished(self, results, cite, label):
        self.progress.setVisible(False)
        self.verify_btn.setEnabled(True)
        self._worker_thread = None
        self._results = results
        self._populate_table(results)
        self._set_summary(self._summary_html(results, cite, label))

    # ------------------------------------------------------------- rendering

    def _populate_table(self, results):
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            cells = [
                STATUS_ICON.get(r.status, r.status),
                r.key,
                r.title or "(no title)",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setBackground(_ROW_BG.get(r.status, _ROW_BG[UNVERIFIED]))
                item.setForeground(_ROW_FG)
                if col == 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, col, item)
        if results:
            self.table.selectRow(0)

    def _show_details(self):
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            return
        r = self._results[min(rows)]
        parts = [
            f"<b>{escape(r.key)}</b> &mdash; "
            f"{escape(STATUS_ICON.get(r.status, r.status))}",
            f"<b>Title:</b> {escape(r.title or '(no title)')}",
            f"<b>Finding:</b> {escape(r.reason)}",
        ]
        for issue in r.issues:
            parts.append(f"&nbsp;&nbsp;&bull; {escape(issue)}")
        if r.matched_title:
            parts.append(
                f"<b>Closest record:</b> {escape(r.matched_title)}"
            )
        if r.matched_doi:
            doi = escape(r.matched_doi)
            parts.append(
                f'<b>DOI:</b> <a href="https://doi.org/{doi}">{doi}</a>'
            )
        if r.checked_via:
            parts.append(
                f"<i>Checked via {escape(r.checked_via)}, "
                f"confidence {r.confidence:.0%}.</i>"
            )
        self.details.setHtml("<br>".join(parts))

    def _summary_html(self, results, cite, label) -> str:
        counts = summary(results)
        hard = counts[MISMATCH] + counts[NOT_FOUND]
        if hard:
            head_color = "#b00020"
        elif counts[REVIEW] or counts[UNVERIFIED] or counts[ERROR]:
            head_color = "#9a6700"
        else:
            head_color = "#1a7f37"
        lines = [
            f'<span style="color:{head_color};"><b>{escape(label)}</b></span>',
            (
                f"Checked {counts['total']} references: "
                f"<b>{counts[VERIFIED]}</b> verified, "
                f"<b>{counts[REVIEW]}</b> review, "
                f'<b style="color:#b00020;">{counts[MISMATCH]}</b> mismatch, '
                f'<b style="color:#b00020;">{counts[NOT_FOUND]}</b> unresolved, '
                f"{counts[UNVERIFIED] + counts[ERROR]} unverified."
            ),
        ]
        if cite is not None and cite.undefined:
            lines.append(
                '<span style="color:#b00020;">Cited but undefined keys '
                "(possibly invented): "
                + escape(", ".join(sorted(cite.undefined)))
                + "</span>"
            )
        return "<br>".join(lines)

    def _set_summary(self, text: str, *, error: bool = False):
        if error:
            self.summary_label.setText(
                f'<span style="color:#b00020;">{escape(text)}</span>'
            )
        else:
            self.summary_label.setText(text)
