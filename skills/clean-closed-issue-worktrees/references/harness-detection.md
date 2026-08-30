# Agent harness detection

Read this reference whenever a worktree may be managed by an agent harness. Apply the general rules first, then every available harness-specific mapping.

## General rule

An issue being closed does not prove that the worktree's current agent task is complete. Harness task state overrides issue-derived cleanup confidence.

- **Active**: task/session reports running, active, waiting for approval/input, or recent live progress. Classify as **Keep**.
- **Inactive**: harness explicitly reports completed or archived and no live operation owns the worktree.
- **Unknown**: the task exists but completion is not explicit, the harness reports an unloaded/idle historical entry that can be resumed, or task tooling is unavailable. Classify as **Needs review**.
- **Not managed**: no harness metadata maps to the path and it is outside recognized harness-managed directories.

Do not use process names, `lsof`, modification time, terminal silence, or a clean Git status as the sole proof that a task ended.
Never label a path under a recognized harness-managed root as `not_managed`. Harness-specific rules below may be stricter than these general defaults.

## Integration model

The cleanup policy is editor-neutral. A documented root adapter may attach `managed_harness` path provenance, while the agent layer supplies an exact-path `harness_name` and aggregate `harness_state`. These normalized fields form the interface to the shared eligibility and deletion policy.

Named sections below are adapters, not an allowlist. A new editor or harness can add stable-root recognition, authoritative task-state mapping, or both without changing the core cleanup rules. Generic Git-registered worktrees remain supported even when no named adapter exists.

## Codex

When Codex thread/task tools are available:

1. List tasks and map each exact `cwd` to the registered worktree path.
2. Treat `active`, running, waiting, or needs-attention tasks as active.
3. Treat archived/completed tasks as inactive. Record `harness_name: "codex"` in new evidence; the original selection format without that optional field remains valid.
4. Treat `notLoaded`, idle-but-resumable, missing pagination coverage, or ambiguous duplicate tasks as unknown unless the user confirms completion.
5. Never remove the calling task's own worktree.

If the user later asks to archive or otherwise manage a Codex task, use the harness's task/thread tools; worktree cleanup does not imply task archival permission.

## Claude Code

Use any available session/task metadata and exact working-directory mapping. Record `harness_name: "claude-code"` in new evidence. A path under `.claude/worktrees` is harness-managed even if no process is visible. If no authoritative session state is available, mark it unknown and request confirmation after presenting the scan. The original selection format without the optional harness name remains valid.

## Cursor

Cursor can create local Git worktrees from all of these surfaces:

- Agents Window worktrees;
- the IDE `/worktree` command;
- each candidate created by the IDE `/best-of-n` command;
- Cursor CLI `-w` or `--worktree [name]`;
- isolated local subagent environments when Cursor gives the subagent a separate Git worktree.

Cursor-hosted Cloud Agents and documented `/in-cloud` cloud subagents are out of scope for local cleanup. Their remote VM clones and branches are not Git worktrees registered in the local repository being scanned. Do not extend that exclusion to a self-hosted or Remote Control worker: if its exact checkout is locally registered, apply the normal exact-path ownership rules and classify unavailable state as `unknown`.

### Ownership

Cursor documents CLI worktrees under `~/.cursor/worktrees/<reponame>/<name>`, alongside editor-created worktrees. Expand `~` with the current runtime's user home and compare both absolute and resolved paths by containment; do not hard-code a macOS, Linux, or Windows home prefix. For the bundled scanner this is `$HOME/.cursor/worktrees` on macOS, Linux, and WSL, and `%USERPROFILE%\.cursor\worktrees` on native Windows. WSL and native Windows have distinct runtime homes; use an explicit absolute compatibility override for a known cross-runtime path instead of guessing `%APPDATA%`, a drive, or a Cursor installation directory. Native `pathlib` comparison handles Windows drive letters, separators, case-insensitivity, spaces, and resolved junction/symlink paths. The scanner reports `managed_harness: "cursor"` for registered paths under the runtime root, including a root reached through a symlink or junction.

Cursor currently documents no managed-root relocation option. Some installed CLI builds expose an undocumented `CURSOR_WORKTREES_ROOT` environment override; as a fail-closed compatibility measure, the scanner recognizes it only when it is present and absolute, and refuses an ambiguous relative value. Do not infer this override when it is absent or present it as a supported public API.

`.cursor/worktrees.json` documents setup commands, including operating-system-specific commands, and Cursor CLI `--workspace` documents source-repository selection. Do not reinterpret these knobs, `CURSOR_CONFIG_DIR`, editor settings, setup-script paths, repository names, or directory basenames as worktree-root overrides.

An exact path reported by authoritative Cursor task/session tooling is Cursor-managed even if it lies outside the documented root, including an isolated local subagent path. Record `harness_name: "cursor"` in its selection evidence. A registered path under the documented root remains Cursor-managed when task tooling is missing, incomplete, or uses a different store; classify it as `unknown`, never `not_managed`.

### Exact task-state mapping

When authoritative task, session, SDK, or hook-backed state is available in the current Cursor environment:

1. Restrict records to `runtime: "local"` on the current host before comparing paths. A cloud or different-worker record with the same path string does not own the local checkout. For self-hosted or Remote Control workers, confirm that the record belongs to this host; if the tool cannot establish runtime/host identity, classify state as `unknown`.
2. Enumerate all available records and pagination in the applicable local store, then compare each exact `cwd`, workspace root, or documented worktree path with the exact registered Git worktree path. Repository-name or branch-name similarity is not a match.
3. Treat an exact owner that is running, waiting on background work, waiting for approval/input, or otherwise live as `active`. As this skill's conservative safety policy, also promote a resumable exact owner to the internal `active` classification even when Cursor labels its latest run idle or finished. If duplicate records own the path, any live or resumable owner wins.
4. Treat the path as `inactive` only when the durable task is explicitly completed or archived and no live or resumable task owns that exact path. A terminal run alone is insufficient when its conversation can still resume.
5. Treat unavailable tooling, incomplete enumeration, a different/custom task store, ambiguous ownership, or unrecognized/error/cancelled/expired-only state as `unknown`.
6. Keep the calling worktree and scan anchor unconditionally, regardless of reported task state.

Cursor CLI history commands such as `agent ls` and `--resume` prove that conversations can be resumed; they do not provide exhaustive path ownership or prove inactivity.

### Cursor automatic cleanup

Cursor 3.5 and later periodically rediscovers the machine worktree root and can automatically clean older worktrees to enforce a machine-wide maximum across all workspaces. Worktrees created outside the manager, including `/worktree` or direct `git worktree add` checkouts under the discovered root, may be eligible.

Age, discovery timestamps, cleanup eligibility, cleanup interval, and the machine-wide count cap are storage-policy signals, not evidence that a task is inactive. If Cursor concurrently removes or changes a selected worktree, the cleanup plan's normal snapshot revalidation must abort.

Official references: [worktrees](https://cursor.com/docs/configuration/worktrees), [Cursor CLI worktrees](https://cursor.com/docs/cli/using), [native Windows CLI installation](https://cursor.com/docs/cli/installation), [platform-specific CLI configuration](https://cursor.com/docs/cli/reference/configuration), [subagents](https://cursor.com/docs/subagents), [Python SDK](https://cursor.com/docs/sdk/python), [hooks](https://cursor.com/docs/hooks), and [self-hosted Cloud Agents](https://cursor.com/docs/cloud-agent/self-hosted).

## Other harnesses

Recognize harness-managed paths and metadata when available, but do not invent status mappings. The named integrations above are non-exhaustive. For an unlisted editor or harness, use authoritative exact-path metadata when available and classify uncertain ownership as `unknown`; never fall back to process guessing.
