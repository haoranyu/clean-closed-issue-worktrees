# Clean Closed Issue Worktrees

A safety-first agent skill for auditing and removing Git worktrees associated with closed GitHub or GitLab issues.

It is designed for Codex, Claude Code, and other skill-capable agent harnesses. Provider access stays in the agent layer, while a deterministic Python script owns local Git inspection, snapshot validation, backup refs, and removal.

## Why this exists

Closed issues often leave behind worktrees containing dependency folders and build caches. Blind cleanup is dangerous: a clean `git status` can hide ignored local data, a detached HEAD can be the only ref to a commit, and an apparently idle worktree can still belong to an active agent task.

This skill enforces a two-phase workflow:

1. Scan and classify every worktree without modifying Git state.
2. Show exact paths, risks, issue state, and estimated reclaimable space.
3. Ask the user to confirm an exact batch and whether branches should be retained.
4. Revalidate the entire batch, then remove only unchanged, approved targets.

The default recommendation is to remove worktrees while retaining local branches.

## Safety properties

- Only closed ordinary issues or merged PRs/MRs qualify.
- Dirty, locked, current, main, active-task, and broad paths are refused.
- Unknown harness state and ambiguous issue mapping are review conditions.
- Ignored `.env`, database, key, credential, and unknown paths require explicit review.
- Detached orphan commits can be protected with deterministic backup branches.
- Branch deletion uses only `git branch -d`; force deletion is not implemented.
- Worktree removal uses only exact paths returned by Git; recursive filesystem deletion is not implemented.
- A changed snapshot aborts the whole batch before the first removal.
- Mid-batch failures stop immediately and report removed, failed, and untouched targets.

## Install

Clone or copy this directory into the skill directory used by your agent harness. Examples:

```bash
git clone https://github.com/haoranyu/clean-closed-issue-worktrees.git \
  ~/.codex/skills/clean-closed-issue-worktrees
```

```bash
git clone https://github.com/haoranyu/clean-closed-issue-worktrees.git \
  ~/.claude/skills/clean-closed-issue-worktrees
```

Then ask the agent to use `$clean-closed-issue-worktrees` with a local repository and a GitHub/GitLab issue-list URL.

## Provider routing

The skill prefers, in order:

1. GitHub/GitLab-specific skills, connectors, or MCP servers;
2. an already authenticated `gh` or `glab`;
3. official read-only APIs for public repositories;
4. browser MCP or a harness-provided browser;
5. a user-provided issue export.

The script never reads tokens, credential stores, browser cookies, or issue pages. This separation keeps it portable across harnesses.

## Local script

Requirements: Python 3.9+ and Git.

Read-only inventory:

```bash
python3 scripts/worktree_cleanup.py scan \
  --repo /path/to/repository \
  --baseline upstream/main \
  --json-out /tmp/worktree-scan.json \
  --markdown-out /tmp/worktree-scan.md \
  --stdout none
```

After provider verification and user review, the agent creates a normalized selection in a temporary directory:

```bash
python3 scripts/worktree_cleanup.py create-plan \
  --repo /path/to/repository \
  --selection /tmp/selection.json \
  --output /tmp/plan.json
```

After the user confirms that exact plan:

```bash
python3 scripts/worktree_cleanup.py execute \
  --plan /tmp/plan.json \
  --confirm-plan <plan-id> \
  --delete-plan-on-success
```

See [SKILL.md](SKILL.md) for the agent workflow and [references/evidence-schema.md](references/evidence-schema.md) for the normalized selection format.

## Test

Tests create isolated temporary repositories and never operate on the checkout containing this skill.

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the suite on Linux, macOS, and Windows.

## License

MIT
