# Clean Closed Issue Worktrees

A safety-first agent skill for auditing and removing Git worktrees associated with closed GitHub or GitLab issues.

It is designed for Codex, Claude Code, Cursor, and other skill-capable agent harnesses. Provider and live-task access stay in the agent layer, while a deterministic Python script owns local Git inspection, recognized Cursor-root detection, snapshot validation, backup refs, and removal.

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
- Scanner-recognized Cursor roots cannot be mislabeled as unmanaged; other harness roots follow the same fail-closed agent workflow.
- Ignored `.env`, database, key, credential, and unknown paths require explicit review.
- Detached orphan commits can be protected with deterministic backup branches.
- Branch deletion uses only `git branch -d`; force deletion is not implemented.
- Worktree removal uses only exact paths returned by Git; recursive filesystem deletion is not implemented.
- A changed snapshot aborts the whole batch before the first removal.
- Mid-batch failures stop immediately and report removed, failed, and untouched targets.

## Install

Requires GitHub CLI 2.90.0 or later. Preview the complete skill payload before installing it:

```bash
gh skill preview haoranyu/clean-closed-issue-worktrees \
  clean-closed-issue-worktrees
```

Install and pin the audited `v0.1.2` release for Codex:

```bash
gh skill install haoranyu/clean-closed-issue-worktrees \
  clean-closed-issue-worktrees@v0.1.2 \
  --agent codex --scope user
```

Or for Claude Code:

```bash
gh skill install haoranyu/clean-closed-issue-worktrees \
  clean-closed-issue-worktrees@v0.1.2 \
  --agent claude-code --scope user
```

With Node.js 22.20 or later, the cross-agent `skills` CLI is another option:

```bash
npx skills add haoranyu/clean-closed-issue-worktrees \
  --skill clean-closed-issue-worktrees --agent codex --global
```

### Plugin marketplaces

This repository is also packaged as a portable Agent Plugin for Cursor and as
a Claude Code plugin. Both manifests discover the same
`skills/clean-closed-issue-worktrees` payload; no skill logic is duplicated.

For local Cursor testing, clone the repository and link it into Cursor's local
plugin directory, then reload Cursor:

```bash
ln -s /absolute/path/to/clean-closed-issue-worktrees \
  ~/.cursor/plugins/local/clean-closed-issue-worktrees
```

For local Claude Code testing:

```bash
claude --plugin-dir /absolute/path/to/clean-closed-issue-worktrees
```

Marketplace installation instructions will be added after the Cursor and
Claude community reviews approve the plugin.

For manual installation, download the versioned source archive from the
[`v0.1.2` release](https://github.com/haoranyu/clean-closed-issue-worktrees/releases/tag/v0.1.2)
and copy its `skills/clean-closed-issue-worktrees` directory into the skill
directory used by your agent. Do not install the entire repository: the payload is only
[`skills/clean-closed-issue-worktrees`](skills/clean-closed-issue-worktrees).

Then ask the agent to use `$clean-closed-issue-worktrees` with a local repository and a GitHub/GitLab issue-list URL.

## Compatibility

| Surface | Status |
| --- | --- |
| GitHub, GitLab issue and PR/MR state | Supported through the agent's provider skill, MCP, CLI, API, or browser fallback |
| Generic local Git worktrees | The engine can inspect and remove any Git-registered worktree, regardless of creator; generic Git compatibility alone does not prove task inactivity |
| First-class harness-state integration | Codex, Claude Code, and Cursor have explicit ownership and state mappings; when authoritative host tooling is unavailable, recognized managed paths remain **Needs review** |
| Cursor local worktrees | Installable as an Agent Skill or Agent Plugin; Agents Window, IDE `/worktree`, `/best-of-n`, and CLI `--worktree` are covered through the documented `~/.cursor/worktrees` root and an explicit absolute `CURSOR_WORKTREES_ROOT` compatibility override when present. An isolated local subagent is covered when a recognized root contains it or authoritative metadata maps its exact path; otherwise state fails closed to **Needs review** |
| Remote Cursor Cloud Agents | Cursor-hosted and `/in-cloud` VM clones are out of local cleanup scope; an exact locally registered self-hosted/Remote Control checkout still follows normal fail-closed ownership rules |
| Codex and Claude Code | Installable with `gh skill`; their existing task/session mapping rules are unchanged |
| Other Agent Skills clients | Standard `SKILL.md` payload; install manually or with a compatible skill installer |
| Local runtime | Git and Python 3.9+ |
| Script/package CI | Ubuntu, macOS, and Windows; live host task/session integrations are not exercised in CI |

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

On Windows, if `python3` opens the Microsoft Store or does not resolve to your installed interpreter, substitute `py -3` for `python3` in the commands below.

Read-only inventory:

From this repository checkout:

```bash
python3 skills/clean-closed-issue-worktrees/scripts/worktree_cleanup.py scan \
  --repo /path/to/repository \
  --baseline upstream/main \
  --json-out /tmp/worktree-scan.json \
  --markdown-out /tmp/worktree-scan.md \
  --stdout none
```

After provider verification and user review, the agent creates a normalized selection in a temporary directory:

```bash
python3 skills/clean-closed-issue-worktrees/scripts/worktree_cleanup.py create-plan \
  --repo /path/to/repository \
  --selection /tmp/selection.json \
  --output /tmp/plan.json
```

After the user confirms that exact plan:

```bash
python3 skills/clean-closed-issue-worktrees/scripts/worktree_cleanup.py execute \
  --plan /tmp/plan.json \
  --confirm-plan <plan-id> \
  --delete-plan-on-success
```

See [SKILL.md](skills/clean-closed-issue-worktrees/SKILL.md) for the agent workflow and [references/evidence-schema.md](skills/clean-closed-issue-worktrees/references/evidence-schema.md) for the normalized selection format.

## Test

Tests create isolated temporary repositories and never operate on the checkout containing this skill.

```bash
python3 -m unittest discover -s tests -v
```

On Windows, if `python3` opens the Microsoft Store or does not resolve to your installed interpreter, use `py -3` instead:

```powershell
py -3 -m unittest discover -s tests -v
```

GitHub Actions runs the suite on Linux, macOS, and Windows.

## License

MIT
