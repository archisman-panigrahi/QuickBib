#!/usr/bin/env python3
"""Patch pyside6-android-deploy so CI can adjust generated buildozer.spec."""

from __future__ import annotations

from pathlib import Path
import re

import PySide6


MARKER = "# QuickBib CI buildozer.spec patch"
TARGET = 'logging.info("[DEPLOY] Running buildozer deployment")'
PATCH = f'''
    {MARKER}
    import os as _quickbib_os
    from pathlib import Path as _QuickBibPath
    import re as _quickbib_re

    def _quickbib_set_buildozer_key(text, key, value):
        pattern = rf"^#?{{_quickbib_re.escape(key)}}\\s*=.*$"
        replacement = f"{{key}} = {{value}}"
        if _quickbib_re.search(pattern, text, flags=_quickbib_re.MULTILINE):
            return _quickbib_re.sub(pattern, replacement, text, count=1, flags=_quickbib_re.MULTILINE)
        return text.rstrip() + f"\\n{{replacement}}\\n"

    for _quickbib_spec in _QuickBibPath.cwd().rglob("buildozer.spec"):
        _quickbib_text = _quickbib_spec.read_text(encoding="utf-8")
        _quickbib_arch = _quickbib_os.environ.get("TARGET_ARCH", "aarch64")
        _quickbib_buildozer_arch = {{
            "armv7a": "armeabi-v7a",
        }}.get(_quickbib_arch, _quickbib_arch)
        for _quickbib_key, _quickbib_value in (
            ("title", "QuickBib"),
            ("package.name", "quickbib"),
            ("package.domain", "io.github.archisman_panigrahi"),
            ("version", "0.8.0"),
            ("icon.filename", "assets/icon/192x192/io.github.archisman_panigrahi.QuickBib.png"),
            ("orientation", "portrait"),
            ("android.archs", _quickbib_buildozer_arch),
            ("android.permissions", "INTERNET"),
        ):
            _quickbib_text = _quickbib_set_buildozer_key(
                _quickbib_text,
                _quickbib_key,
                _quickbib_value,
            )
        _quickbib_spec.write_text(_quickbib_text, encoding="utf-8")
'''


def main() -> None:
    deploy_py = Path(PySide6.__file__).resolve().parent / "scripts" / "android_deploy.py"
    text = deploy_py.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"{deploy_py} is already patched")
        return
    if TARGET not in text:
        raise SystemExit(f"Could not find patch target in {deploy_py}")
    deploy_py.write_text(text.replace(TARGET, PATCH + "\n" + TARGET, 1), encoding="utf-8")
    print(f"Patched {deploy_py}")


if __name__ == "__main__":
    main()
