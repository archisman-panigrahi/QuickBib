#!/usr/bin/env python3

import sys
from pathlib import Path
import signal
from .qt import QApplication, QIcon

from .app_info import APP_NAME, APP_VERSION, HOMEPAGE, REPO_URL, LICENSE_PATH
from .main_window import QuickBibWindow


def main(argv):
    app = QApplication(argv)
    # Only set desktop/WM hints on Linux. Windows and macOS do not use
    # desktop files and may behave differently; restrict the change to
    # avoid affecting those platforms.
    try:
        import platform as _platform
        import sys as _sys
        is_linux = _sys.platform.startswith("linux") or _platform.system().lower() == "linux"
        if is_linux:
            # Application name used by Qt for window class and other places
            app.setApplicationName("QuickBib")
            # Hint the desktop file name (without the .desktop suffix).
            # On some platforms KDE/Plasma uses this to match the running
            # app to the launcher entry. This API may not be available on
            # older bindings, so check for it.
            if hasattr(app, 'setDesktopFileName'):
                try:
                    app.setDesktopFileName('io.github.archisman_panigrahi.QuickBib')
                except Exception:
                    # Ignore failures; it's a best-effort hint.
                    pass
    except Exception:
        # Be conservative: if anything fails, continue without crashing.
        pass
    try:
        theme_icon = QIcon.fromTheme("io.github.archisman_panigrahi.QuickBib")
        if not theme_icon.isNull():
            app.setWindowIcon(theme_icon)
        else:
            # assets are installed under share/quickbib/assets
            asset_path = Path(__file__).parent.parent / "assets" / "icon" / "64x64" / "io.github.archisman_panigrahi.QuickBib.png"
            if asset_path.exists():
                app.setWindowIcon(QIcon(str(asset_path)))
    except Exception:
        pass
    win = QuickBibWindow()
    win.show()
    # Set SIGINT to default so Ctrl+C produces KeyboardInterrupt.
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except Exception:
        pass
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
