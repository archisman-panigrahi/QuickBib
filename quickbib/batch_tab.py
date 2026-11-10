import threading

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QProgressBar,
    QFileDialog,
)
from PyQt6.QtCore import QObject, pyqtSignal
from doi2bib3 import fetch_bibtex
from doi2bib3.io import save_bibtex_to_file

from .i18n import tr


class BatchWorker(QObject):
    """Does what ``doi2bib3 --input FILE --output OUT`` does, on a background
    thread, reporting each entry and stopping early if cancelled."""

    item_done = pyqtSignal(str, object)  # query, error (None on success)
    finished = pyqtSignal(int, int)  # saved, failed

    def __init__(self, queries, output_path, mbox):
        super().__init__()
        self.queries, self.output_path, self.mbox = queries, output_path, mbox
        self.cancelled = threading.Event()

    def run(self):
        saved = failed = 0
        for query in self.queries:
            if self.cancelled.is_set():
                break
            try:
                bibtex = fetch_bibtex(query, mbox=self.mbox)
                # The first entry replaces the file, later ones are appended
                save_bibtex_to_file(bibtex, self.output_path, append=saved > 0)
                saved += 1
                self.item_done.emit(query, None)
            except Exception as e:
                failed += 1
                self.item_done.emit(query, str(e))
        self.finished.emit(saved, failed)


class BatchTab(QWidget):
    """Turn a text file of DOIs/arXiv IDs/URLs/titles into one .bib file."""

    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout(self)

        hint = QLabel(tr('Text file with one DOI, arXiv ID, URL or title per line. Blank lines and lines starting with # are ignored.'))
        hint.setWordWrap(True)
        vbox.addWidget(hint)

        self.input_entry = self._file_row(vbox, tr('Input file:'), self.choose_input)
        self.output_entry = self._file_row(vbox, tr('Output .bib file:'), self.choose_output)

        self.mbox_checkbox = QCheckBox(tr('Prevent line breaks in author names'))
        vbox.addWidget(self.mbox_checkbox)

        self.start_btn = QPushButton(tr('Start'))
        self.start_btn.clicked.connect(self.start_or_cancel)
        vbox.addWidget(self.start_btn)

        self.progress = QProgressBar()
        self.progress.setFormat("%v / %m")
        vbox.addWidget(self.progress)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        vbox.addWidget(self.status)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        vbox.addWidget(self.log_view, 1)

        self._worker = None

    def _file_row(self, vbox, label, choose):
        vbox.addWidget(QLabel(label))
        row = QHBoxLayout()
        entry = QLineEdit()
        entry.setReadOnly(True)
        button = QPushButton(tr('Browse…'))
        button.clicked.connect(choose)
        row.addWidget(entry, 1)
        row.addWidget(button)
        vbox.addLayout(row)
        return entry

    def choose_input(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('Input file:'))
        if path:
            self.input_entry.setText(path)

    def choose_output(self):
        # The native save dialog already asks before overwriting a file
        path, _ = QFileDialog.getSaveFileName(self, tr('Output .bib file:'), "references.bib", "BibTeX (*.bib)")
        if path:
            self.output_entry.setText(path if path.endswith(".bib") else path + ".bib")

    def start_or_cancel(self):
        if self._worker:
            self._worker.cancelled.set()
            self.start_btn.setEnabled(False)
            return

        if not self.input_entry.text() or not self.output_entry.text():
            self.status.setText(tr('Please choose an input file and an output .bib file.'))
            return
        try:
            with open(self.input_entry.text(), encoding="utf-8-sig") as fh:
                queries = [s for s in map(str.strip, fh) if s and not s.startswith("#")]
        except Exception as e:
            self.status.setText(str(e))
            return

        self.log_view.clear()
        self.status.clear()
        self.progress.setRange(0, len(queries))
        self.progress.setValue(0)
        self.start_btn.setText(tr('Cancel'))

        self._worker = BatchWorker(queries, self.output_entry.text(), self.mbox_checkbox.isChecked())
        self._worker.item_done.connect(self._on_item_done)
        self._worker.finished.connect(self._on_finished)
        threading.Thread(target=self._worker.run, daemon=True).start()

    def _on_item_done(self, query, error):
        self.log_view.appendPlainText(f"✅ {query}" if error is None else f"❌ {query}: {error}")
        self.progress.setValue(self.progress.value() + 1)

    def _on_finished(self, saved, failed):
        path, self._worker = self._worker.output_path, None
        self.start_btn.setText(tr('Start'))
        self.start_btn.setEnabled(True)
        self.status.setText(tr('Saved {saved} entries to {path}. {failed} failed.', saved=saved, path=path, failed=failed))
