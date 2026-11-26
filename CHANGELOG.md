# Changelog

## 0.1.0 (2026-11-26)

- First release: portable Agent Plugins 1.0 package with the `draft-post`, `get-started`, `voice-card` skills.
- Codex marketplace file at `.agents/plugins/marketplace.json`; installs with `codex plugin marketplace add` then `codex plugin add`.
- Manifest, skill, outcome-sentence and public-hygiene checks, run in CI on Linux, macOS and Windows with Python 3.11 and 3.13.
- Install checked on Hermes Agent 0.22.0 and Codex 0.166.0 (see README, Install).
- Install lines pin the release payload commit; the release check verifies the pin is an ancestor of the tagged commit and that only README.md and CHANGELOG.md changed since.
