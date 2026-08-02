# Plugin and skill execution evidence

Updated: 2026-08-02

| Capability | Discovery and invocation evidence | Current status |
|---|---|---|
| Superpowers | Read brainstorming, writing-plans, executing-plans, worktrees, TDD, systematic-debugging, review reception/request, branch finish, and verification guidance. The user-supplied approved design and plan are being executed inline. Worktree and TDD red/green gates were invoked. | Active |
| CodeRabbit | Read the review skill. CLI was absent on Windows; official installer rejected MSYS with `Unsupported operating system: msys_nt-10.0-26300`. WSL installation produced a binary that exits with `Illegal instruction (core dumped)`. | Unavailable; no result is represented as CodeRabbit output |
| Codex Security | Read and invoked the threat-model and diff-scan workflows. The diff workspace and preflight started, and defensive review identified two availability bugs, but the platform cybersecurity safety gate blocked the plugin scan before validation/finalization. Per user direction, it was not retried; ordinary regression tests cover both fixes. | Unavailable; no completed Codex Security scan is claimed |
| GitHub | Read and invoked the GitHub skill. Connector returned 404 for the private repository; authenticated `gh`/`git` fallback confirmed private/admin state and pushed the immutable baseline. | Active fallback |
| Test Android Apps | Android emulator QA and performance skills were discovered. | Pending buildable APK |
| Build Android Apps | Android Emulator Browser skill was discovered. | Pending buildable APK |
| CompText Token Saver | Read and invoked project-state-first. Both `memory_recall` and `context_prepare` returned `workspace_not_allowed` for `comptext-phone-agent`; no allowlist was broadened. | Unavailable for this workspace |
| Custom `dev-6a4e3e549bc48191b33d6623ca76fe5e` plugin | The plugin was requested but exposed no callable skill, MCP tool, or app capability in this session. | Unavailable |

This file is updated at each later review, Android, security, and release phase. Missing tools
are recorded as unavailable evidence, never as a clean result.
