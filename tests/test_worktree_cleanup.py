from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from typing import Optional


SCRIPT = Path(__file__).parents[1] / "scripts" / "worktree_cleanup.py"
SPEC = importlib.util.spec_from_file_location("worktree_cleanup", SCRIPT)
assert SPEC and SPEC.loader
cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup)


def command(*args: str, cwd: Optional[Path] = None) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"Command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result.stdout.strip()


class RepositoryFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.main = root / "main repo"
        command("git", "init", "-b", "main", str(self.main))
        command("git", "config", "user.email", "tests@example.com", cwd=self.main)
        command("git", "config", "user.name", "Skill Tests", cwd=self.main)
        (self.main / "tracked.txt").write_text("base\n", encoding="utf-8")
        command("git", "add", "tracked.txt", cwd=self.main)
        command("git", "commit", "-m", "Initial commit", cwd=self.main)

    def commit_file(self, relative: str, content: str, message: str, *, cwd: Path | None = None) -> None:
        target_cwd = cwd or self.main
        target = target_cwd / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        command("git", "add", relative, cwd=target_cwd)
        command("git", "commit", "-m", message, cwd=target_cwd)

    def add_branch_worktree(self, branch: str, directory: str) -> Path:
        target = self.root / directory
        command("git", "branch", branch, cwd=self.main)
        command("git", "worktree", "add", str(target), branch, cwd=self.main)
        return target

    def add_detached_worktree(self, directory: str) -> Path:
        target = self.root / directory
        command("git", "worktree", "add", "--detach", str(target), "main", cwd=self.main)
        return target


def evidence(number: int = 123, **overrides: object) -> dict:
    value = {
        "mapping_confidence": "strong",
        "harness_state": "not_managed",
        "issue": {
            "provider": "github",
            "repository_url": "https://github.com/example/repo",
            "url": f"https://github.com/example/repo/issues/{number}",
            "number": number,
            "kind": "issue",
            "state": "closed",
        },
    }
    value.update(overrides)
    return value


def selection(path: Path, **overrides: object) -> dict:
    value = {
        "baseline": "main",
        "branch_action": "keep",
        "backup_orphans": False,
        "targets": [
            {
                "path": str(path.resolve()),
                "ignored_paths_approved": False,
                "risk_acknowledged": False,
                "evidence": evidence(),
            }
        ],
    }
    value.update(overrides)
    return value


class WorktreeCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = RepositoryFixture(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_selection(self, value: dict) -> Path:
        path = self.root / "selection.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def create_plan(self, value: dict) -> tuple[Path, dict]:
        selection_path = self.write_selection(value)
        plan_path = self.root / "plan.json"
        plan = cleanup.create_plan(str(self.repo.main), selection_path, plan_path)
        return plan_path, plan

    def test_scan_finds_issue_evidence_and_ignored_risks(self) -> None:
        (self.repo.main / ".gitignore").write_text("node_modules/\n.env.*\n", encoding="utf-8")
        command("git", "add", ".gitignore", cwd=self.repo.main)
        command("git", "commit", "-m", "Add ignores", cwd=self.repo.main)
        target = self.repo.add_branch_worktree("123-fix-widget", "work tree-测试")
        (target / "node_modules").mkdir()
        (target / "node_modules" / "cache.bin").write_bytes(b"cache")
        (target / ".env.local").write_text("SECRET=not-read-by-script\n", encoding="utf-8")

        inventory = cleanup.scan_repository(self.repo.main, baseline="main")
        item = next(value for value in inventory["worktrees"] if value["path"] == str(target.resolve()))

        self.assertFalse(item["dirty"])
        self.assertEqual(item["issue_evidence"]["branch_ids"], [123])
        self.assertIn("node_modules/", item["ignored"]["regenerable"])
        self.assertIn(".env.local", item["ignored"]["sensitive"])
        self.assertGreater(item["size_bytes"], 0)

    def test_plan_refuses_dirty_worktree(self) -> None:
        target = self.repo.add_branch_worktree("123-dirty", "dirty-wt")
        (target / "untracked.txt").write_text("work\n", encoding="utf-8")

        with self.assertRaisesRegex(cleanup.CleanupError, "tracked or untracked"):
            self.create_plan(selection(target))

    def test_plan_refuses_unknown_ignored_content_without_approval(self) -> None:
        (self.repo.main / ".gitignore").write_text("private-output/\n", encoding="utf-8")
        command("git", "add", ".gitignore", cwd=self.repo.main)
        command("git", "commit", "-m", "Ignore private output", cwd=self.repo.main)
        target = self.repo.add_branch_worktree("123-private", "private-wt")
        (target / "private-output").mkdir()
        (target / "private-output" / "value.txt").write_text("local\n", encoding="utf-8")

        with self.assertRaisesRegex(cleanup.CleanupError, "unapproved ignored"):
            self.create_plan(selection(target))

    def test_execute_removes_worktree_and_keeps_branch(self) -> None:
        target = self.repo.add_branch_worktree("123-keep-branch", "remove me")
        plan_path, plan = self.create_plan(selection(target))

        result, code = cleanup.execute_plan(plan_path, plan["plan_id"], None, True)

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(target.exists())
        self.assertFalse(plan_path.exists())
        self.assertEqual(command("git", "branch", "--list", "123-keep-branch", cwd=self.repo.main), "123-keep-branch")

    def test_execute_rejects_changed_head_before_any_removal(self) -> None:
        target = self.repo.add_branch_worktree("123-changing", "changing-wt")
        plan_path, plan = self.create_plan(selection(target))
        self.repo.commit_file("new.txt", "new\n", "Change after confirmation", cwd=target)

        with self.assertRaisesRegex(cleanup.CleanupError, "HEAD changed"):
            cleanup.execute_plan(plan_path, plan["plan_id"], None, False)
        self.assertTrue(target.exists())

    def test_execute_requires_exact_plan_id(self) -> None:
        target = self.repo.add_branch_worktree("123-confirm", "confirm-wt")
        plan_path, _ = self.create_plan(selection(target))

        with self.assertRaisesRegex(cleanup.CleanupError, "exactly match"):
            cleanup.execute_plan(plan_path, "wrong-plan-id", None, False)
        self.assertTrue(target.exists())

    def test_batch_preflight_failure_removes_nothing(self) -> None:
        first = self.repo.add_branch_worktree("123-first", "first-wt")
        second = self.repo.add_branch_worktree("124-second", "second-wt")
        value = selection(first)
        value["targets"].append(
            {
                "path": str(second.resolve()),
                "ignored_paths_approved": False,
                "risk_acknowledged": False,
                "evidence": evidence(124),
            }
        )
        plan_path, plan = self.create_plan(value)
        self.repo.commit_file("changed.txt", "changed\n", "Change second", cwd=second)

        with self.assertRaisesRegex(cleanup.CleanupError, "HEAD changed"):
            cleanup.execute_plan(plan_path, plan["plan_id"], None, False)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())

    def test_baseline_move_aborts_confirmed_plan(self) -> None:
        target = self.repo.add_branch_worktree("123-baseline", "baseline-wt")
        plan_path, plan = self.create_plan(selection(target))
        self.repo.commit_file("later.txt", "later\n", "Move baseline")

        with self.assertRaisesRegex(cleanup.CleanupError, "Baseline moved"):
            cleanup.execute_plan(plan_path, plan["plan_id"], None, False)
        self.assertTrue(target.exists())

    def test_detached_head_losing_retaining_ref_aborts(self) -> None:
        target = self.repo.add_detached_worktree("retained-detached-wt")
        self.repo.commit_file("detached.txt", "unique\n", "Detached work", cwd=target)
        detached_head = command("git", "rev-parse", "HEAD", cwd=target)
        command("git", "branch", "temporary-retainer", detached_head, cwd=self.repo.main)
        plan_path, plan = self.create_plan(selection(target))
        command("git", "branch", "-D", "temporary-retainer", cwd=self.repo.main)

        with self.assertRaisesRegex(cleanup.CleanupError, "lost all retaining refs"):
            cleanup.execute_plan(plan_path, plan["plan_id"], None, False)
        self.assertTrue(target.exists())

    def test_main_worktree_is_never_selectable(self) -> None:
        with self.assertRaisesRegex(cleanup.CleanupError, "main worktree"):
            self.create_plan(selection(self.repo.main))

    def test_backup_branch_preserves_detached_orphan(self) -> None:
        target = self.repo.add_detached_worktree("orphan-wt")
        self.repo.commit_file("orphan.txt", "unique\n", "Fix orphan. Closes #123", cwd=target)
        value = selection(target, backup_orphans=True)
        plan_path, plan = self.create_plan(value)
        backup = plan["targets"][0]["backup_branch"]

        result, code = cleanup.execute_plan(plan_path, plan["plan_id"], None, False)

        self.assertEqual(code, 0)
        self.assertFalse(target.exists())
        self.assertEqual(result["created_backups"][0]["branch"], backup)
        self.assertTrue(command("git", "show-ref", "--verify", f"refs/heads/{backup}", cwd=self.repo.main))

    def test_branch_delete_only_after_ancestry_and_uses_safe_delete(self) -> None:
        target = self.repo.add_branch_worktree("123-merged", "merged-wt")
        self.repo.commit_file("feature.txt", "done\n", "Finish #123", cwd=target)
        command("git", "merge", "--no-ff", "123-merged", "-m", "Merge issue 123", cwd=self.repo.main)
        value = selection(target, branch_action="delete")
        plan_path, plan = self.create_plan(value)

        result, code = cleanup.execute_plan(plan_path, plan["plan_id"], None, False)

        self.assertEqual(code, 0)
        self.assertTrue(result["removed"][0]["branch_deleted"])
        self.assertEqual(command("git", "branch", "--list", "123-merged", cwd=self.repo.main), "")

    def test_branch_delete_refuses_unique_commits(self) -> None:
        target = self.repo.add_branch_worktree("123-unmerged", "unmerged-wt")
        self.repo.commit_file("unique.txt", "unique\n", "Unique work", cwd=target)

        with self.assertRaisesRegex(cleanup.CleanupError, "Git ancestry"):
            self.create_plan(selection(target, branch_action="delete"))

    def test_closed_unmerged_pull_request_is_refused(self) -> None:
        target = self.repo.add_branch_worktree("123-closed-pr", "closed-pr-wt")
        bad_evidence = evidence(
            issue={
                "provider": "github",
                "repository_url": "https://github.com/example/repo",
                "url": "https://github.com/example/repo/pull/123",
                "number": 123,
                "kind": "pull_request",
                "state": "closed",
            }
        )
        value = selection(target)
        value["targets"][0]["evidence"] = bad_evidence

        with self.assertRaisesRegex(cleanup.CleanupError, "not eligible"):
            self.create_plan(value)

    def test_active_harness_is_always_refused(self) -> None:
        target = self.repo.add_branch_worktree("123-active", "active-wt")
        value = selection(target)
        value["targets"][0]["risk_acknowledged"] = True
        value["targets"][0]["evidence"]["harness_state"] = "active"

        with self.assertRaisesRegex(cleanup.CleanupError, "active harness"):
            self.create_plan(value)

    def test_unmerged_linked_change_requires_acknowledgement(self) -> None:
        target = self.repo.add_branch_worktree("123-linked", "linked-wt")
        value = selection(target)
        value["targets"][0]["evidence"]["linked_change"] = {
            "kind": "pull_request",
            "number": 456,
            "url": "https://github.com/example/repo/pull/456",
            "state": "closed",
        }

        with self.assertRaisesRegex(cleanup.CleanupError, "Linked PR/MR is not merged"):
            self.create_plan(value)


if __name__ == "__main__":
    unittest.main()
