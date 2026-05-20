# <img src="assets/icon/scalable/io.github.archisman_panigrahi.QuickBib.svg" align="left" width="90" height="90">  <br> QuickBib

This is a cross platform app that enables you to get the bibtex entry from a DOI number, arXiv ID, article url (supports Nature journals, APS journals, PNAS, and more) or article title. It uses [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3) as its backend. Written in Python, QuickBib is licensed under GPLv3.

QuickBib can also **verify** that the BibTeX references in a paper are authentic and not hallucinated — see [Verify references](#verify-references).
 
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

4. Run QuickBib from source

You can run the package module directly:

```
python3 -m quickbib
```

Or run the convenience script in `bin/quickbib`:

```
./bin/quickbib
```

## Verify references

Large language models frequently invent realistic-looking citations — fabricated DOIs, papers that were never written, or DOIs that point to a completely different article. QuickBib can check every BibTeX reference against authoritative databases (CrossRef and arXiv) and tell you which ones are genuine.

Verification is **deterministic**: QuickBib fetches the real record for each entry and compares the metadata in code. No AI service, API key, or subscription is involved. Each reference is reported as one of:

- **verified** — the DOI/arXiv ID resolves and the metadata matches, or the title was found in CrossRef;
- **mismatch** — a record exists but the title does not match (e.g. the DOI belongs to a different paper);
- **not found** — the DOI/arXiv ID does not resolve, or no matching publication exists — likely fabricated;
- **unverified** — the entry had nothing to check against, or a database was unreachable.

There are three ways to use it.

### 1. In the desktop app

Open QuickBib and choose **Tools → Verify References** (or the **Verify References** quick-link button). Point it at a local `.bib` file, or connect directly to an Overleaf project using your Overleaf project ID and Git token. Results appear in a colour-coded table with the full finding for each reference.

### 2. From the command line

No GUI required:

```
python3 -m quickbib.verify references.bib
python3 -m quickbib.verify ./paper-folder --email you@example.com
python3 -m quickbib.verify --overleaf <PROJECT_ID> --token <GIT_TOKEN>
```

Add `--json` for machine-readable output. When `.tex` files are present, it also reports `\cite` keys that are not defined in any `.bib` file (a common sign of an invented citation key). Supplying `--email` opts in to CrossRef's faster "polite pool".

### 3. As an MCP server (optional — for Claude Desktop, Cursor, …)

The [`quickbib_mcp/`](quickbib_mcp/) folder is an optional [Model Context Protocol](https://modelcontextprotocol.io) server that exposes the same verification engine to AI assistants — so you can ask Claude to "check the references in my Overleaf project" while you write. See [`quickbib_mcp/README.md`](quickbib_mcp/README.md) for setup. The desktop app and CLI above work entirely on their own; the MCP server is just an extra front-end.

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
