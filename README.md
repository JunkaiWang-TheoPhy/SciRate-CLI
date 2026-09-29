<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文</a></p>

<h1 align="center">SciRate CLI</h1>

<p align="center"><img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue"> <img alt="AGPL-3.0" src="https://img.shields.io/badge/license-AGPL--3.0-blue"></p>

![Scholarly paper inside a SciRate command-line frame](assets/scirate-cli-banner.png)

## Introduction

An unofficial client for [SciRate](https://scirate.com) and arXiv with no third-party runtime dependencies. Read paper metadata, feeds, comments and sciters as JSON; expose the same read operations through a stdio MCP server. On macOS, use an existing Chrome or Safari session for explicitly requested interactions without exporting cookies.

Version 0.3.0 is an initial beta. SciRate's web routes are not a stable public API. Cloudflare can block direct reads; the client reports that condition rather than bypassing it. Browser interactions require a signed-in account. Passing offline tests does not establish live account compatibility.

## Installation

Requires Python 3.11+. Install the release wheel or use:

```sh
pipx install git+https://github.com/JunkaiWang-TheoPhy/SciRate-CLI.git@v0.3.0
scirate --version
scirate --help
```

Alternatively, clone the repository and run `python -m pip install .` in a virtual environment. GitHub release publication does not imply PyPI publication.

## Commands

```sh
scirate paper 1509.01147
scirate community 1509.01147
scirate feed quant-ph
scirate scites USERNAME --page 1
scirate import saved-page.html --source-url https://scirate.com/arxiv/quant-ph
scirate auth-status --browser Chrome
scirate browser-read --browser Chrome
scirate act scite 1509.01147
scirate act unscite 1509.01147
scirate act subscribe quant-ph
scirate act unsubscribe quant-ph
scirate act comment 1509.01147 --content 'Your considered comment'
scirate act reply COMMENT_ID --content 'Your reply'
scirate receipt TICKET
```

Success emits `{"ok":true,"data":...}` to stdout. Errors emit `{"ok":false,"error":...}` to stderr and exit 1; syntax errors exit 2. Actions return a pending ticket, not proof of success. Query its receipt in the same tab, refresh, and confirm the resulting site state. An unknown ticket can mean a different tab, page reload, or invalid ticket. Never blindly resend an uncertain comment.

Browser commands are macOS-only. In Chrome's **macOS menu bar**, enable **View > Developer > Allow JavaScript from Apple Events** (not in the Settings page). Safari has an equivalent Develop menu option. Open SciRate, complete any normal browser challenge, and sign in yourself. Keep only the intended SciRate tab open: the bridge uses the first matching tab. Disable the broad browser scripting permission when no longer needed.

## MCP

```json
{"mcpServers":{"scirate":{"command":"scirate","args":["mcp"]}}}
```

Six read-only tools: `paper`, `community`, `feed`, `scites`, `browser_read`, `auth_status`. Writes are CLI-only. Transport is newline-delimited JSON-RPC over stdio; no HTTP listener starts. If the host has a restricted PATH, supply the installed executable's absolute path.

## Storage And Evidence

HTTP responses are cached for one hour. Set `SCIRATE_DATA_DIR` to choose the local directory; the compatible default is `~/.local/share/scirate-tools/data`. Files are written atomically with owner-only permissions. Imported pages may contain private session information: never commit cache or HTML archives.

Missing fields remain unknown; hidden/deleted comment text is omitted. See [sources](docs/sources.md), [verification](docs/verification.md), and [security](SECURITY.md). Login automation, comment edit/delete, moderation and a TUI are not implemented.

## Development

```sh
python -m unittest discover -s tests -v
python -m compileall -q scirate.py community.py browser.py
python -m pip install build
python -m build
```

Tests use synthetic upstream-shaped HTML and mocked network/browser responses, not public posts. CI checks Python 3.11, 3.12 and 3.13. See [contributing](docs/contributing.md).

## Structure

- `docs/`: interface research and command design
- `scirate.py`, `community.py`, `browser.py`: client, parser and browser bridge
- `tests/`: regression tests
- `assets/`: visual material

## License

Licensed under GNU AGPL-3.0-only. See [LICENSE](LICENSE). Not affiliated with SciRate or arXiv; no upstream implementation code is vendored.
