from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "clean-closed-issue-worktrees"
SKILL_FILE = SKILL_ROOT / "SKILL.md"


def frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise AssertionError(f"Missing frontmatter field: {key}")
    return match.group(1).strip()


class SkillPackageTests(unittest.TestCase):
    def test_plugin_manifests_share_identity_and_version(self) -> None:
        agent_plugin = json.loads(
            (REPOSITORY_ROOT / "plugin.json").read_text(encoding="utf-8")
        )
        claude_plugin = json.loads(
            (REPOSITORY_ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            agent_plugin["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(agent_plugin["name"], SKILL_ROOT.name)
        self.assertEqual(claude_plugin["name"], SKILL_ROOT.name)
        self.assertEqual(agent_plugin["version"], claude_plugin["version"])
        self.assertEqual(agent_plugin["repository"], claude_plugin["repository"])

    def test_payload_is_self_contained(self) -> None:
        expected = [
            SKILL_FILE,
            SKILL_ROOT / "LICENSE.txt",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "scripts" / "worktree_cleanup.py",
            SKILL_ROOT / "references" / "evidence-schema.md",
            SKILL_ROOT / "references" / "harness-detection.md",
            SKILL_ROOT / "references" / "provider-access.md",
        ]
        self.assertTrue(all(path.is_file() for path in expected))

    def test_frontmatter_is_portable(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        self.assertEqual(frontmatter_value(text, "name"), SKILL_ROOT.name)
        self.assertEqual(frontmatter_value(text, "license"), "MIT")
        self.assertLessEqual(len(frontmatter_value(text, "description")), 200)
        self.assertIn("Python 3.9+", text)

    def test_markdown_reference_links_resolve_inside_payload(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+)\)", text)
        self.assertTrue(links)
        for relative in links:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

    def test_openai_prompt_invokes_the_published_skill_name(self) -> None:
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$clean-closed-issue-worktrees", metadata)

    def test_cursor_harness_contract_is_documented(self) -> None:
        harness = (SKILL_ROOT / "references" / "harness-detection.md").read_text(
            encoding="utf-8"
        )
        skill = SKILL_FILE.read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Cursor", harness)
        for surface in (
            "Agents Window",
            "`/worktree`",
            "`/best-of-n`",
            "`--worktree",
            "isolated local subagent",
        ):
            self.assertIn(surface, harness)
        self.assertIn("~/.cursor/worktrees/<reponame>/<name>", harness)
        self.assertIn("CURSOR_WORKTREES_ROOT", harness)
        self.assertIn("never `not_managed`", harness)
        self.assertIn("resumable", harness)
        self.assertIn("explicitly completed or archived", harness)
        self.assertIn('runtime: "local"', harness)
        self.assertIn("current host", harness)
        self.assertIn("Cursor-hosted Cloud Agents", harness)
        self.assertIn("Cursor 3.5", harness)
        self.assertIn("Cursor", skill)
        self.assertIn("Generic local Git worktrees", readme)
        self.assertIn("First-class harness-state integration", readme)


if __name__ == "__main__":
    unittest.main()
