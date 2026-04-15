# Aider Workflow Wrapper

## Project Overview

This project is a disciplined workflow wrapper around Aider.

It is designed to help you run Aider in a more controlled and reviewable way by adding:

- scoped sessions
- prompt persistence
- execution artifacts
- run reviews
- diff exports
- nightly reports
- iterative prompt tuning

The wrapper does not replace Aider. It adds structure around how you prepare, run, inspect, and review Aider sessions inside a repo.

## Features

Current implemented scripts:

- `scripts/start_session.py`
  Creates a new session folder and writes the base session artifacts without running Aider.
- `scripts/create_and_run_session.py`
  Creates a new session and immediately runs Aider for that session.
- `scripts/run_aider_session.py`
  Runs Aider for an existing session and captures execution artifacts.
- `scripts/review_session.py`
  Lets you review a completed session with a verdict, score, failure tags, and notes.
- `scripts/export_diff.py`
  Exports the current git diff for a selected session and records changed files into session metadata.
- `scripts/nightly_report.py`
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

### Create and Run a New Session

Use this when you want the wrapper to create a session and immediately launch Aider:

```powershell
python scripts/create_and_run_session.py
```

You will be prompted for:

- task title
- task type
- expected scope as a comma-separated list of files
- model name

### Run an Existing Session

Use this when the session already exists and you want to launch Aider for it:

```powershell
python scripts/run_aider_session.py
```

### Create a Session Without Running Aider

Use this when you want to prepare a session first and run it later:

```powershell
python scripts/start_session.py
```

### Review a Session

```powershell
python scripts/review_session.py
```

### Export a Diff

```powershell
python scripts/export_diff.py
```

### Generate the Nightly Report

```powershell
python scripts/nightly_report.py
```

## Workflow Example

This is the current end to end workflow for one task.

### 1. Create a Task and Run Aider

```powershell
python scripts/create_and_run_session.py
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
python scripts/review_session.py
```

Choose the session and record:

- verdict
- score
- failure tags
- notes summary

### 4. Export the Patch

```powershell
python scripts/export_diff.py
```

This writes `diff.patch` into the session folder and records changed files back into `session.json`.

### 5. Generate the Nightly Report

```powershell
python scripts/nightly_report.py
```

This updates:

```text
reports/nightly_report.md
```

## Project Structure

### `scripts/`

Contains the wrapper’s workflow scripts:

- session creation
- session execution
- review
- diff export
- reporting

### `sessions/`

Contains one folder per tracked task session.

Each session folder stores the task metadata, prompt artifacts, run artifacts, and optional diff export.

### `reports/`

Contains generated markdown reports, currently including `nightly_report.md`.

### `templates/`

Contains the base JSON template used for session metadata.

### `tests/`

Contains the current automated test suite for the wrapper scripts.

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

Optional artifact produced by `export_diff.py`.

This contains the current git diff at the time of export.

## Best Practices

- Use one task per session.
- Keep the expected file scope tight and explicit.
- Write task titles that clearly describe the requested change.
- Review failed or low-quality runs instead of discarding them.
- Use `aider_stdout.txt` and `aider_stderr.txt` when diagnosing a bad run.
- Export diffs for sessions you want to inspect or compare later.
- Use nightly reports to identify repeated failure tags and improve future prompts.

## Overall Vision and Long Term Plan

The long term goal of this wrapper is to evolve from a session runner into a **persistent AI engineering workflow system** built around memory, recall, and iterative improvement.

Today, the wrapper provides disciplined session execution and review around Aider.

The broader plan is to transform each coding session into reusable engineering memory.

### Session Memory

Every session already acts as a memory unit.

Each session stores:

- task objective
- scoped files
- prompt history
- execution artifacts
- diffs
- review verdicts
- failure tags
- notes

Over time, this creates a searchable history of:

- what problems were worked
- what prompts succeeded
- what prompts failed
- what files were repeatedly involved
- what model performed best

This is the foundation for long term recall.

### Prompt Recall and Reuse

A major planned feature is prompt recall.

The system should eventually be able to look at prior successful sessions and surface:

- similar bugfix prompts
- successful feature implementation prompts
- common refactor instructions
- file scope patterns that worked well

This allows future sessions to reuse proven prompt structures instead of reinventing prompts every time.

Example future use case:

> “Find previous sessions involving WHOIS failures and reuse the highest scoring prompt.”

This will help reduce repeated bad runs and improve accuracy.

### Failure Memory

Another major goal is persistent failure memory.

The wrapper should eventually track repeated failure patterns such as:

- no code changes made
- wrong file modified
- broad refactor drift
- syntax breakages
- ignored scope
- prompt misunderstanding

This can later be used as a preflight warning system before launching Aider.

Example:

> “This task resembles 4 previously failed multi-file prompts. Recommend narrowing scope.”

This directly supports improving run accuracy.

### File and Code Recall

Long term, sessions should support recall of recurring file relationships.

For example:

- `intel/views.py` often changes with `services/whois_enrichment.py`
- UI tasks frequently involve templates and CSS together
- certain scripts often break together

This allows smarter scope recommendations for future runs.

### Report Driven Learning

Nightly reports are intended to become a learning system rather than only a summary report.

Future reports should help answer questions like:

- What prompts are most successful?
- Which model performs best for bugfixes?
- Which files have the highest failure rate?
- What failure tags are increasing over time?

The goal is continuous improvement of local AI coding workflows.

### Long Term Direction

The long term vision is:

**session history → structured memory → recall → smarter future prompts**

The wrapper is being designed to reduce repeated bad runs by learning from previous sessions and improving prompt discipline over time.

## Roadmap

Known next improvements for the wrapper:

- consolidate the workflow into a single primary entry point.
- automatic diff export after runs
- stronger validation for session inputs and scope paths
- richer reporting based on run artifacts and review outcomes
