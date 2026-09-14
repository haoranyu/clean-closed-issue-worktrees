# Security Policy

## Supported versions

Security fixes are applied to the latest tagged release. Installations pinned to
an older release should update only after previewing the new skill payload.

## Tool permission boundary

The skill pre-approves only `Read` where supported. It does not pre-approve
arbitrary shell, Python, Git, write, or MCP tools. `allowed-tools` is additive
permission metadata, not a sandbox or a replacement for host permissions.
It cannot undo existing broad grants or bypass modes. Exact-plan user consent
and the cleanup engine's validation remain required even when the host allows
a command without prompting. Client support and verification limits are
documented in the skill's [tool permission reference](skills/clean-closed-issue-worktrees/references/tool-permissions.md).

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository. Please do not
open a public issue for a vulnerability that could cause unintended worktree or
branch removal, command injection, path traversal, credential exposure, or
bypass of the scan-confirm-execute boundary.

Include the affected version or commit, operating system, Git and Python
versions, a minimal reproduction, and the expected safety behavior. Do not
include real credentials or sensitive repository contents.

If you suspect unsafe cleanup behavior, stop before execution and retain the
generated scan or plan only if it contains no sensitive paths or repository
information.
