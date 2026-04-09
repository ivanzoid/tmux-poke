# tmux-poke

Small CLI for scheduling text + Enter into an existing tmux session on the local machine.

## Installation

```bash
# Install from GitHub with pipx
pipx install 'git+https://github.com/ivanzoid/tmux-poke.git'
```

After installation, use the `tmux-poke` command.

## Why this approach

The script uses `tmux send-keys`, so it does not attach to the session, steal focus, or block normal use of that tmux session. When the scheduled time arrives, it resolves the session's currently active pane, types into that pane, waits one second, and then sends Enter to that same pane.

This is useful when you want to continue Claude Code, Codex, or a similar terminal app later after a usage limit resets. Schedule a `continue` poke, leave the session alone, and let it resume when the time arrives.

## Usage

Core arguments:

```bash
# --session / -s: target tmux session by id or name
tmux-poke --session '$160' --delay 30

# --delay / -d: schedule by delay in seconds, h:m, or h:m:s
tmux-poke --session '$160' --delay 1:15:30

# --at / -a: schedule for a local time
tmux-poke --session '$160' --at '21:15'

# --text / -t: change the text sent before Enter
tmux-poke --session '$160' --delay 30 --text 'status'

# --enter-before / -E: send Enter, wait, then type the text
tmux-poke --session '$160' --delay 30 --enter-before

# --dry-run / -n: preview the schedule without touching tmux
tmux-poke --session '$160' --delay 30 --dry-run

# --version / -v: print the installed CLI version
tmux-poke --version
```

Useful --at forms:

```bash
# Next occurrence of a local clock time, today or tomorrow
tmux-poke --session '$160' --at '21:15'

# Specific local date and minute
tmux-poke --session '$160' --at '2026-04-06 21:15'

# Specific local date and second
tmux-poke --session 160 --at '2026-04-06T21:15:30'
```

## Notes

- `--session` accepts either a tmux session name or a session id.
- Numeric ids can be passed as `160`; the script also resolves them as tmux ids like `$160`.
- `--at` is interpreted in the machine's local timezone.
- `--at HH:MM` schedules the next occurrence of that local time: later today if it is still ahead, otherwise tomorrow.
- `--delay` accepts raw seconds, `h:m`, or `h:m:s`.
- `--text` defaults to `continue`, but it can be changed if needed.
- `--enter-before` sends Enter before typing the text, so the default sequence becomes Enter, wait one second, `continue`, wait one second, Enter.
- The script always waits one second between each send step.
- `--version` shows the CLI version.
- Short options are available: `-s`, `-d`, `-a`, `-t`, `-E`, `-n`, and `-v`.
