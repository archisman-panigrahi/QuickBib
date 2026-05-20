# <img src="assets/icon/scalable/io.github.archisman_panigrahi.QuickBib.svg" align="left" width="90" height="90">  <br> QuickBib

This is a cross platform app that enables you to get the bibtex entry from a DOI number, arXiv ID, article url (supports Nature journals, APS journals, PNAS, and more) or article title. It uses [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3) as its backend. Written in Python, QuickBib is licensed under GPLv3.
 
![screenshot](assets/screenshots/quickbib-animated.gif)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=archisman-panigrahi/QuickBib&type=date&legend=top-left)](https://www.star-history.com/#archisman-panigrahi/QuickBib&type=date&legend=top-left)

[![Stargazers repo roster for @archisman-panigrahi/QuickBub](https://reporoster.com/stars/archisman-panigrahi/QuickBib)](https://github.com/archisman-panigrahi/QuickBib/stargazers)

## How to install?

### GNU/Linux
<a href="https://repology.org/project/quickbib/versions">
    <img src="https://repology.org/badge/vertical-allrepos/quickbib.svg" alt="Packaging status" align="right">
</a>

#### Ubuntu/Mint
You can use our [official PPA](https://code.launchpad.net/~apandada1/+archive/ubuntu/quickbib)
```
sudo add-apt-repository ppa:apandada1/quickbib
sudo apt update
sudo apt install quickbib
```
On Debian,you can download and install the prebuilt .deb package from the PPA (or, use Flatpak/Snap).

#### Arch Linux/EndeavourOS/Manjaro
You can get it from the AUR

```
yay -S quickbib
```

#### Distro agnostic method 
QuickBib is available on Flathub and Snap Store.

<a href='https://flathub.org/en/apps/io.github.archisman_panigrahi.QuickBib'>
    <img height='55' alt='Get it on Flathub' src='https://flathub.org/api/badge?locale=en'/>
</a>
<a href="https://snapcraft.io/quickbib">
    <img height='55' alt="Get it from the Snap Store" src=https://snapcraft.io/en/dark/install.svg />
</a>

#### Install from source with meson in GNU/Linux
Install the required dependencies, pyqt6 and [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3). Afterwards, you can use meson to install quickbib.

```
git clone https://github.com/archisman-panigrahi/QuickBib.git
cd QuickBib
meson setup builddir --prefix="$HOME/.local"
meson install -C builddir
```

To uninstall, 
```
meson uninstall -C builddir
```

### Windows

QuickBib is available on Microsoft Store.

<a href="https://apps.microsoft.com/detail/9pk4hvx04jdq?referrer=appbadge&mode=full" target="_blank"  rel="noopener noreferrer">
	<img src="https://get.microsoft.com/images/en-us%20dark.svg" width="200"/>
</a>

It can be also installed via `winget`. Open Windows Terminal/Powershell and run
```
winget install -e --id archisman-panigrahi.QuickBib
```

Alternatively, prebuilt installers are available to download from [GitHub Releases](https://github.com/archisman-panigrahi/QuickBib/releases/latest). Note that Windows smartscreen might complain because it doesn't know about this app and you would have to [manually bypass it](https://www.thewindowsclub.com/microsoft-defender-smartscreen-prevented-an-unrecognized-app-from-starting).

### Web App

A web app is available at https://quickbib.streamlit.app/.

### macOS

It is recommended that on macOS you use the [web app](https://quickbib.streamlit.app/) instead. _Continue reading to learn why_.

No prebuilt macOS installers: Distributing an app that users can graphically install and run seems to require paying Apple perpetually (US$99/year) to sign and notarize the app even if the app is free — that’s plain extortion — so we ship the source instead. You can run QuickBib from source or build a macOS app using the packaging scripts on GitHub. **If you have a better idea about how to package the macOS app in a more convenient way (without perpetually paying Apple), please let us know in GitHub Issues**.

You can install the app's dependencies with pip and run from source (**see below**).

## How to run from source? (works in GNU/Linux or macOS and perhaps also Windows with a little bit of tweaking)

1. Clone the repo and enter it

```
git clone https://github.com/archisman-panigrahi/QuickBib.git
cd QuickBib
```

2. Create and activate a virtual environment (recommended)

```
python3 -m venv .venv
source .venv/bin/activate
```

3. Upgrade pip and install dependencies

```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

The desktop app defaults to PyQt6. To exercise the PySide6 path used by the
Android build, install the alternate requirements and set the Qt binding
explicitly:

```
pip install -r requirements-pyside.txt
QUICKBIB_QT_API=pyside6 python3 -m quickbib
```

4. Run QuickBib from source

You can run the package module directly:

```
python3 -m quickbib
```

Or run the convenience script in `bin/quickbib`:

```
./bin/quickbib
```

## Android

QuickBib keeps a single codebase for desktop and Android. The app imports Qt
through `quickbib/qt.py`: PyQt6 remains the default desktop binding, while
Android sets `QUICKBIB_QT_API=pyside6` and uses PySide6.

The Android entry point is the repository-root `main.py`, and
`quickbib.pyproject` lists the files that `pyside6-android-deploy` should
bundle. Android package metadata is set by the GitHub Actions workflow and
`tools/patch_pyside_android_deploy.py`:

- App title: `QuickBib`
- Package id: `io.github.archisman_panigrahi.quickbib`
- Version: `0.8.0`
- Icon: `assets/icon/192x192/io.github.archisman_panigrahi.QuickBib.png`
- Orientation: `portrait`
- Permission: `INTERNET`

To build an APK without installing Android Studio locally, run the
`Android APK` workflow from GitHub Actions. It runs on pushes to any branch and
can also be run manually for any branch once the workflow exists on the default
branch. Supported architecture choices are `aarch64`, `x86_64`, and `armv7a`.
For `aarch64` and `x86_64`, the workflow downloads the matching PySide6 and
shiboken6 Android wheels from Qt's official release archive. `armv7a` is 32-bit
ARM and needs custom PySide6/shiboken6 Android wheel URLs.

## Translations

QuickBib now uses JSON-based translations in `quickbib/locales/`. All translations
were initially done with AI and only some were later modified by native speakers.
Therefore there may be some mistakes/bad translation.
PRs for modifications and addition of new languages are welcome!

1. Copy `quickbib/locales/en.json` to a new file like `quickbib/locales/es.json`.
2. Translate the values, keeping keys unchanged.
3. Validate files locally:

```
python3 tools/check_translations.py
```

4. Open a pull request.

To test a specific locale locally, set `LANG` (or `LC_ALL`), for example:

```
LANG=es python3 -m quickbib
```
