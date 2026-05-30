# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for QuickBib.

This spec collects PyQt6 resources plus the project's `assets` and `quickbib/po`
directories. It builds an --onedir (COLLECT) output named `QuickBib` which the
NSIS script packages.

If you want an exe-only single-file build set `onefile=True` and adjust the NSIS script.
"""
import sys
import os
try:
    # Newer PyInstaller versions expose Tree in utils.hooks
    from PyInstaller.utils.hooks import collect_all, Tree
except Exception:
    # Fallback: define a simple Tree helper that mimics PyInstaller.utils.hooks.Tree
    from PyInstaller.utils.hooks import collect_all

    def Tree(source_dir, prefix=None):
        """
        Walk source_dir and return a list of (src, dest) tuples suitable for
        passing to Analysis(datas=...). dest paths are relative to the
        distribution root, optionally prefixed.
        This is a minimal compatible fallback for including static asset files.
        """
        if prefix is None:
            prefix = ''
        entries = []
        for root, _, files in os.walk(source_dir):
            rel_dir = os.path.relpath(root, source_dir)
            # When rel_dir is '.', we want to place files directly under prefix
            rel_dir = '' if rel_dir == '.' else rel_dir
            for f in files:
                src = os.path.join(root, f)
                if rel_dir:
                    dest = os.path.join(prefix, rel_dir)
                else:
                    dest = prefix
                entries.append((src, dest))
        return entries

block_cipher = None

# Collect PyQt6 related datas/binaries/hiddenimports handled by PyInstaller's helpers
pyqt_datas, pyqt_binaries, pyqt_hiddenimports = collect_all('PyQt6')

# Include application assets (icons, screenshots, etc.)
# Include PO translation files used by quickbib/i18n.py.
# Also include the repository LICENSE file and place it into the `quickbib` package
# so runtime code that does Path(__file__).with_name('LICENSE') can find it when
# PyInstaller produces the onedir distribution.
datas = (
    pyqt_datas
    + Tree('assets', prefix='assets')
    + Tree('quickbib/po', prefix='quickbib/po')
    + [(os.path.join('.', 'LICENSE'), 'quickbib')]
)
binaries = pyqt_binaries
hiddenimports = pyqt_hiddenimports + ['doi2bib3']

a = Analysis(
    ['windows_packaging/quickbib_launcher.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuickBib',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    # Use the provided Windows .ico file from the repo's assets
    icon='assets/icon/64x64/io.github.archisman_panigrahi.quickbib.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='QuickBib',
)
