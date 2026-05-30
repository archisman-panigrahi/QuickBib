#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "quickbib"
PO_DIR = SOURCE_DIR / "po"
DOMAIN = "quickbib"
BASE_LOCALE = "en"
BASE_FILE = PO_DIR / BASE_LOCALE / "LC_MESSAGES" / f"{DOMAIN}.po"
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class PoEntry:
    msgid: str
    msgstr: str
    references: list[str] = field(default_factory=list)


def _unescape_po_string(value: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(value):
        char = value[i]
        if char != "\\" or i + 1 >= len(value):
            result.append(char)
            i += 1
            continue

        escaped = value[i + 1]
        result.append({
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "\\": "\\",
            '"': '"',
        }.get(escaped, escaped))
        i += 2
    return "".join(result)


def _escape_po_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def _parse_po_string(line: str, path: Path, line_number: int) -> str:
    start = line.find('"')
    end = line.rfind('"')
    if start == -1 or end <= start:
        raise ValueError(f"{path}:{line_number}: expected quoted PO string")
    return _unescape_po_string(line[start + 1:end])


def _po_line(field: str, value: str) -> str:
    return f'{field} "{_escape_po_string(value)}"'


def _load_po(path: Path) -> tuple[list[str], dict[str, PoEntry]]:
    if not path.exists():
        return _default_header(path), {}

    header: list[str] = []
    entries: dict[str, PoEntry] = {}
    current_field: str | None = None
    current: dict[str, str] = {}
    references: list[str] = []

    def commit(line_number: int) -> None:
        nonlocal header, current, references
        msgid = current.get("msgid")
        msgstr = current.get("msgstr")
        if msgid == "" and "msgid" in current:
            header = _format_header(msgstr or "", path)
            return
        if msgid is None:
            raise ValueError(f"{path}:{line_number}: message is missing msgid")
        if msgstr is None:
            raise ValueError(f"{path}:{line_number}: message '{msgid}' is missing msgstr")
        if msgid in entries:
            entries[msgid].references.extend(references)
            if msgstr and not entries[msgid].msgstr:
                entries[msgid].msgstr = msgstr
            return
        entries[msgid] = PoEntry(msgid, msgstr, references)

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            if current:
                commit(line_number)
            current = {}
            references = []
            current_field = None
            continue
        if line.startswith("#:"):
            references.extend(line[2:].strip().split())
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgctxt"):
            raise ValueError(f"{path}:{line_number}: msgctxt is not used; keep only msgid and msgstr")

        for field_name in ("msgid", "msgstr"):
            if line.startswith(field_name):
                current_field = field_name
                current[field_name] = _parse_po_string(line, path, line_number)
                break
        else:
            if line.startswith('"') and current_field:
                current[current_field] += _parse_po_string(line, path, line_number)
            else:
                raise ValueError(f"{path}:{line_number}: unsupported PO syntax")

    if current:
        commit(line_number if "line_number" in locals() else 1)
    if not header:
        header = _default_header(path)
    return header, entries


def _format_header(header: str, path: Path) -> list[str]:
    language = _locale_for_path(path)
    lines = header.splitlines()
    if not any(line.startswith("Language:") for line in lines):
        lines.append(f"Language: {language}")
    return [
        "# QuickBib translations.",
        "# Copyright (C) 2026 QuickBib contributors",
        "# This file is distributed under the same license as the QuickBib project.",
        "#",
        'msgid ""',
        'msgstr ""',
        *[f'"{_escape_po_string(line)}\\n"' for line in lines],
    ]


def _default_header(path: Path) -> list[str]:
    language = _locale_for_path(path)
    return _format_header(
        "\n".join([
            "Project-Id-Version: QuickBib",
            "Report-Msgid-Bugs-To: https://github.com/archisman-panigrahi/quickbib/issues",
            "POT-Creation-Date: 2026-05-30 00:00-0400",
            "PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE",
            "Last-Translator: FULL NAME <EMAIL@ADDRESS>",
            "Language-Team: LANGUAGE <LL@li.org>",
            f"Language: {language}",
            "MIME-Version: 1.0",
            "Content-Type: text/plain; charset=UTF-8",
            "Content-Transfer-Encoding: 8bit",
            "Generated-By: validate_po.py",
        ]),
        path,
    )


def _locale_for_path(path: Path) -> str:
    try:
        return path.relative_to(PO_DIR).parts[0]
    except ValueError:
        return BASE_LOCALE


def _write_po(path: Path, header: list[str], entries: list[PoEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [*header, ""]
    for entry in entries:
        if entry.references:
            lines.append("#: " + " ".join(entry.references))
        lines.append(_po_line("msgid", entry.msgid))
        lines.append(_po_line("msgstr", entry.msgstr))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _translation_files() -> list[Path]:
    return sorted(PO_DIR.glob(f"*/LC_MESSAGES/{DOMAIN}.po"))


def _extract_messages() -> dict[str, list[str]]:
    messages: dict[str, list[str]] = {}
    for path in sorted(SOURCE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "tr":
                continue
            first_arg = node.args[0]
            if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
                continue
            reference = f"{path.relative_to(ROOT)}:{node.lineno}"
            messages.setdefault(first_arg.value, []).append(reference)
    return messages


def _placeholders(value: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(value))


def validate() -> bool:
    if not BASE_FILE.exists():
        print(f"Missing base translation file: {BASE_FILE}")
        return False

    used_messages = _extract_messages()
    _, base = _load_po(BASE_FILE)
    base_msgids = set(base)
    success = True

    missing_from_base = sorted(set(used_messages) - base_msgids)
    unused_in_base = sorted(base_msgids - set(used_messages))
    if missing_from_base:
        success = False
        print(f"{BASE_FILE}: missing messages used by source:")
        for msgid in missing_from_base:
            print(f"  - {msgid}")
    if unused_in_base:
        success = False
        print(f"{BASE_FILE}: messages not used by source:")
        for msgid in unused_in_base:
            print(f"  - {msgid}")

    locale_files = _translation_files()
    if not locale_files:
        print(f"No PO files found in {PO_DIR}")
        return False

    for locale_file in locale_files:
        _, data = _load_po(locale_file)
        msgids = set(data)

        missing = sorted(base_msgids - msgids)
        extra = sorted(msgids - base_msgids)
        placeholder_mismatches = sorted(
            msgid for msgid in base_msgids & msgids
            if _placeholders(msgid) != _placeholders(data[msgid].msgstr)
        )

        if missing or extra or placeholder_mismatches:
            success = False
            print(f"{locale_file}:")
            if missing:
                print(f"  missing messages ({len(missing)}):")
                for msgid in missing:
                    print(f"    - {msgid}")
            if extra:
                print(f"  extra messages ({len(extra)}):")
                for msgid in extra:
                    print(f"    - {msgid}")
            if placeholder_mismatches:
                print(f"  placeholder mismatch ({len(placeholder_mismatches)}):")
                for msgid in placeholder_mismatches:
                    print(f"    - {msgid}")

    if success:
        print(f"All PO translation files are valid ({len(locale_files)} locale file(s)).")
    return success


def extract() -> bool:
    used_messages = _extract_messages()
    header, base = _load_po(BASE_FILE)

    ordered_msgids = [msgid for msgid in base if msgid in used_messages]
    ordered_msgids.extend(sorted(set(used_messages) - set(ordered_msgids)))

    base_entries: list[PoEntry] = []
    for msgid in ordered_msgids:
        entry = base.get(msgid, PoEntry(msgid, msgid))
        entry.msgstr = msgid
        entry.references = used_messages[msgid]
        base_entries.append(entry)
    _write_po(BASE_FILE, header, base_entries)

    for locale_file in _translation_files():
        if locale_file == BASE_FILE:
            continue
        locale_header, entries = _load_po(locale_file)
        locale_entries: list[PoEntry] = []
        for base_entry in base_entries:
            entry = entries.get(base_entry.msgid, PoEntry(base_entry.msgid, ""))
            entry.references = base_entry.references
            locale_entries.append(entry)
        _write_po(locale_file, locale_header, locale_entries)

    return validate()


def main() -> int:
    parser = argparse.ArgumentParser(prog="validate_po.py")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--validate", action="store_const", dest="mode", const="validate")
    group.add_argument("--extract", action="store_const", dest="mode", const="extract")
    parser.set_defaults(mode="validate")
    args = parser.parse_args()

    if args.mode == "extract":
        return 0 if extract() else 1
    return 0 if validate() else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(exc)
        raise SystemExit(1)
