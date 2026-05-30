#!/usr/bin/env python3
"""
A small macOS packager script intended to be run on a macOS machine (Apple
Silicon recommended) or macOS self-hosted runner. It will:

- create an isolated venv
- pip install application requirements + pyinstaller
- run pyinstaller to build a .app bundle
- create a compressed DMG that can be distributed and dragged into /Applications

Note: This script keeps things simple and focuses on producing a working DMG.
Code signing and notarization are out of scope and should be performed on a
developer machine or CI runner with the appropriate certificates.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import plistlib
import argparse

ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv_macos_build"
DIST_DIR = ROOT / "dist"
BUILD_NAME = "QuickBib"


def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def ensure_venv():
    if not VENV_DIR.exists():
        print("Creating virtual environment at", VENV_DIR)
        run([sys.executable, "-m", "venv", str(VENV_DIR)])


def venv_python():
    return str(VENV_DIR / "bin" / "python")


def install_deps():
    pip = [venv_python(), "-m", "pip", "install", "--upgrade", "pip"]
    run(pip)
    # install project requirements
    req = ROOT / "requirements.txt"
    if req.exists():
        run([venv_python(), "-m", "pip", "install", "-r", str(req)])
    # install pyinstaller
    run([venv_python(), "-m", "pip", "install", "pyinstaller==5.11.0"])  # pinned known-good


def _find_or_make_icns() -> Path | None:
    """Find a .icns file in assets/icon or try to generate one from PNG sizes.

    Returns the Path to the .icns file or None if not available.
    The generator uses `iconutil` (macOS) and the PNGs under assets/icon/*.
    """
    icons_dir = ROOT / "assets" / "icon"
    if not icons_dir.exists():
        return None

    # Prefer a bundled .icns if present
    icns = next(icons_dir.glob("*.icns"), None)
    if icns:
        return icns

    # If on macOS and iconutil is available, try to assemble an .iconset
    if sys.platform != "darwin":
        return None

    if shutil.which("iconutil") is None:
        return None

    # Map available PNG folders to iconset filenames
    mapping = {
        "16x16": "icon_16x16.png",
        "32x32": "icon_32x32.png",
        "64x64": "icon_64x64.png",
        "128x128": "icon_128x128.png",
    }

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / (BUILD_NAME + ".iconset")
        iconset.mkdir()

        found_any = False
        for folder_name, icon_name in mapping.items():
            src_dir = icons_dir / folder_name
            if src_dir.exists():
                # pick the first png inside
                png = next(src_dir.glob("*.png"), None)
                if png:
                    dest = iconset / icon_name
                    shutil.copyfile(png, dest)
                    found_any = True
                    # if we have a 64x64, make it 32x32@2x which iconutil understands
                    if folder_name == "64x64":
                        (iconset / "icon_32x32@2x.png").write_bytes(dest.read_bytes())

        if not found_any:
            return None

        out_icns = Path(tmp) / (BUILD_NAME + ".icns")
        try:
            run(["iconutil", "-c", "icns", str(iconset), "-o", str(out_icns)])
        except subprocess.CalledProcessError:
            return None

        if out_icns.exists():
            # move to a persistent location inside dist_artifacts for reproducibility
            out_dir = ROOT / "dist_artifacts"
            out_dir.mkdir(parents=True, exist_ok=True)
            persistent = out_dir / out_icns.name
            shutil.copyfile(out_icns, persistent)
            return persistent

    return None


def build_app():
    # Ensure clean build
    if (ROOT / "build").exists():
        shutil.rmtree(ROOT / "build")
    if (ROOT / "dist").exists():
        shutil.rmtree(ROOT / "dist")

    # Use our mac launcher as entrypoint so quickbib package is importable
    entry = ROOT / "windows_packaging" / "quickbib_macos_launcher.py"

    cmd = [
        venv_python(), "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--windowed",
        "--name", BUILD_NAME,
        str(entry)
    ]

    # Icon support: prefer a .icns in assets/icon, or try to generate one from PNGs
    icon_path = _find_or_make_icns()
    if icon_path:
        print("Using icon:", icon_path)
        cmd += ["--icon", str(icon_path)]

    # Optionally include assets directory if present
    assets = ROOT / "assets"
    if assets.exists():
        # PyInstaller expects --add-data in the format source:dest
        cmd += ["--add-data", f"{assets}{os.pathsep}assets"]

    po_dir = ROOT / "quickbib" / "po"
    if po_dir.exists():
        cmd += ["--add-data", f"{po_dir}{os.pathsep}quickbib/po"]

    run(cmd)


def create_dmg():
    # Try several common locations for the .app bundle produced by PyInstaller:
    # - dist/<name>/<name>.app
    # - dist/<name>.app
    # - any .app under dist/ (first match)
    app_bundle = None

    candidate1 = ROOT / "dist" / BUILD_NAME / (BUILD_NAME + ".app")
    candidate2 = ROOT / "dist" / (BUILD_NAME + ".app")
    if candidate1.exists():
        app_bundle = candidate1
    elif candidate2.exists():
        app_bundle = candidate2
    else:
        # fallback: search for any .app under dist/
        apps = list((ROOT / "dist").glob("**/*.app"))
        if apps:
            app_bundle = apps[0]

    if app_bundle is None or not app_bundle.exists():
        raise SystemExit(f"Failed to find built .app bundle in dist/ (checked {candidate1}, {candidate2} and recursive search)")

    # Ensure app Info.plist contains a proper version string
    # Try to import package metadata from the repo if available
    try:
        sys.path.insert(0, str(ROOT))
        from quickbib.app_info import APP_VERSION
    except Exception:
        APP_VERSION = None

    out_dir = ROOT / "dist_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    dmg_path = out_dir / f"{BUILD_NAME}-macos-arm64.dmg"

    # Create a temporary staging dir that will hold the .app
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        staged = tmp_path / app_bundle.name
        print("Copying app bundle to staging", staged)
        shutil.copytree(app_bundle, staged, symlinks=True)

        # Before creating the DMG, update the app bundle Info.plist with version
        if APP_VERSION is not None:
            info_plist = staged / "Contents" / "Info.plist"
            try:
                with open(info_plist, 'rb') as f:
                    plist = plistlib.load(f)
                plist['CFBundleShortVersionString'] = APP_VERSION
                plist['CFBundleVersion'] = APP_VERSION
                with open(info_plist, 'wb') as f:
                    plistlib.dump(plist, f)
                print("Updated Info.plist with version:", APP_VERSION)
            except Exception:
                print("Warning: failed to update Info.plist with version")

        # Also include the repository LICENSE file inside the app bundle's Resources
        try:
            license_src = ROOT / "LICENSE"
            if license_src.exists():
                resources_dir = staged / "Contents" / "Resources"
                resources_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(license_src, resources_dir / "LICENSE")
                print("Copied LICENSE into app bundle Resources")
        except Exception:
            print("Warning: failed to copy LICENSE into app bundle")

        # Create the DMG using hdiutil (macOS only)
        # Other options: create a DMG with a link to /Applications for drag-to-install
        print("Creating compressed DMG at", dmg_path)
        run([
            "hdiutil", "create",
            "-volname", BUILD_NAME,
            "-srcfolder", str(tmp_path),
            "-ov",
            "-format", "UDZO",
            str(dmg_path),
        ])

    print("DMG created:", dmg_path)
    return dmg_path


def create_app_artifact() -> Path:
    """Copy the built .app bundle into dist_artifacts and create a zip archive.

    This is useful if you want to distribute the .app directly (or as a zip)
    instead of packaging it inside a DMG.
    Returns the path to the zip archive if created, else the .app path.
    """
    # Find the built .app bundle (same logic as create_dmg)
    app_bundle = None

    candidate1 = ROOT / "dist" / BUILD_NAME / (BUILD_NAME + ".app")
    candidate2 = ROOT / "dist" / (BUILD_NAME + ".app")
    if candidate1.exists():
        app_bundle = candidate1
    elif candidate2.exists():
        app_bundle = candidate2
    else:
        apps = list((ROOT / "dist").glob("**/*.app"))
        if apps:
            app_bundle = apps[0]

    if app_bundle is None or not app_bundle.exists():
        raise SystemExit(f"Failed to find built .app bundle in dist/ (checked {candidate1}, {candidate2} and recursive search)")

    out_dir = ROOT / "dist_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    target_app = out_dir / app_bundle.name
    # remove existing target if present
    if target_app.exists():
        if target_app.is_dir():
            shutil.rmtree(target_app)
        else:
            target_app.unlink()

    print("Copying app bundle to", target_app)
    shutil.copytree(app_bundle, target_app, symlinks=True)

    # Make a zip archive containing the .app (easier for distribution)
    zip_base = out_dir / f"{BUILD_NAME}-macos-arm64"
    print("Creating zip archive for app at", zip_base.with_suffix('.zip'))
    # shutil.make_archive will add the .zip suffix automatically
    shutil.make_archive(str(zip_base), 'zip', root_dir=out_dir, base_dir=target_app.name)

    zip_path = zip_base.with_suffix('.zip')
    print("App artifact created:", target_app, zip_path)
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Build QuickBib .app and optionally a DMG")
    parser.add_argument('--app-only', action='store_true', help='Do not create a DMG; instead copy the .app to dist_artifacts and create a zip')
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("WARNING: This packager is intended to be run on macOS. You are on:", sys.platform)

    ensure_venv()
    install_deps()
    build_app()

    if args.app_only:
        artifact = create_app_artifact()
        print("Packaging complete. Artifact:", artifact)
    else:
        dmg = create_dmg()
        print("Packaging complete. Artifact:", dmg)


if __name__ == "__main__":
    main()
