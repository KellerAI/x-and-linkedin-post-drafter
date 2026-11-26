# AGENTS.md

## Purpose

`x-and-linkedin-post-drafter` is a portable Agent Plugins 1.0 package (root `plugin.json` plus `skills/`) for Hermes Agent and OpenAI Codex. Drafts X and LinkedIn posts and replies in your own voice from a short voice card, with a claim check and a character count on every draft. Behavior, install and limits are in `README.md`.

## Repo layout

- `plugin.json` - Agent Plugins 1.0 manifest (the only manifest; no per-host overlay yet)
- `skills/get-started/SKILL.md`, `skills/voice-card/SKILL.md`, `skills/draft-post/SKILL.md` - the plugin's skills
- `.agents/plugins/marketplace.json` - Codex and ChatGPT desktop marketplace entry
- `scripts/check_plugin.py` - manifest, skill, outcome-sentence and public-hygiene checks
- `tests/` - unittest suite that runs the checks and their negative cases
- `evals/cases.md` - behavior scenarios scored before each release

## Setup and tests

Standard library only:

```bash
python -m unittest discover -s tests -v
python scripts/check_plugin.py            # add --release before tagging a release
```

CI runs the suite on Linux, macOS and Windows with Python 3.11 and 3.13.

## Rules for agents

- `AGENTS.md` is the only agent-instructions file. Do not add `CLAUDE.md` or other tool-specific instruction files.
- Keep the plugin skills-only. Adding a tool, hook, MCP server or script changes the README disclosure and needs maintainer approval first.
- The outcome sentence is the first sentence of `plugin.json` `description` and the line under the README title. Change both together; the check fails if they drift. Keep it to 10 words or fewer.
- Never weaken or skip a test or check to get to green. Fix the content.
- This repo is public. Keep working notes, status files, approval lists, drafts, internal names, ticket ids and machine-specific paths out of it. `scripts/check_plugin.py` fails if they land.
- Every public claim in `README.md` must trace to a file, a test or a recorded run. Do not present illustrative transcripts as recorded runs.
- The README install line pins a 40-character release commit. Update it, and any catalog entry, on every behavior change.
- Don't open catalog PRs, post, publish or submit forms without maintainer approval.
- Agent-authored PRs come from the `son-of-anton-ai` account, state what changed, why, and the test evidence.
- Update `CHANGELOG.md` for user-visible changes.
