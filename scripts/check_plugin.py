#!/usr/bin/env python3
"""Checks for a portable Agent Plugins 1.0 package. Standard library only.

- plugin.json follows the Agent Plugins 1.0.0 schema (fields, name pattern).
- Every skills/<dir>/SKILL.md has frontmatter whose name matches its folder,
  a description that says when to use it, and a license.
- The outcome sentence (first sentence of the manifest description) is 10 words
  or fewer and matches the line under the README title.
- Skills-only: no root mcp.json, hooks, apps or bin.
- Codex marketplace entry names this plugin and carries the required policy keys.
- Public hygiene: no internal markers or private terms (EXTRA_HYGIENE_TERMS or a
  gitignored .hygiene-terms file), machine paths, ticket or chat ids, secrets,
  em-dashes or working-note files.
- --release: the README install line pins a 40-character commit.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ALLOWED_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                "repository", "license", "keywords", "extensions"}
AUTHOR_KEYS = {"name", "email", "url"}
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
MAX_OUTCOME_WORDS = 10

HYGIENE_PATTERNS = {
    "internal marker": re.compile(r"(keep\s+private|do\s+not\s+(post|submit)\s+from\s+bots|mac\s+mini|shared\s+box)", re.I),
    "machine path": re.compile(r"(/home/box|/workspace/|/cursor/|/Users/[A-Za-z]|C:\\\\Users)"),
    "ticket id": re.compile(r"\b(?!(?:UTF|SHA|ISO|RFC|CVE|ES|TLS|HTTP)-)[A-Z]{2,5}-\d{1,5}\b"),
    "chat id": re.compile(r"\b[CU]0[A-Z0-9]{8,}\b"),
    "uuid": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
    "secret-like token": re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_|sk[-_][A-Za-z0-9]{20,}|xox[abpr]-|AKIA[0-9A-Z]{16})"),
    "em-dash": re.compile("\u2014"),
}
NOTE_FILE_RE = re.compile(r"(?i)^(notes?|status|todo|handoff|approvals?|draft)s?(\..*)?$")
SKIP_HYGIENE = {"LICENSE"}
# Skills-only packages: these would make the plugin load code or servers on enable.
FORBIDDEN_ROOT = ("mcp.json", ".mcp.json", ".app.json", "hooks", "bin", "commands")
TEXT_SUFFIXES = {".md", ".json", ".yml", ".yaml", ".py", ".txt", ""}
SELF_REL = "scripts/check_plugin.py"
LOCAL_TERMS_FILE = ".hygiene-terms"  # gitignored; one private term per line


def extra_terms(root: Path) -> list[str]:
    """Private names to block, kept out of the public repo: env var plus a gitignored file."""
    import os
    terms = [t.strip() for t in os.environ.get("EXTRA_HYGIENE_TERMS", "").split(",")]
    local = root / LOCAL_TERMS_FILE
    if local.exists():
        terms += [t.strip() for t in local.read_text(encoding="utf-8").splitlines()]
    return [t for t in terms if t and not t.startswith("#")]


def outcome_sentence(description: str) -> str:
    match = re.match(r"(.+?[.!?])(\s|$)", description.strip())
    return (match.group(1) if match else description).strip()


def readme_promise(readme: str) -> str:
    lines = [l.strip() for l in readme.splitlines()]
    seen_title = False
    for line in lines:
        if line.startswith("# "):
            seen_title = True
            continue
        if seen_title and line and not line.startswith("[!["):
            return line
    return ""


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def check_pin_in_history(root: Path, pin: str) -> list[str]:
    """The pinned commit must be an ancestor of HEAD and differ from HEAD only in README.md and CHANGELOG.md,
    so the pinned install loads exactly the files the tagged commit ships."""
    import subprocess

    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)

    if git("cat-file", "-e", f"{pin}^{{commit}}").returncode != 0:
        return [f"release: pinned commit {pin[:12]} is not in this repository"]
    if git("merge-base", "--is-ancestor", pin, "HEAD").returncode != 0:
        return [f"release: pinned commit {pin[:12]} is not an ancestor of HEAD"]
    changed = {l for l in git("diff", "--name-only", pin, "HEAD").stdout.splitlines() if l}
    extra = sorted(changed - {"README.md", "CHANGELOG.md"})
    return [f"release: files changed after the pinned commit besides README.md and CHANGELOG.md: {extra}"] if extra else []


def check(root: Path, release: bool = False) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"plugin.json: cannot read ({exc})"]

    if manifest.get("$schema") != SCHEMA_ID:
        errors.append("plugin.json: $schema must be the Agent Plugins 1.0.0 schema id")
    extra = set(manifest) - ALLOWED_KEYS
    if extra:
        errors.append(f"plugin.json: keys not allowed by the schema: {sorted(extra)}")
    name = manifest.get("name", "")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append("plugin.json: name must be kebab-case, 1-64 chars, no '--' or '..'")
    if name and name != root.name and root.name not in {"", "."}:
        errors.append(f"plugin.json: name '{name}' should match the repo folder '{root.name}'")
    if not SEMVER_RE.match(str(manifest.get("version", ""))):
        errors.append("plugin.json: version must be semver")
    author = manifest.get("author", {})
    if not isinstance(author, dict) or set(author) - AUTHOR_KEYS:
        errors.append("plugin.json: author may only have name, email, url")
    if not isinstance(manifest.get("keywords", []), list):
        errors.append("plugin.json: keywords must be a list")
    if not manifest.get("license"):
        errors.append("plugin.json: license is required for a public package")

    description = manifest.get("description", "")
    outcome = outcome_sentence(description)
    if len(outcome.split()) > MAX_OUTCOME_WORDS:
        errors.append(f"outcome sentence has {len(outcome.split())} words (max {MAX_OUTCOME_WORDS}): {outcome!r}")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    if not readme:
        errors.append("README.md is missing")
    elif readme_promise(readme) != outcome:
        errors.append(f"README promise {readme_promise(readme)!r} differs from manifest outcome {outcome!r}")

    skills_dir = root / "skills"
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []
    if not skill_dirs:
        errors.append("skills/: at least one skill is required")
    for skill in skill_dirs:
        skill_md = skill / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill.name}: SKILL.md missing")
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm.get("name") != skill.name:
            errors.append(f"{skill.name}: frontmatter name must equal the folder name")
        if not fm.get("description", "").lower().startswith("use "):
            errors.append(f"{skill.name}: description should start with 'Use ...' and say when to use it")
        if not fm.get("license"):
            errors.append(f"{skill.name}: frontmatter license missing")
        if readme and f"`{skill.name}`" not in readme:
            errors.append(f"{skill.name}: not listed in README skills table")

    market_path = root / ".agents" / "plugins" / "marketplace.json"
    if market_path.exists():
        market = json.loads(market_path.read_text(encoding="utf-8"))
        entries = [e for e in market.get("plugins", []) if e.get("name") == name]
        if not entries:
            errors.append("marketplace.json: no entry for this plugin")
        for entry in entries:
            policy = entry.get("policy", {})
            if not policy.get("installation") or not policy.get("authentication") or not entry.get("category"):
                errors.append("marketplace.json: entry needs policy.installation, policy.authentication and category")
            path = entry.get("source", {}).get("path", "")
            if not str(path).startswith("./"):
                errors.append("marketplace.json: source.path must start with './'")

    for forbidden in FORBIDDEN_ROOT:
        if (root / forbidden).exists():
            errors.append(f"{forbidden}: this package is skills-only; the README disclosure says so")

    for required in ("LICENSE", "NOTICE", "AGENTS.md", "CHANGELOG.md"):
        if not (root / required).exists():
            errors.append(f"{required} is missing")
    if (root / "CLAUDE.md").exists():
        errors.append("CLAUDE.md found: AGENTS.md is the only agent-instructions file")

    private_terms = extra_terms(root)
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        if rel.as_posix() == LOCAL_TERMS_FILE:
            continue
        if NOTE_FILE_RE.match(path.name) or rel.parts[0] in {"drafts", "internal"} or path.name.endswith(".internal.md"):
            errors.append(f"{rel}: working-note file in a public repo")
        if path.name in SKIP_HYGIENE or path.suffix not in TEXT_SUFFIXES:
            continue
        if rel.as_posix() in {SELF_REL, LOCAL_TERMS_FILE} or rel.parts[0] == "tests":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in HYGIENE_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: {label} ({match.group(0)!r})")
        for term in private_terms:  # never echo the term itself into CI logs
            for match in re.finditer(re.escape(term), text, re.I):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: private term")

    if release:
        hermes_pins = re.findall(r"hermes plugins install \S+ --ref (\S+)", readme)
        codex_pins = re.findall(r"codex plugin marketplace add \S+ --ref (\S+)", readme)
        pins = hermes_pins + codex_pins
        if not hermes_pins or not codex_pins or not all(re.fullmatch(r"[0-9a-f]{40}", p) for p in pins):
            errors.append("release: README Hermes and Codex install lines must pin a 40-character commit")
        elif len(set(pins)) != 1:
            errors.append("release: README Hermes and Codex install lines must pin the same commit")
        elif (root / ".git").exists():
            errors.extend(check_pin_in_history(root, pins[0]))
    return errors


def main(argv: list[str]) -> int:
    release = "--release" in argv
    args = [a for a in argv if not a.startswith("--")]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parent.parent
    errors = check(root, release=release)
    for err in errors:
        print(f"FAIL {err}")
    if not errors:
        print(f"ok: {root.name}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
