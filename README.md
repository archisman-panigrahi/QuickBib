# <img src="assets/icon/scalable/io.github.archisman_panigrahi.QuickBib.svg" align="left" width="90" height="90">  <br> QuickBib

This is a cross platform app that enables you to get the bibtex entry from a DOI number, arXiv ID, article url (supports Nature journals, APS journals, ACS journals, AMS journals, Science, PNAS, ScienceDirect, IOP Science, SciPost and more) or article title. It uses [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3) as its backend. Written in Python, QuickBib is licensed under GPLv3.

*Metadata from Crossref and arXiv (no AI/ML). [Here](https://github.com/archisman-panigrahi/doi2bib3/blob/main/docs/ALGORITHM_VISUALS.md#2-identifier-resolution-decision-tree) is how it works.*

<img src="assets/screenshots/quickbib-animated.gif" width="420" height="400"><br><br>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=archisman-panigrahi/QuickBib&type=date&legend=top-left)](https://www.star-history.com/#archisman-panigrahi/QuickBib&type=date&legend=top-left)

[![Stargazers repo roster for @archisman-panigrahi/QuickBub](https://reporoster.com/stars/archisman-panigrahi/QuickBib)](https://github.com/archisman-panigrahi/QuickBib/stargazers)

## How to install?

### GNU/Linux
<table align="right">
  <tr>
    <td align="right">
      <img src="https://img.shields.io/github/v/release/archisman-panigrahi/QuickBib" alt="GitHub Release">
    </td>
    <td rowspan="3">
      <a href="https://repology.org/project/quickbib/versions">
        <img src="https://repology.org/badge/vertical-allrepos/quickbib.svg" alt="Packaging status">
      </a>
    </td>
  </tr>
  <tr>
    <td align="right">
      <a href="https://flathub.org/apps/details/io.github.archisman_panigrahi.QuickBib">
        <img src="https://img.shields.io/flathub/v/io.github.archisman_panigrahi.QuickBib?color=67bed9" alt="Flathub version">
      </a>
    </td>
  </tr>
  <tr>
    <td align="right">
      <img src="https://img.shields.io/winget/v/archisman-panigrahi.QuickBib" alt="WinGet Package Version">
    </td>
  </tr>
</table>


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

#### Omarchy

An <a href="https://omarchyplugins.com/plugin.html?id=archisman-panigrahi.quickbib">Omarchy plugin</a> is available in <a href="https://github.com/archisman-panigrahi/QuickBib-omarchy-plugin">here</a>:
```
omarchy plugin add https://github.com/archisman-panigrahi/QuickBib-omarchy-plugin.git --enable
```
<img src="https://raw.githubusercontent.com/archisman-panigrahi/QuickBib-omarchy-plugin/refs/heads/main/preview.png" alt="QuickBib Omarchy plugin preview" loading="lazy" width="600"/>


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

A web app is available at https://archisman-panigrahi.github.io/QuickBib/webapp.

### macOS

It is recommended that on macOS you use the [web app](https://archisman-panigrahi.github.io/QuickBib/webapp) instead. _Continue reading to learn why_.

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

4. Run QuickBib from source

You can run the package module directly:

```
python3 -m quickbib
```

Or run the convenience script in `bin/quickbib`:

```
./bin/quickbib
```

## Translations

QuickBib uses gettext-style PO translations in `quickbib/po/`. All translations
were initially done with AI and only some were later modified by native speakers.
Therefore there may be some mistakes/bad translation.
PRs for modifications and addition of new languages are welcome!

### Translation file format

Each language has one PO file:

```
quickbib/po/<language>/LC_MESSAGES/quickbib.po
```

For example:

```
quickbib/po/fr/LC_MESSAGES/quickbib.po
quickbib/po/pt_br/LC_MESSAGES/quickbib.po
quickbib/po/zh_cn/LC_MESSAGES/quickbib.po
```

In each entry, `msgid` is the English source text and `msgstr` is the
translation. Translate only `msgstr`; keep `msgid` unchanged.

### Improve an existing translation

1. Open the PO file for the language you want to improve.
2. Edit the `msgstr` values.
3. Validate the PO files:

```
python3 validate_po.py --validate
```

4. Open a pull request.

### Add a new language

1. Choose a language code, such as `de`, `es`, `fr`, `pt_br`, or `zh_cn`.
2. Create a new directory using that language code:

```
mkdir -p quickbib/po/<language>/LC_MESSAGES
```

3. Copy the English PO file:

```
cp quickbib/po/en/LC_MESSAGES/quickbib.po quickbib/po/<language>/LC_MESSAGES/quickbib.po
```

4. Edit the new file and translate the `msgstr` values. Keep `msgid` unchanged.
5. Update the `Language:` header in the new file to match the language code.
6. Validate the PO files:

```
python3 validate_po.py --validate
```

7. Open a pull request.

### Update PO files after source changes

When adding or removing calls like `tr("Text to translate")` in the source code,
refresh the PO files before validating:

```
python3 validate_po.py --extract
python3 validate_po.py --validate
```

`--extract` adds new English strings, removes unused strings, and refreshes
source line references while keeping existing translations.

To test a specific locale locally, set `LANG` (or `LC_ALL` if your environment
already sets it), for example:

```
LANG=es python3 -m quickbib
```
