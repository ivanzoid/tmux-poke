# Repository Guidelines

## Project Structure & Module Organization

This repository is intentionally small:

- `tmux_poke.py`: the main executable CLI. It parses arguments, resolves the target tmux session, computes the schedule, and sends text plus `Enter`.
- `README.md`: user-facing usage examples and behavior notes.
- `AGENTS.md`: contributor guidance for future changes.

There is no dedicated `tests/` directory yet. If tests are added, place them under `tests/` and keep them focused on argument parsing, time handling, and tmux command execution boundaries.

## Build, Test, and Development Commands

- `python3 tmux_poke.py -h`: show CLI help.
- `./tmux_poke.py -s '$160' -d 30 -n`: dry-run a delay-based schedule.
- `./tmux_poke.py -s '$160' -a '2026-04-06 21:15:30' -n`: dry-run an absolute-time schedule.
- `python3 -m py_compile tmux_poke.py`: quick syntax check.

This project has no build step. Changes should be validated by dry runs against a real tmux session where practical.

## Coding Style & Naming Conventions

Use Python 3 with standard library only unless there is a clear need otherwise. Follow existing style:

- 4-space indentation
- `snake_case` for functions and variables
- small, single-purpose helper functions
- direct error messages via `fail(...)`

Keep the script executable and favor clear control flow over abstraction. Update `README.md` when CLI behavior changes.

## Testing Guidelines

There is no formal test suite yet. Minimum validation for CLI changes:

- run `python3 -m py_compile tmux_poke.py`
- run at least one `--dry-run`
- if behavior changes around scheduling or tmux targeting, verify against a disposable tmux session

When adding tests later, prefer `pytest` with files named `test_*.py`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative subjects such as `Add short CLI options` and `Support h:m delay format`. Keep commit messages concise and behavior-focused.

For pull requests, include:

- a brief summary of the user-visible change
- exact commands used for verification
- README updates when flags, output, or examples change

## Security & Configuration Tips

Do not hardcode session ids, host-specific paths, or secrets. This tool sends keystrokes to live tmux panes, so prefer `--dry-run` first when changing targeting or scheduling logic.
