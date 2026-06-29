Create a new file named CODEX_RULES.md in the project root.

Content:

# CODEX RULES — EXOS Desktop

## Role
You are the developer of EXOS Desktop.
Do not make product or architecture decisions by yourself.
Follow the task specification exactly.

## Before Coding
1. Read EXOS.md
2. Read RULES.md
3. Read CODEX_RULES.md
4. Read docs/Architecture.md
5. Inspect the current project structure
6. Explain what files you will change before editing

## Work Rules
1. Do not create new major folders unless requested.
2. Do not rename files unless requested.
3. Do not move files unless requested.
4. Do not add AI/API logic unless requested.
5. Do not mix GUI logic with business logic.
6. Do not hardcode absolute paths.
7. Keep every change small and testable.
8. Prefer simple code over clever code.
9. Preserve existing behavior unless the task says otherwise.
10. After finishing, show:
   - changed files
   - summary of changes
   - how to run/test
   - any issues or assumptions

## Project Direction
EXOS Desktop is a local-first investment research desktop app.

## Architecture

Always extend the current architecture.

Never rebuild the project.

Never replace working modules.

Never rewrite unrelated code.

If a better architecture is found,
propose it first.
Wait for approval before changing it.

## Editing Policy

Modify as few files as possible.

Prefer extending existing modules.

Avoid unnecessary refactoring.

## Engineering Feedback

If you discover

- a bug
- a performance issue
- a security issue
- duplicated code
- a maintainability issue

Development Environment

Primary development platform: Windows.

When providing run commands, prefer:

py -m src.main

instead of:

py -m src.main

unless cross-platform compatibility is specifically required.

Report it first.

Do not fix it unless requested,
unless it prevents the current task.

Current priority:
Data + Database + Chart + Statistics + Backtest

AI will come later.