# Aider Workflow Wrapper

## Project Overview

This project is a command line workflow tool built as a structured wrapper around Aider.

It is session driven, artifact and reporting aware, and designed with a future memory and recall roadmap in mind.

It helps you run Aider in a more controlled and reviewable way by adding:

- scoped sessions
- prompt persistence
- execution artifacts
- run reviews
- diff exports
- nightly reports
- iterative prompt tuning

The wrapper does not replace Aider. It adds structure around how you prepare, run, inspect, review, and report on Aider sessions inside a repo through one primary CLI entry point.

## Features

Current implemented CLI workflows:

- `create`
  Creates a new session folder and writes the base session artifacts without running Aider.
- `create-run`
  Creates a new session and immediately runs Aider for that session.
- `run`
  Runs Aider for an existing session and captures execution artifacts.
- `review`
  Lets you review a completed session with a verdict, score, failure tags, and notes.
- `export-diff`
  Exports the current git diff for a selected session and records changed files into session metadata.
- `report`
  Generates a markdown report summarizing reviewed and unreviewed sessions.

## Installation

### Python Requirements

This project currently expects a working Python environment with `pytest` available for tests.

The repository currently includes:

```text
requirements.txt
```

Install dependencies with:

```powershell
python -m pip install -r requirements.txt
```

### Required External Tools

You also need:

- `aider` installed and available on your `PATH`
- `git` installed and available on your `PATH`

The wrapper uses:

- `aider` to run coding sessions
- `git` to verify repositories and export diffs

### Required Config File

The runner expects this file to exist in the repo root:

```text
.aider.config.yaml
```

That config is passed to Aider by the current run path.

## Quick Start

```powershell
python main.py create
python main.py create-run
python main.py run
python main.py review
python main.py export-diff
python main.py report
```

Run this to see CLI help:

```powershell
python main.py --help
```

For session creation commands, you will be prompted for:

- task title
- task type
- expected scope as a comma-separated list of files
- model name

You can also provide some values directly on the command line:

```powershell
python main.py create --task-title "Tighten run path validation" --task-type bugfix --scope "scripts/run_aider_session.py, scripts/start_session.py" --model gpt-4.1
python main.py create-run --task-title "Fix report wording"
python main.py run --session-id 2026-04-14_173119_test_task --model gpt-4.1
python main.py review --session-id 2026-04-14_173119_test_task
python main.py export-diff --session-id 2026-04-14_173119_test_task
```

### Create a Session Without Running Aider

Use this when you want to prepare a session first and run it later:

```powershell
python main.py create
```

### Create and Run a New Session

Use this when you want the wrapper to create a session and immediately launch Aider:

```powershell
python main.py create-run
```

### Run an Existing Session

Use this when the session already exists and you want to launch Aider for it:

```powershell
python main.py run
```

### Review a Session

```powershell
python main.py review
```

### Export a Diff

```powershell
python main.py export-diff
```

### Generate the Nightly Report

```powershell
python main.py report
```

## Workflow Example

This is the current end to end workflow for one task.

### 1. Create a Task and Run Aider

```powershell
python main.py create-run
```

Example answers:

- Task title: `Tighten run path validation`
- Task type: `bugfix`
- Expected scope: `scripts/run_aider_session.py, scripts/start_session.py`
- Model name: `gpt-4.1`

This creates a new folder under `sessions/` and then launches Aider against the selected files.

### 2. Inspect Run Output

After the run, open the new session folder and inspect:

- `aider_run.json`
- `aider_stdout.txt`
- `aider_stderr.txt`

These show the command used, run timing, exit code, and raw output from Aider.

### 3. Review the Result

```powershell
python main.py review
```

Choose the session and record:

- verdict
- score
- failure tags
- notes summary

### 4. Export the Patch

```powershell
python main.py export-diff
```

This writes `diff.patch` into the session folder and records changed files back into `session.json`.

### 5. Generate the Nightly Report

```powershell
python main.py report
```

This updates:

```text
reports/nightly_report.md
```

## Project Structure

### `main.py`

Contains the primary command line entry point for the wrapper.

This is the main launch surface for:

- session creation
- session execution
- review
- diff export
- reporting

### `scripts/`

Contains the underlying workflow modules used by the CLI entry point.

### `sessions/`

Contains one folder per tracked task session.

Each session folder stores the task metadata, prompt artifacts, run artifacts, and optional diff export.

### `reports/`

Contains generated markdown reports, currently including `nightly_report.md`.

### `templates/`

Contains the base JSON template used for session metadata.

### `tests/`

Contains the current automated test suite for the wrapper.

## Session Artifacts

Each session folder may contain these files.

### `session.json`

Stores structured metadata such as:

- session id
- timestamp
- repo path
- task title
- task type
- model name
- expected scope
- review fields
- changed files
- last run metadata

### `prompt.txt`

Stores the prompt content currently used by the wrapper for the Aider run.

### `context_files.txt`

Stores the expected scope file list for the session.

### `notes.txt`

Manual notes file for the session.

### `aider_run.json`

Stores execution metadata for the most recent run, including:

- command used
- exit code
- start time
- finish time
- duration
- working directory

### `aider_stdout.txt`

Raw stdout captured from the Aider process.

### `aider_stderr.txt`

Raw stderr captured from the Aider process.

### `diff.patch`

Optional artifact produced by `python main.py export-diff`.

This contains the current git diff at the time of export.

## Best Practices

- Use one task per session.
- Keep the expected file scope tight and explicit.
- Write task titles that clearly describe the requested change.
- Review failed or low-quality runs instead of discarding them.
- Use `aider_stdout.txt` and `aider_stderr.txt` when diagnosing a bad run.
- Export diffs for sessions you want to inspect or compare later.
- Use nightly reports to identify repeated failure tags and improve future prompts.
