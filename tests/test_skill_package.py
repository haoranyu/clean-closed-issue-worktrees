from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
