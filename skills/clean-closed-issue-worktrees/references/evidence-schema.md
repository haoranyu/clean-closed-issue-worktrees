# Selection evidence and execution plans

Read this reference immediately before `create-plan` or when diagnosing a refused selection.

## Selection JSON

Create this file only in a system temporary directory after the read-only scan. All paths must exactly match `scan.json`; do not construct paths from globs or unresolved variables.

```json
{
  "baseline": "upstream/main",
  "branch_action": "keep",
  "backup_orphans": false,
  "targets": [
    {
      "path": "/absolute/path/to/repo-worktree-123",
      "ignored_paths_approved": false,
      "risk_acknowledged": false,
      "evidence": {
        "mapping_confidence": "strong",
        "harness_name": "example-harness",
        "harness_state": "inactive",
        "issue": {
          "provider": "github",
          "repository_url": "https://github.com/owner/repo",
          "url": "https://github.com/owner/repo/issues/123",
          "number": 123,
          "kind": "issue",
          "state": "closed"
        },
        "linked_change": {
          "kind": "pull_request",
          "number": 456,
          "url": "https://github.com/owner/repo/pull/456",
          "state": "merged"
        }
      }
    }
  ]
}
```

### Required semantics

- `baseline`: the matched remote's verified default or relevant target branch. It is mandatory when `branch_action` is `delete`.
- `branch_action`: `keep` or `delete`. Ask every time; recommend `keep`.
- `backup_orphans`: a JSON boolean; set `true` only when the user explicitly approved creation of deterministic backup branches for detached orphan commits.
- `mapping_confidence`: use `strong` only for the evidence types in `SKILL.md`. Other mappings require `risk_acknowledged: true` after the user selects the review item.
- `harness_name`: optional normalized exact-path task owner such as `codex`, `claude-code`, `cursor`, or another harness identifier. Identifiers use lowercase alphanumeric tokens separated only by `.`, `_`, or `-`. Include it in new harness-derived evidence when the owner is known; it remains optional so the original Codex/Claude selection format stays valid. The scanner independently emits `managed_harness` as path provenance for recognized roots. The two fields may differ when one harness uses a checkout created by another, but `harness_state` must aggregate every known exact-path owner and `not_managed` must respect either field.
- `harness_state`: `inactive`, `not_managed`, `unknown`, or `active`. `active` is always refused and cannot be bypassed. `inactive` requires explicit task completion/archive with no live exact-path owner; new harness-derived evidence should also identify `harness_name`, but the field is not mandatory for compatibility with the original normalized selection contract. `unknown` requires explicit risk acknowledgement. Use `not_managed` only when the path is outside every recognized harness root and an exhaustive authoritative lookup finds no owner.
- A path under any scanner-recognized managed root, or mapped exactly to a harness by authoritative tooling, is never `not_managed`. With unavailable or incomplete task state, use `unknown`. When several task records map to one exact path, aggregate them according to every applicable harness-specific mapping; any active or waiting owner makes the combined state `active`.
- `harness_state` is the trusted normalized aggregate supplied by the agent layer. It must cover every scanner-recognized path owner and every exact-path task owner within the scope required by each applicable mapping. An inactive record from one harness does not replace a missing lookup for another. If required runtime/host identity or coverage cannot be established, the aggregate must be `unknown`. Cursor specifically requires current-local-host coverage and treats a resumable exact owner as `active`; see [harness-detection.md](harness-detection.md).
- `ignored_paths_approved`: a JSON boolean; set `true` only after the user reviewed sensitive/unknown ignored paths.
- `risk_acknowledged`: a JSON boolean recording an explicit user choice for a reported review condition. It is not a bypass for dirty, active, falsely unowned managed, locked, main/current, scan-anchor, symlinked, or broad paths. Quoted strings and numeric lookalikes are invalid approval evidence.
- `issue.kind`: `issue`, `pull_request`, or `merge_request`. An issue must be closed; a PR/MR must be merged.
- `linked_change`: optional. A non-merged linked change requires explicit risk acknowledgement and remains a review item.

## Plan lifecycle

`create-plan` rescans the repository, enforces local invariants, and writes a schema-versioned snapshot containing:

- repository common-dir identity;
- resolved baseline identity;
- exact path and resolved path;
- recognized managed-harness path provenance;
- HEAD and branch/detached state;
- ignored-path fingerprint;
- branch action and any backup branch;
- estimated reclaimable bytes;
- a random `plan_id`.

Show the user the exact targets, branch behavior, backup operations, estimate, and `plan_id` before execution. The later execution call must repeat the exact ID with `--confirm-plan`.

`create-plan` writes plan schema 2. `execute` also accepts a schema-1 plan from the original skill, but only through the same full rescan and current evidence validation used for schema 2. Because schema 1 has no managed-root snapshot, execution refuses it when a target is now recognized as managed; recreate the plan with the current skill in that case. Unsupported schema versions are rejected. Execution also rechecks the main worktree, fresh scan anchor, and execution-time current working directory. Any protected target, changed path, managed-harness ownership, HEAD, branch, status, ignored-path set, retaining refs, baseline, lock/prunable state, evidence validity, or repository identity refuses the entire batch. Once execution begins, a mid-batch Git failure stops immediately; Git worktree removal is not atomic.

## Branch deletion

`branch_action: "delete"` is allowed only when each target HEAD is an ancestor of the selected baseline. Execution still uses `git branch -d`; a refusal is a safe failure. Never change the script to use `-D` as a convenience.

## Detached orphan backup

With explicit approval and `backup_orphans: true`, the plan assigns:

```text
worktree-cleanup/backup-YYYYMMDD-<12-char-sha>
```

The branch is created before removal and the command refuses to overwrite an existing ref.
