# Tool permissions

The skill declares `allowed-tools: Read`. This is a single scalar tool name,
so it avoids differences between clients' list separators. It grants no shell,
interpreter, Git, write, or provider/MCP permission. Reading skill references is
useful without automatically approving the cleanup script's `execute` command.

`allowed-tools` is pre-approval metadata, not a sandbox or a tool denylist.
It does not revoke existing host permissions, override bypass modes, or prove
that every omitted tool will prompt. Keep exact-target user consent and the
script's plan validation even when the host already permits a command.

## Client support

Documentation checked on 2026-09-14:

| Client | Meaning and limits |
| --- | --- |
| GitHub Copilot CLI | Supports `allowed-tools`. CLI 1.0.83's native parser accepts `Read` with no unknown tools and produces no additional permission rules. Reads already require no extra grant in this parser; `Bash` instead produces a shell grant. The declaration deliberately adds no execution approval. Other Copilot surfaces were not runtime-tested. |
| Claude Code | Documents `Read` and scalar strings. The field grants permission for the invoking turn; omitted tools remain available under existing permission settings. Claude Code 2.1.251 is installed in the validation environment, but an interactive permission workflow was not tested. |
| Codex and Cursor | Do not assume this field is enforced or that tool names are shared. No runtime enforcement claim is made for these clients. Use their normal tool permissions and the same scan-confirm-execute contract. |

The Agent Skills specification calls this field experimental and notes that
support varies by implementation. A client ignoring it receives the same safety
instructions and deterministic engine checks as before. If a client reports an
unknown tool, use its normal permission flow; do not replace the declaration
with a wildcard or blanket shell grant to silence the warning.

Provider and harness tools remain available through their documented routes,
subject to host permissions. An unavailable lookup still means **Needs review**;
it is not a reason to skip evidence or relabel a managed path as unmanaged.

## Verification

Package tests enforce the single read-only grant and resolve this reference.
The existing temporary-repository suite exercises scan, plan validation,
protected worktrees, and approved execution. Those tests do not prove a client's
interactive permission behavior.

Copilot CLI 1.0.83's distributed native parser was checked with the actual
frontmatter. `Read` yielded `rules: []`, `unknownTools: []`, and
`parsedSpecs: ["Read"]`; a `Bash` control yielded a `shell` rule. This verifies
parsing and absence of an added execution grant, not an end-to-end session.

Before claiming interactive acceptance, use a disposable repository and record
client version and permission settings:

1. Load the skill with default permissions and no broad execution grants.
2. Complete an inventory and verify that no worktree or branch was removed.
3. Propose an exact plan; verify that loading the skill has not automatically
   approved its execution command. Cancel any tool prompt and verify the target
   still exists.
4. Explicitly approve the exact plan and required host tool request, then verify
   only the selected disposable worktree was removed and branch behavior matches
   the plan.

This interactive check remains pending; do not substitute package tests or the
parser check for it.

## Sources

- [Agent Skills specification](https://agentskills.io/specification)
- [Copilot skill tool pre-approvals](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills#enabling-a-skill-to-run-a-script)
- [Copilot CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference#skills-reference)
- [Claude Code skill permissions](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill)
- [Cursor skills](https://cursor.com/docs/skills)
