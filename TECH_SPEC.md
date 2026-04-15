## Objective
Create a lightweight wrapper around Aider that makes each coding run reviewable, scoreable, and easier to improve over time.

## Scope
Track session setup, human review, diff export, and nightly reporting without adding heavyweight infrastructure.

## Folder Structure
- `config/`: review rules, scoring legend, and allowed failure tags.
- `scripts/`: workflow commands for starting, reviewing, exporting, and reporting sessions.
- `sessions/`: one folder per tracked Aider task.
- `reports/`: generated review summaries.

## Session Lifecycle
1. Start a session with a task title, task type, model, and expected file scope.
2. Run Aider using the generated prompt/context files.
3. Export the git diff to snapshot the outcome and changed files.
4. Review the session with a verdict, score, failure tags, and notes.
5. Generate a nightly report to identify where the wrapper should improve.

## Data Model
Each `session.json` stores normalized scope data, review metadata, changed files, and a prompt preview so the wrapper can compare intent to outcome.

## Scripts
Scripts share a common session library so validation and persistence logic stay consistent.

## Future Versions
- Add non-interactive CLI flags for CI and batch workflows.
- Compare `expected_scope` against `changed_files` automatically to flag drift before review.
- Store repo revision metadata to make diffs reproducible.
