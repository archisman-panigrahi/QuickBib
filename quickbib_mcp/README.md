# QuickBib MCP Server

An optional [Model Context Protocol](https://modelcontextprotocol.io) server
that exposes QuickBib's **reference-verification engine** to AI assistants
(Claude Desktop, Claude Code, Cursor, …).

It lets you ask an assistant to *"check whether the references in my paper are
real"* while you write. The assistant calls a tool — **the verdict itself is
produced by this server's deterministic code**, which fetches the authentic
record for each reference from CrossRef and arXiv and compares the metadata.
The AI never decides authenticity; it only relays the result.

> **Do I need a paid subscription?** No. This is a *local* MCP server. It runs
> on the free tier of Claude Desktop, and MCP is an open standard supported by
> other clients too. You only need *some* MCP client to drive the tools — the
> verification work and the network calls are done entirely by this server.
>
> If you do not want any AI client involved at all, you do not need this
> server: use the QuickBib desktop app (**Tools → Verify References**) or the
> command line (`python -m quickbib.verify`) instead. Same engine, no MCP.

## Tools

| Tool | What it does |
|------|--------------|
| `verify_overleaf_project` | Clone an Overleaf project via its Git bridge, verify every `.bib` entry, and cross-check `\cite` keys in the `.tex` files. |
| `verify_bib_file` | Verify every entry in a local `.bib` file. |
| `verify_bibtex_text` | Verify BibTeX entries pasted directly as text. |
| `verify_reference` | Verify a single DOI, arXiv ID, or article title. |

Each tool returns a structured result plus a plain-text `report` the assistant
can relay verbatim.

## Prerequisites

- **Python 3.10+** and **Git** on your `PATH`.
- A local copy of the **QuickBib repository** (this folder lives inside it —
  the server imports `quickbib.verify` from the repo, no install needed).
- The **`mcp`** package:

  ```
  pip install -r quickbib_mcp/requirements.txt
  ```

No API key is required for CrossRef or arXiv.

## Add it to Claude Desktop

Edit the Claude Desktop config file:

| OS      | Path |
|---------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux   | `~/.config/Claude/claude_desktop_config.json` |

Add a `quickbib-verifier` entry pointing at `server.py` (use the **absolute
path** to your checkout):

```json
{
  "mcpServers": {
    "quickbib-verifier": {
      "command": "python",
      "args": ["C:\\Users\\you\\QuickBib\\quickbib_mcp\\server.py"],
      "env": {
        "OVERLEAF_PROJECT_ID": "your_overleaf_project_id",
        "OVERLEAF_GIT_TOKEN": "olp_xxxxxxxxxxxxxxxx",
        "CROSSREF_EMAIL": "you@example.com"
      }
    }
  }
}
```

On macOS / Linux use a forward-slash path, e.g.
`"/home/you/QuickBib/quickbib_mcp/server.py"`.

Restart Claude Desktop. The `quickbib-verifier` tools appear in the 🔧 menu.

The whole `env` block is **optional**:

- `OVERLEAF_PROJECT_ID` / `OVERLEAF_GIT_TOKEN` — default credentials for
  `verify_overleaf_project`. You can also pass them as tool arguments instead
  of putting them here.
- `CROSSREF_EMAIL` — opts in to CrossRef's faster "polite pool".

## Add it to Claude Code

```
claude mcp add quickbib-verifier -- python /abs/path/to/QuickBib/quickbib_mcp/server.py
```

(Other MCP clients such as Cursor use the same `command` / `args` shape as the
Claude Desktop JSON above.)

## Getting Overleaf credentials

1. **Project ID** — open the project on Overleaf; it is the last part of the
   URL: `https://www.overleaf.com/project/<PROJECT_ID>`.
2. **Git token** — Overleaf → *Account Settings* → *Git Integration* →
   *Create Token*.

The token grants read access to the project. It is used locally to `git clone`
the project and is never stored or transmitted anywhere else.

## Smoke test (no AI client needed)

```
pip install -r quickbib_mcp/requirements.txt
python -m quickbib_mcp
```

The process starts and waits for JSON-RPC on stdin — that is the MCP server
running over stdio. Press Ctrl+C to exit. For a quick functional check without
the protocol, the underlying engine is also runnable directly:

```
python -m quickbib.verify --help
```

## Usage examples

Once configured, ask your assistant things like:

```
Verify the references in my Overleaf project.
Check this .bib file for hallucinated citations: /path/to/refs.bib
Is the DOI 10.1038/nphys1170 real?
```

## License

GPL-3.0-or-later, same as QuickBib.
