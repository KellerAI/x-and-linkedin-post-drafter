import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_plugin  # noqa: E402


class RepoPasses(unittest.TestCase):
    def test_repo_has_no_findings(self):
        self.assertEqual(check_plugin.check(ROOT), [])

    def test_outcome_sentence_is_short(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        outcome = check_plugin.outcome_sentence(manifest["description"])
        self.assertLessEqual(len(outcome.split()), 10)

    def test_every_skill_treats_input_as_data_and_package_requires_a_yes(self):
        texts = {p: p.read_text(encoding="utf-8").lower() for p in (ROOT / "skills").glob("*/SKILL.md")}
        for path, text in texts.items():
            self.assertIn("never instructions", text, path)
        self.assertTrue(any("yes" in text for text in texts.values()), "no skill states a yes-required approval rule")

    def test_readme_states_the_hermes_skill_namespace(self):
        import hashlib
        name = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["name"]
        namespace = f"agent-plugin-{name}-{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        self.assertIn(namespace + ":get-started", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_codex_install_uses_marketplace_add_then_plugin_add(self):
        name = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["name"]
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"codex plugin marketplace add KellerAI/{name} --ref", readme)
        self.assertIn(f"codex plugin add {name}@kellerai-{name}", readme)


class NegativeCases(unittest.TestCase):
    """Each case breaks one rule in a temporary copy and expects the check to fail."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / ROOT.name
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def append(path, text):
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text)

    def edit_manifest(self, **changes):
        path = self.root / "plugin.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(changes)
        path.write_text(json.dumps(data), encoding="utf-8")

    def assertFlags(self, fragment):
        errors = check_plugin.check(self.root)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_wrong_schema(self):
        self.edit_manifest(**{"$schema": "https://example.com/other.json"})
        self.assertFlags("$schema")

    def test_unknown_manifest_key(self):
        self.edit_manifest(hooks="./hooks.json")
        self.assertFlags("keys not allowed")

    def test_bad_name(self):
        self.edit_manifest(name="Weekly--Reviewer")
        self.assertFlags("kebab-case")

    def test_long_outcome_sentence(self):
        self.edit_manifest(description="This sentence is far too long to be a crisp outcome promise for anyone. Rest.")
        self.assertFlags("outcome sentence")

    def test_readme_promise_drift(self):
        readme = self.root / "README.md"
        outcome = check_plugin.outcome_sentence(json.loads((self.root / "plugin.json").read_text(encoding="utf-8"))["description"])
        text = readme.read_text(encoding="utf-8")
        readme.write_text(text.replace(outcome, "Something else.", 1), encoding="utf-8")
        self.assertFlags("README promise")

    def test_skill_name_mismatch(self):
        skill = self.root / "skills" / "get-started" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8").replace("name: get-started", "name: other", 1), encoding="utf-8")
        self.assertFlags("frontmatter name")

    def test_machine_path_leak(self):
        self.append(self.root / "skills" / "get-started" / "SKILL.md", "\nSee /home/box/shared/x\n")
        self.assertFlags("machine path")

    def test_ticket_id_leak(self):
        self.append(self.root / "README.md", "\nTracked in OPS-1020.\n")
        self.assertFlags("ticket id")

    def test_secret_like_token(self):
        self.append(self.root / "README.md", "\nghp_" + "a" * 36 + "\n")
        self.assertFlags("secret-like token")

    def test_private_term_from_local_file(self):
        (self.root / ".hygiene-terms").write_text("Projectcodename\n", encoding="utf-8")
        self.append(self.root / "README.md", "\nBuilt for projectcodename.\n")
        self.assertFlags("private term")

    def test_internal_marker(self):
        self.append(self.root / "README.md", "\nKeep private until launch.\n")
        self.assertFlags("internal marker")

    def test_em_dash(self):
        self.append(self.root / "README.md", "\nA \u2014 B\n")
        self.assertFlags("em-dash")

    def test_working_note_file(self):
        (self.root / "NOTES.md").write_text("status", encoding="utf-8")
        self.assertFlags("working-note file")

    def test_mcp_json_rejected_for_skills_only(self):
        (self.root / "mcp.json").write_text("{}", encoding="utf-8")
        self.assertFlags("skills-only")

    def test_elevenlabs_style_key_rejected(self):
        self.append(self.root / "README.md", "\nsk_" + "a" * 40 + "\n")
        self.assertFlags("secret-like token")

    def test_claude_md_rejected(self):
        (self.root / "CLAUDE.md").write_text("x", encoding="utf-8")
        self.assertFlags("CLAUDE.md")

    def test_marketplace_missing_policy(self):
        path = self.root / ".agents" / "plugins" / "marketplace.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["plugins"][0]["policy"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertFlags("policy.installation")

    def test_release_check_rejects_placeholder_pin(self):
        readme = self.root / "README.md"
        text = readme.read_text(encoding="utf-8")
        import re
        readme.write_text(re.sub(r"--ref [0-9a-f]{40}", "--ref <release-sha>", text), encoding="utf-8")
        self.assertTrue(any(e.startswith("release:") for e in check_plugin.check(self.root, release=True)))

    def test_release_check_rejects_mismatched_pins(self):
        readme = self.root / "README.md"
        text = readme.read_text(encoding="utf-8")
        import re
        pins = re.findall(r"--ref ([0-9a-f]{40})", text)
        readme.write_text(text.replace(pins[0], "b" * 40, 1), encoding="utf-8")
        self.assertTrue(any("same commit" in e for e in check_plugin.check(self.root, release=True)))

    def test_release_pin_accepts_full_sha(self):
        readme = self.root / "README.md"
        import re
        text = re.sub(r"--ref (?:[0-9a-f]{40}|<release-sha>)", "--ref " + "a" * 40, readme.read_text(encoding="utf-8"))
        readme.write_text(text, encoding="utf-8")
        self.assertEqual(check_plugin.check(self.root, release=True), [])


if __name__ == "__main__":
    unittest.main()
