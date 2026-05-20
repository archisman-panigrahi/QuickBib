#!/usr/bin/env python3
"""Patch pyside6-android-deploy so CI can adjust generated buildozer.spec."""

from __future__ import annotations

from pathlib import Path
import re

import PySide6


MARKER = "# QuickBib CI buildozer.spec patch"
TARGET = 'logging.info("[DEPLOY] Running buildozer deployment")'
TARGET_RE = re.compile(rf"^(?P<indent>\s*){re.escape(TARGET)}$", re.MULTILINE)
PATCH_LINES = [
    MARKER,
    "import os as _quickbib_os",
    "from pathlib import Path as _QuickBibPath",
    "import re as _quickbib_re",
    "",
    "def _quickbib_set_buildozer_key(text, key, value):",
    '    pattern = rf"^#?{_quickbib_re.escape(key)}\\s*=.*$"',
    '    replacement = f"{key} = {value}"',
    "    if _quickbib_re.search(pattern, text, flags=_quickbib_re.MULTILINE):",
    "        return _quickbib_re.sub(pattern, replacement, text, count=1, flags=_quickbib_re.MULTILINE)",
    '    return text.rstrip() + f"\\n{replacement}\\n"',
    "",
    "def _quickbib_pin_requirement(text, requirement, pinned_requirement):",
    '    pattern = r"^(?P<prefix>#?requirements\\s*=\\s*)(?P<value>.*)$"',
    "    match = _quickbib_re.search(pattern, text, flags=_quickbib_re.MULTILINE)",
    "    if not match:",
    '        return text.rstrip() + f"\\nrequirements = {pinned_requirement}\\n"',
    '    parts = [part.strip() for part in match.group("value").split(",") if part.strip()]',
    "    replaced = False",
    "    for index, part in enumerate(parts):",
    '        if part == requirement or part.startswith(f"{requirement}=="):',
    "            parts[index] = pinned_requirement",
    "            replaced = True",
    "            break",
    "    if not replaced:",
    "        parts.insert(0, pinned_requirement)",
    '    replacement = match.group("prefix") + ",".join(parts)',
    "    return text[: match.start()] + replacement + text[match.end() :]",
    "",
    "def _quickbib_requirement_name(requirement):",
    '    match = _quickbib_re.match(r"\\s*([A-Za-z0-9_.-]+)", requirement)',
    "    return match.group(1).lower().replace('_', '-') if match else requirement",
    "",
    "def _quickbib_add_requirement(text, requirement):",
    '    pattern = r"^(?P<prefix>#?requirements\\s*=\\s*)(?P<value>.*)$"',
    "    match = _quickbib_re.search(pattern, text, flags=_quickbib_re.MULTILINE)",
    "    if not match:",
    '        return text.rstrip() + f"\\nrequirements = {requirement}\\n"',
    '    parts = [part.strip() for part in match.group("value").split(",") if part.strip()]',
    "    requirement_name = _quickbib_requirement_name(requirement)",
    "    for part in parts:",
    "        if _quickbib_requirement_name(part) == requirement_name:",
    "            return text",
    "    parts.append(requirement)",
    '    replacement = match.group("prefix") + ",".join(parts)',
    "    return text[: match.start()] + replacement + text[match.end() :]",
    "",
    "def _quickbib_android_requirements():",
    '    requirements = _QuickBibPath.cwd() / "requirements-android.txt"',
    "    if not requirements.exists():",
    "        return []",
    "    return [",
    "        line",
    "        for line in (line.strip() for line in requirements.read_text(encoding='utf-8').splitlines())",
    "        if line and not line.startswith('#')",
    "    ]",
    "",
    'for _quickbib_spec in _QuickBibPath.cwd().rglob("buildozer.spec"):',
    '    _quickbib_text = _quickbib_spec.read_text(encoding="utf-8")',
    '    _quickbib_arch = _quickbib_os.environ.get("TARGET_ARCH", "aarch64")',
    "    _quickbib_buildozer_arch = {",
    '        "aarch64": "arm64-v8a",',
    "    }.get(_quickbib_arch, _quickbib_arch)",
    "    for _quickbib_key, _quickbib_value in (",
    '        ("title", "QuickBib"),',
    '        ("package.name", "quickbib"),',
    '        ("package.domain", "io.github.archisman_panigrahi"),',
    '        ("version", "0.8.0"),',
    '        ("icon.filename", "assets/icon/192x192/io.github.archisman_panigrahi.QuickBib.png"),',
    '        ("orientation", "portrait"),',
    '        ("android.archs", _quickbib_buildozer_arch),',
    '        ("android.permissions", "INTERNET"),',
    "    ):",
    "        _quickbib_text = _quickbib_set_buildozer_key(",
    "            _quickbib_text,",
    "            _quickbib_key,",
    "            _quickbib_value,",
    "        )",
    '    _quickbib_python_version = _quickbib_os.environ.get("ANDROID_PYTHON_VERSION", "3.11.9")',
    "    _quickbib_text = _quickbib_pin_requirement(",
    "        _quickbib_text,",
    '        "python3",',
    '        f"python3=={_quickbib_python_version}",',
    "    )",
    "    _quickbib_text = _quickbib_pin_requirement(",
    "        _quickbib_text,",
    '        "hostpython3",',
    '        f"hostpython3=={_quickbib_python_version}",',
    "    )",
    "    for _quickbib_requirement in _quickbib_android_requirements():",
    "        _quickbib_text = _quickbib_add_requirement(",
    "            _quickbib_text,",
    "            _quickbib_requirement,",
    "        )",
    '    _quickbib_spec.write_text(_quickbib_text, encoding="utf-8")',
]


def main() -> None:
    deploy_py = Path(PySide6.__file__).resolve().parent / "scripts" / "android_deploy.py"
    text = deploy_py.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"{deploy_py} is already patched")
        return
    match = TARGET_RE.search(text)
    if not match:
        raise SystemExit(f"Could not find patch target in {deploy_py}")
    indent = match.group("indent")
    patch = "\n".join(indent + line if line else "" for line in PATCH_LINES)
    replacement = f"{patch}\n{match.group(0)}"
    deploy_py.write_text(
        text[: match.start()] + replacement + text[match.end() :],
        encoding="utf-8",
    )
    print(f"Patched {deploy_py}")


if __name__ == "__main__":
    main()
