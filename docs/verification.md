# Verification Boundaries

Tests check synthetic upstream-shaped HTML, inputs, read-only MCP discovery, browser request construction and cache behavior. They do not authenticate or post to SciRate.

On 2026-09-29, Chrome Apple Events access succeeded. Browser capture initially faced Cloudflare and correctly rejected it; subsequently the normal browser loaded the quantum physics feed and the bridge successfully parsed its public papers. The session was not signed in. Live account write acceptance has not been verified. A pending ticket, HTTP 200 or successful script execution alone is insufficient evidence of completed interaction.

The complete suite passed 23 tests locally. The seven new release tests were also run against the pre-release prototype, without real network calls: `Ran 7 tests ... FAILED (failures=5, errors=1)`; the new implementation returned `Ran 23 tests ... OK`. Failures covered request timeout, corrupt-cache recovery, page argument type, JSON-RPC parse error, protocol negotiation and unknown receipt handling. The live feed read parsed 50 paper records.

Release gates: tests, clean diff checks, wheel/sdist build, and independently installed wheel help/version/MCP smoke checks. CI results are recorded separately in GitHub Actions.
