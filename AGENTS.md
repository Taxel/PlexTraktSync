# AGENTS

## Scope

These instructions apply to the whole repository.

## Project summary

- Python CLI application for two-way sync between Plex and Trakt
- Main package: `plextraktsync/`
- Test suite: `tests/`
- Packaging/tooling: `pyproject.toml`, `setup.cfg`, `requirements.txt`, `Pipfile`

## Key entrypoints

- CLI module: `plextraktsync/cli.py`
- Python module entry: `plextraktsync/__main__.py`
- Sync command: `plextraktsync/commands/sync.py`
- Core sync runner: `plextraktsync/sync/Sync.py`
- Shared object factory: `plextraktsync/factory/Factory.py`

## Architecture notes

- Commands are declared in `plextraktsync/cli.py` and lazily loaded from
  `plextraktsync/commands/`.
- Runtime state and shared services are created through the cached
  `Factory` object.
- Configuration is loaded from defaults, then local config, then `.env` via
  `plextraktsync/config/Config.py`.
- Sync behavior is plugin-driven through
  `plextraktsync/sync/plugin/SyncPluginManager.py`.

## Development commands

- Run app info: `./plextraktsync.sh info`
- Run tests: `pytest`
- Install test deps: `pip install -r tests/requirements.txt`
- Install runtime deps: `python -m pip install -r requirements.txt`
- `requirements.pipenv.txt` exists to keep Pipenv versions in sync for
  Dependabot, not as a runtime requirements file.

## Change guidance

- Prefer small, focused changes.
- Keep CLI option changes aligned between `cli.py` and the implementing
  command module.
- When changing sync behavior, check whether the change belongs in a plugin
  instead of the core `Sync` class.
- When changing config behavior, preserve migration behavior for legacy
  `config.json` users.
- Add or update pytest coverage for behavior changes when practical.
- Prefer behavior-focused tests over implementation-coupled tests.
- Avoid asserting internal call shapes (exact URL/query construction, private
  helper usage, or call ordering) unless that detail is itself user-visible
  behavior or a documented compatibility contract.

## Commit guidelines

- Prefer atomic commits: one intent, one self-contained change.
- Keep commits small enough to review and revert independently.
- Separate refactors, behavior changes, tests, and docs when practical.
- Follow the principles from https://cbea.ms/git-commit/.
- Use commit messages with:
  - a short imperative subject line
  - a blank line after the subject
  - optional body bullets explaining why/context
- Include a `Co-authored-by` trailer for LLM-assisted commits.
- The trailer example below is illustrative only; agents must replace both the
  name and email with their own identity instead of copying the example
  literally.
- Example trailer format:
  - `Co-authored-by: OpenCode (<active-model>) <noreply@openai.com>`

## Validation

- Run `pytest` for behavior changes.
- For CLI-related changes, also run `./plextraktsync.sh info` when relevant.
