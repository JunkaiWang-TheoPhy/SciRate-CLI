# Project Map

SciRate-CLI is an unofficial Python 3.11+ client, licensed AGPL-3.0-only, with no third-party runtime dependencies. The canonical remote is the SciRate-CLI repository on GitHub under JunkaiWang-TheoPhy.

- `scirate.py`: CLI entry, HTTP cache, arXiv Atom reader, saved-page import, read-only stdio MCP.
- `community.py`: standard-library HTML parser for upstream paper/comment/sciter templates.
- `browser.py`: macOS Chrome/Safari Apple Events bridge and explicit asynchronous write commands.
- `tests/`: unit/regression tests and Node-based generated-JavaScript contract check.
- `docs/`: source ledger, contribution and verification boundaries.
- `.github/workflows/test.yml`: Python matrix, tests, install and package build.
- `pyproject.toml`: version and installed `scirate` entry point.

Run tests with `python -m unittest discover -s tests -v`; build with `python -m build`. Browser reads depend on an open SciRate tab and enabled scripting permission. Account writes require a signed-in session; automated tests never post public content. Direct HTTP requests may face Cloudflare. Cache and session archives must remain outside Git. See SECURITY.md and docs/verification.md before changing these boundaries.
