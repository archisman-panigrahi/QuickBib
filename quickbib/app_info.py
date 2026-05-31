from pathlib import Path
import sys

# Application metadata
APP_NAME = "QuickBib"
APP_VERSION = "0.8.1"
HOMEPAGE = "https://archisman-panigrahi.github.io/QuickBib/"
REPO_URL = "https://github.com/archisman-panigrahi/QuickBib"
WEBAPP_URL = "https://quickbib.streamlit.app/"
ISSUES_URL = "https://github.com/archisman-panigrahi/QuickBib/issues"
# LICENSE is located in the repository root (one level up from the package dir)
# Use resolve().parent.parent so this works when the package is imported from
# an installed location or run from source.
LICENSE_PATH = Path(__file__).resolve().parent.parent / "LICENSE"
# Fallback: when running from a bundled EXE, LICENSE is alongside the executable
LICENSE_PATH_FALLBACK = Path(sys.executable).resolve().parent / "LICENSE"
