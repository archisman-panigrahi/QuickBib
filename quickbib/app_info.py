from pathlib import Path
import sys

# Application metadata
APP_NAME = "QuickBib"
APP_VERSION = "0.9.6"
HOMEPAGE = "https://archisman-panigrahi.github.io/QuickBib/"
REPO_URL = "https://github.com/archisman-panigrahi/QuickBib"
WEBAPP_URL = "https://archisman-panigrahi.github.io/QuickBib/webapp"
ISSUES_URL = "https://github.com/archisman-panigrahi/QuickBib/issues"
ALGORITHM_VISUALS_URL = "https://github.com/archisman-panigrahi/doi2bib3/blob/main/docs/ALGORITHM_VISUALS.md#2-identifier-resolution-decision-tree"
# LICENSE is located in the repository root (one level up from the package dir)
# Use resolve().parent.parent so this works when the package is imported from
# an installed location or run from source.
LICENSE_PATH = Path(__file__).resolve().parent.parent / "LICENSE"
# Fallback: when running from a bundled EXE, LICENSE is alongside the executable
LICENSE_PATH_FALLBACK = Path(sys.executable).resolve().parent / "LICENSE"
