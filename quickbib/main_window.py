import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QTextBrowser,
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QMenu,
    QTextEdit,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtGui import QAction, QPixmap, QFont, QIcon, QDesktopServices
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QUrl

from .helpers import get_bibtex_for_doi, copy_to_clipboard
from .about_dialog import AboutDialog
from .how_to_use_dialog import HowToUseDialog
from .app_info import LICENSE_PATH, WEBAPP_URL, ISSUES_URL
from .i18n import tr


class FetchWorker(QObject):
    finished = pyqtSignal(bool, str, object)  # found, bibtex, error

    def __init__(self, doi: str):
        super().__init__()
        self.doi = doi

    def run(self):
        try:
            found, bibtex, error = get_bibtex_for_doi(self.doi)
        except Exception as e:
            found, bibtex, error = False, "", str(e)
        self.finished.emit(found, bibtex, error)


class QuickBibWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("window.title"))
        self.setMinimumSize(320, 360)
        self._compact_breakpoint = 460
        self._is_compact_layout = None

        # Set up emoji font support
        self._emoji_font = self._setup_emoji_font()

        central = QWidget()
        self.setCentralWidget(central)

        vbox = QVBoxLayout()
        central.setLayout(vbox)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu(tr("menu.file"))
        quit_action = QAction(tr("action.quit"), self)
        quit_action.setFont(self._emoji_font)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu(tr("menu.edit"))
        copy_action = QAction(tr("action.copy_bibtex"), self)
        copy_action.setFont(self._emoji_font)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        help_menu = menubar.addMenu(tr("menu.help"))
        about_action = QAction(tr("action.about"), self)
        about_action.setFont(self._emoji_font)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        howto_action = QAction(tr("action.examples"), self)
        howto_action.setFont(self._emoji_font)
        howto_action.triggered.connect(self.show_how_to_use)
        help_menu.addAction(howto_action)

        help_menu.addSeparator()

        webapp_action = QAction(tr("action.webapp"), self)
        webapp_action.setFont(self._emoji_font)
        webapp_action.triggered.connect(lambda: self._open_url(WEBAPP_URL))
        help_menu.addAction(webapp_action)

        feedback_action = QAction(tr("action.feedback"), self)
        feedback_action.setFont(self._emoji_font)
        feedback_action.triggered.connect(lambda: self._open_url(ISSUES_URL))
        help_menu.addAction(feedback_action)

        self.mobile_menu_btn = QToolButton()
        self.mobile_menu_btn.setText("☰")
        self.mobile_menu_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.mobile_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.mobile_menu_btn.setStyleSheet("QToolButton::menu-indicator { width: 0px; image: none; }")

        mobile_menu = QMenu(self.mobile_menu_btn)
        mobile_menu.addAction(copy_action)
        mobile_menu.addSeparator()
        mobile_menu.addAction(about_action)
        mobile_menu.addAction(howto_action)
        mobile_menu.addSeparator()
        mobile_menu.addAction(webapp_action)
        mobile_menu.addAction(feedback_action)
        mobile_menu.addSeparator()
        mobile_menu.addAction(quit_action)
        self.mobile_menu_btn.setMenu(mobile_menu)

        # Quick links
        self.quick_links_widget = QWidget()
        quick_links = QHBoxLayout()
        quick_links.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        quick_links.setContentsMargins(0, 0, 0, 0)
        quick_links.setSpacing(6)
        self.quick_links_widget.setLayout(quick_links)
        vbox.addWidget(self.quick_links_widget)

        webapp_btn = QPushButton(tr("button.webapp"))
        webapp_btn.setFont(self._emoji_font)
        webapp_btn.clicked.connect(lambda: self._open_url(WEBAPP_URL))
        quick_links.addWidget(webapp_btn)

        howto_btn = QPushButton(tr("button.examples"))
        howto_btn.setFont(self._emoji_font)
        howto_btn.clicked.connect(self.show_how_to_use)
        quick_links.addWidget(howto_btn)

        feedback_btn = QPushButton(tr("button.feedback"))
        feedback_btn.setFont(self._emoji_font)
        feedback_btn.clicked.connect(lambda: self._open_url(ISSUES_URL))
        quick_links.addWidget(feedback_btn)

        vbox.addSpacing(8)

        # DOI entry
        self.entry_box = QHBoxLayout()
        vbox.addLayout(self.entry_box)

        self.doi_header_row = QWidget()
        self.doi_header_layout = QHBoxLayout()
        self.doi_header_layout.setContentsMargins(0, 0, 0, 0)
        self.doi_header_row.setLayout(self.doi_header_layout)
        self.entry_box.addWidget(self.doi_header_row)

        self.doi_label = QLabel(tr("label.doi"))
        self.doi_header_layout.addWidget(self.doi_label)
        self.doi_header_layout.addStretch(1)
        self.doi_header_layout.addWidget(self.mobile_menu_btn)

        self.doi_entry = QLineEdit()
        self.doi_entry.setPlaceholderText(tr("placeholder.query"))
        self.entry_box.addWidget(self.doi_entry)
        # Trigger fetch when user presses Enter in the DOI entry
        self.doi_entry.returnPressed.connect(self.fetch_bibtex)

        self.fetch_btn = QPushButton(tr("button.fetch"))
        self.fetch_btn.clicked.connect(self.fetch_bibtex)
        self.entry_box.addWidget(self.fetch_btn)

        # Status label
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status.setTextFormat(Qt.TextFormat.RichText)
        self.status.setWordWrap(True)
        vbox.addWidget(self.status)

        # Text view
        self.textview = QTextEdit()
        self.textview.setReadOnly(True)
        self.textview.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.textview.setMinimumHeight(180)
        vbox.addWidget(self.textview, 1)

        # Buttons (fixed-height bar so it won't overlap the output area on short windows)
        self.btn_widget = QWidget()
        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        btn_box.setContentsMargins(0, 0, 0, 0)
        btn_box.setSpacing(8)
        self.btn_widget.setLayout(btn_box)
        self.btn_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Slightly smaller fixed height to reduce vertical margin
        self.btn_widget.setFixedHeight(24)
        vbox.addWidget(self.btn_widget)

        self.copy_btn = QPushButton(tr("button.copy_clipboard"))
        self.copy_btn.setFont(self._emoji_font)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_box.addWidget(self.copy_btn)

        self._apply_responsive_layout(self.width())
        self.resize(500, 400)

        # Keep references to worker/thread so they don't get GC'd
        self._worker_thread = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout(event.size().width())

    def _apply_responsive_layout(self, width: int) -> None:
        compact = width < self._compact_breakpoint
        if compact == self._is_compact_layout:
            return

        self._is_compact_layout = compact

        self.entry_box.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact
            else QBoxLayout.Direction.LeftToRight
        )

        if compact:
            self.menuBar().setVisible(False)
            self.mobile_menu_btn.setVisible(True)
            self.quick_links_widget.setVisible(False)
            self.doi_header_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.doi_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.copy_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.doi_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.menuBar().setVisible(True)
            self.mobile_menu_btn.setVisible(False)
            self.quick_links_widget.setVisible(True)
            self.doi_header_row.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self.doi_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.copy_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.doi_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _setup_emoji_font(self):
        """Set up a font with good emoji support across different desktop environments."""
        # Emoji font families with fallbacks (order matters)
        emoji_fonts = [
            "Noto Color Emoji",  # Best cross-platform emoji support
            "Noto Emoji",
            "Apple Color Emoji",  # macOS
            "Segoe UI Emoji",  # Windows
            "DejaVu Sans",  # Good Linux support
        ]
        
        # Get the system default font and preserve its size
        default_font = QFont()
        font_size = default_font.pointSize()
        
        font = QFont()
        font.setPointSize(font_size)
        
        # Try to set the font family with fallbacks
        font.setFamilies(emoji_fonts)
        return font

    def _format_status_with_emoji(self, text: str) -> str:
        """Format status text with emoji characters using emoji font."""
        # Find emoji characters and wrap them in HTML with emoji font
        emoji_list = "✅📋🌐💬ℹ️"
        emoji_font_families = "Noto Color Emoji, Noto Emoji, Apple Color Emoji, Segoe UI Emoji, DejaVu Sans"
        
        result = text
        for emoji in emoji_list:
            if emoji in result:
                result = result.replace(
                    emoji,
                    f'<span style="font-family: {emoji_font_families}">{emoji}</span>'
                )
        return result

    def _open_url(self, url: str) -> None:
        """Open an external URL in the user's default browser."""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            self.status.setText(self._format_status_with_emoji(tr("status.link_open_failed")))

    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def show_how_to_use(self):
        dlg = HowToUseDialog(self)
        dlg.exec()

    def fetch_bibtex(self):
        doi = self.doi_entry.text().strip()
        if not doi:
            self.status.setText(self._format_status_with_emoji(tr("status.enter_valid_doi")))
            return

        self.status.setText(tr("status.fetching"))
        self.textview.clear()

        worker = FetchWorker(doi)

        def thread_target():
            worker.run()

        worker.finished.connect(self.on_fetch_finished)

        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

        self._worker_thread = (worker, t)

    def on_fetch_finished(self, found: bool, bibtex: str, error: object):
        if found:
            self.textview.setPlainText(bibtex)
            self.status.setText(self._format_status_with_emoji(tr("status.fetch_success")))
        else:
            self.textview.clear()
            if error:
                self.status.setText(self._format_status_with_emoji(tr("status.error", error=error)))
            else:
                self.status.setText(self._format_status_with_emoji(tr("status.error_not_found")))

        self._worker_thread = None

    def copy_to_clipboard(self):
        text = self.textview.toPlainText()
        if text.strip():
            ok = copy_to_clipboard(text)
            if ok:
                self.status.setText(self._format_status_with_emoji(tr("status.copy_success")))
            else:
                self.status.setText(self._format_status_with_emoji(tr("status.copy_failed")))
        else:
            self.status.setText(self._format_status_with_emoji(tr("status.nothing_to_copy")))
