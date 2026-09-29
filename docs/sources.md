# Source ledger — 2026-09-29

Official source inspected at commit `8822bce6db734765f3b43dbe2eaf846245e9df71`:
https://github.com/scirate/scirate

Fully inspected relevant files: papers/_paper.html.slim, papers/show.html.slim,
papers/scites.html.erb, comments/_comment.html.slim, sessions/new.html.slim,
comments_controller.rb, sessions_controller.rb, application_controller.rb,
scirate.js.coffee, comments.js.coffee. These establish the parser selectors,
reply references, CSRF requirements, and comment form parameters.

Third-party comparisons:
- https://github.com/vprusso/scirate — Python requests/HTML extraction; old releases;
  useful reader interface, not adopted as an unverified runtime dependency.
- https://github.com/silky/scirate-cli — Haskell terminal selection and voting;
  useful interaction workflow, current live compatibility unverified.
- https://github.com/scirate/scirate/pull/535 — proposed JSON responses;
  proposal is not treated as deployed functionality.

No third-party implementation code copied into this project. Tests contain
synthetic HTML following the documented official template structure.
