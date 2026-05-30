from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt

from .app_info import APP_NAME, APP_VERSION, HOMEPAGE, REPO_URL, LICENSE_PATH, LICENSE_PATH_FALLBACK, WEBAPP_URL, ISSUES_URL
from .i18n import tr


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('About QuickBib'))
        self.resize(600, 420)
        # Match minimum width to the main app minimum (320)
        self.setMinimumWidth(320)

        # Main layout
        vbox = QVBoxLayout()
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(12)
        self.setLayout(vbox)

        # Header: icon + title
        header = QHBoxLayout()
        header.setSpacing(12)
        vbox.addLayout(header)

        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setScaledContents(True)
        try:
            theme_icon = QIcon.fromTheme("io.github.archisman_panigrahi.QuickBib")
            if not theme_icon.isNull():
                pix = theme_icon.pixmap(64, 64)
            else:
                asset_path = Path(__file__).parent.parent / "assets" / "icon" / "64x64" / "io.github.archisman_panigrahi.QuickBib.png"
                if asset_path.exists():
                    pix = QPixmap(str(asset_path))
                    if pix.isNull():
                        pix = QPixmap()
                else:
                    pix = QPixmap()
        except Exception:
            pix = QPixmap()
        icon_label.setPixmap(pix)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_label = QLabel(f"{APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)

        subtitle = QLabel(tr('Version {version}', version=APP_VERSION))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(subtitle)

        header.addLayout(title_layout)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setObjectName("aboutFrame")
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame.setLayout(frame_layout)
        vbox.addWidget(frame)

        tabs = QTabWidget()
        frame_layout.addWidget(tabs)

        about_text = QTextBrowser()
        translations_welcome = tr(
            '<b>Translations:</b> Want to help translate QuickBib? Improve an existing translation or add a new language on the <a href="{repo_url}">project\'s GitHub page</a>. Not sure how to start? Open an issue on <a href="{issues_url}">GitHub</a>!',
            repo_url=REPO_URL, issues_url=ISSUES_URL,
        )
        about_html = f"""
        <p>{tr('{app_name} fetches BibTeX entries from DOIs, arXiv IDs, and known journal URLs. It is a simple utility to quickly convert identifiers into usable BibTeX records.', app_name=APP_NAME)}</p>
        <p>{tr('QuickBib uses <a href="https://github.com/archisman-panigrahi/doi2bib3">doi2bib3</a> as its backend for DOI to BibTeX conversion.')}</p>
        <p>
          {tr('<b>Homepage:</b> <a href="{homepage}">{homepage}</a><br><b>Source Code:</b> <a href="{repo_url}">{repo_url}</a><br><b>Report Issues:</b> <a href="{issues_url}">{issues_url}</a><br><br><b>Web app:</b> Check it out <a href="{webapp_url}">here</a>.', homepage=HOMEPAGE, repo_url=REPO_URL, issues_url=ISSUES_URL, webapp_url=WEBAPP_URL)}
        </p>
        <p>{translations_welcome}</p>
        <p>{tr('<b>License:</b> Released under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html#license-text">GNU General Public License Version 3</a>. Full text available on the <i>License</i> tab.')}</p>
        """
        about_text.setHtml(about_html)
        about_text.setOpenExternalLinks(True)
        tabs.addTab(about_text, tr('About'))

        authors_text = QTextBrowser()
        prs_welcome = tr(
            'Bug reports and pull requests are welcome on the <a href="{repo_url}">project\'s GitHub page</a>.',
            repo_url=REPO_URL,
        )
        authors_html = f"""
        <h3>{tr('Authors')}</h3>
        <ul>
          <li><a href="https://github.com/archisman-panigrahi/">Archisman Panigrahi</a></li>
        </ul>
        <h3>{tr(' Significant Contributors')}</h3>
        <ul>
          <li>{tr('<a href="https://github.com/Kyuyrii/">Kyuyrii</a>: Helped fix the snap package.')}</li>
        </ul>
        <p>{tr('This project was inspired by <a href="https://github.com/bibcure/doi2bib">doi2bib</a>, whose development unfortunately stopped.')}</p>
        <p>{tr('This project would not have been possible without the help from GitHub Copilot.')}</p>
        <p>{prs_welcome}</p>
        """
        authors_text.setHtml(authors_html)
        authors_text.setOpenExternalLinks(True)
        tabs.addTab(authors_text, tr('Authors'))

        translators_text = QTextBrowser()
        translators_html = """
        <ul>
          <li>Archisman Panigrahi (অর্চিষ্মান পাণিগ্রাহী) — Bangla</li>
          <li>YanMing (焱铭) — Simplified Chinese</li>
        </ul>
        """
        translators_text.setHtml(translators_html)
        translators_text.setOpenExternalLinks(True)
        tabs.addTab(translators_text, tr('Translators'))

        license_text = QTextBrowser()
        if LICENSE_PATH.exists() or LICENSE_PATH_FALLBACK.exists():
            license_file = LICENSE_PATH if LICENSE_PATH.exists() else LICENSE_PATH_FALLBACK
            try:
                license_content = license_file.read_text(encoding="utf-8")
                license_text.setPlainText(license_content)
            except Exception:
                license_text.setHtml(tr('<p>Unable to read LICENSE file.</p>'))
        else:
            license_text.setHtml(tr('<p>GPLv3 license text not found in repository. See the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html#license-text">Read it online</a>.</p>'))
        tabs.addTab(license_text, tr('License'))

        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch()

        dedication = QLabel(tr('<em>Dedicated to all my friends 😊</em>'))
        dedication.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dedication.setMinimumWidth(240)
        btn_hbox.addWidget(dedication)

        btn_hbox.addStretch()
        close_btn = QPushButton(tr('✕ Close'))
        close_btn.clicked.connect(self.reject)
        close_btn.setFixedHeight(28)
        btn_hbox.addWidget(close_btn)
        vbox.addLayout(btn_hbox)
