# Contributing And Releasing

Use Python 3.11+ in a virtual environment. Install with `python -m pip install -e .`. Run `python -m unittest discover -s tests -v`, `python -m compileall -q scirate.py community.py browser.py`, and `git diff --check`.

Parser changes need upstream-template evidence and fixtures. Never commit session HTML, tokens or private content. Browser writes must not run in CI. Preserve AGPL licensing and align English/Chinese README sections.

For release, synchronize versions in pyproject.toml and scirate.py, update CHANGELOG.md, build wheel/sdist with `python -m build`, then install the wheel in a fresh environment outside the checkout. Check help/version/imports and MCP initialization. Inspect distributions and Git history for private data before publication. Tag the verified commit and attach both distributions with SHA-256 checksums to GitHub Releases. Do not claim a PyPI upload unless performed.
