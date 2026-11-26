# X and LinkedIn Post Drafter

[![CI](https://github.com/KellerAI/x-and-linkedin-post-drafter/actions/workflows/ci.yml/badge.svg)](https://github.com/KellerAI/x-and-linkedin-post-drafter/actions/workflows/ci.yml)

Posts in your own voice, drafted, never posted.

```text
You:   Draft a post about our launch note (pasted above).
Agent: X (214/280):
       <draft in your voice, in its own block>
       LinkedIn (1,126/3,000): <draft>
       Needs source: "cut review time by half" is not in your note. Add a source or I will drop it.
       Alternative hook: <one line>
       Nothing is posted. Copy what you want.
```

Illustrative transcript, not a recorded run. A recorded demo replaces it before the first release.

Drafts X and LinkedIn posts and replies in your own voice from a short voice card, with a claim check and a character count on every draft. Portable Agent Plugins 1.0 package for Hermes Agent and for OpenAI Codex and the ChatGPT desktop app: one `plugin.json` and 3 skills.

## Install

Hermes Agent:

```bash
hermes plugins install KellerAI/x-and-linkedin-post-drafter --ref <release-sha> --no-enable
hermes plugins enable x-and-linkedin-post-drafter
```

Portable packages stay disabled until you enable them. Once enabled, the skills appear as `x-and-linkedin-post-drafter:get-started` and `x-and-linkedin-post-drafter:voice-card` and `x-and-linkedin-post-drafter:draft-post`.

OpenAI Codex or the ChatGPT desktop app: this repository ships a marketplace file at `.agents/plugins/marketplace.json`. Add the repository as a plugin marketplace and install `x-and-linkedin-post-drafter`.

## Skills

| Skill | Use it when |
|---|---|
| `get-started` | You have just enabled the plugin. It asks about your audience, builds or loads your voice card and sets your never-include list. |
| `voice-card` | You have no voice card, want to update it, or keep making the same edit to drafts. |
| `draft-post` | You want an X or LinkedIn post or reply drafted from an idea, your own work, a link or a post you paste. |

## What it needs

- Nothing beyond pasted text. LinkedIn content is used only when you paste it; the plugin does not scrape.


## What it does not do

- It does not post, like, follow, comment, connect or message for you.
- It does not invent anecdotes, metrics, clients or quotes.
- It does not share one person's voice card or samples with another person.

## Disclosure

- No network calls of its own, no telemetry, no stored credentials. Voice cards live in your host's memory if it has one, or in a Markdown block you keep.
- Companion to KellerAI's Hook Desk plugin for studying why a post's opening works: https://github.com/KellerAI/hermes-plugins/tree/main/hook-desk
- Model calls are your host's own; the plugin adds none.
- Skills only: no tools, hooks, MCP servers, scripts, compiled binaries, stored credentials or telemetry.

## Honest limits

- A voice card built from a few samples captures patterns, not you. Drafts need your edit, and early drafts sound less like you.
- The claim check covers only what can be found and opened this run; it does not make a claim true.
- Platform character limits and rules change. Check the current limit for your account.
- The approval rule is an instruction to the model, not an enforced lock. Your host's approval settings are what actually block an unapproved action.

## Measured evaluation

No measured results yet. `evals/cases.md` lists the scenarios each release is scored on. Results, including failures, are published here per release.

## Development

```bash
python -m unittest discover -s tests -v
python scripts/check_plugin.py
```

Standard library only; no install needed. See `AGENTS.md`.

## License and credit

Apache-2.0. See `LICENSE` and `NOTICE`.

Built by KellerAI (https://kellerai.io). KellerAI on X: [@KellerAI_KAI](https://x.com/kellerai_kai) · Jonathan Bowe, Co-Founder & COO, on X: [@KellerAI_COO](https://x.com/KellerAI_COO) · LinkedIn: https://www.linkedin.com/in/jonathan-bowe-kellerai

KellerAI is not affiliated with or endorsed by Nous Research, xAI or OpenAI.
