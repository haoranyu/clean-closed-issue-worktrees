from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "clean-closed-issue-worktrees"
    / "scripts"
    / "worktree_cleanup.py"
)

SPEC = importlib.util.spec_from_file_location("worktree_cleanup", SCRIPT)
assert SPEC and SPEC.loader

worktree_cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worktree_cleanup)


def command(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed: {args}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    return result.stdout.strip()


class NestedIgnoredReproTest(unittest.TestCase):
    def test_nested_sensitive_file_is_surfaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            worktree = root / "worktree"

            command("git", "init", "-b", "main", str(repo))
            command(
                "git",
                "config",
                "user.email",
                "tests@example.com",
                cwd=repo,
            )
            command(
                "git",
                "config",
                "user.name",
                "Skill Tests",
                cwd=repo,
            )

            (repo / ".gitignore").write_text(
                "node_modules/\n",
                encoding="utf-8",
            )
            (repo / "tracked.txt").write_text(
                "base\n",
                encoding="utf-8",
            )

            command("git", "add", ".", cwd=repo)
            command(
                "git",
                "commit",
                "-m",
                "Add ignore rule",
                cwd=repo,
            )

            command(
                "git",
                "branch",
                "123-security-repro",
                cwd=repo,
            )

            command(
                "git",
                "worktree",
                "add",
                str(worktree),
                "123-security-repro",
                cwd=repo,
            )

            secret = (
                worktree
                / "node_modules"
                / "fake-package"
                / ".env"
            )
            secret.parent.mkdir(parents=True)
            secret.write_text(
                "API_KEY=THIS_IS_A_FAKE_SECRET\n",
                encoding="utf-8",
            )

            inventory = worktree_cleanup.scan_repository(repo)

            item = next(
                item
                for item in inventory["worktrees"]
                if item["path"] == str(worktree.resolve())
            )

            self.assertFalse(item["dirty"])

            self.assertIn(
                "node_modules/fake-package/.env",
                item["ignored_entries"],
            )

            self.assertIn(
                "node_modules/fake-package/.env",
                item["ignored"]["sensitive"],
            )


if __name__ == "__main__":
    unittest.main()