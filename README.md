# tmux-poke

Small CLI for scheduling text + Enter into an existing tmux session on the local machine.

## Installation

Install from the current checkout:

```bash
pipx install .
```

Install directly from GitHub:

```bash
pipx install 'git+https://github.com/ivanzoid/tmux-poke.git'
```

After installation, use the `tmux-poke` command. The repository also keeps the executable `./tmux_poke.py` script for local use.

## Why this approach

The script uses `tmux send-keys`, so it does not attach to the session, steal focus, or block normal use of that tmux session. When the scheduled time arrives, it resolves the session's currently active pane, types into that pane, waits one second, and then sends Enter to that same pane.

This is useful when you want to continue Claude Code, Codex, or a similar terminal app later after a usage limit resets. Schedule a `continue` poke, leave the session alone, and let it resume when the time arrives.

## Usage

Delay-based scheduling:

```bash
tmux-poke --session '$160' --delay 30
tmux-poke -s '$160' -d 30
tmux-poke -s '$160' -d 1:15
tmux-poke -s '$160' -d 1:15:30
./tmux_poke.py --session '$160' --delay 30
./tmux_poke.py -s '$160' -d 30
./tmux_poke.py -s '$160' -d 1:15
./tmux_poke.py -s '$160' -d 1:15:30
```

Absolute local time scheduling:

```bash
tmux-poke --session '$160' --at '21:15'
tmux-poke --session '$160' --at '2026-04-06 21:15'
tmux-poke --session 160 --at '2026-04-06T21:15:30'
tmux-poke -s 160 -a '2026-04-06T21:15:30'
./tmux_poke.py --session '$160' --at '21:15'
./tmux_poke.py --session '$160' --at '2026-04-06 21:15'
./tmux_poke.py --session 160 --at '2026-04-06T21:15:30'
./tmux_poke.py -s 160 -a '2026-04-06T21:15:30'
```

Dry run:

```bash
tmux-poke --session '$160' --delay 30 --dry-run
tmux-poke -s '$160' -d 30 -n
./tmux_poke.py --session '$160' --delay 30 --dry-run
./tmux_poke.py -s '$160' -d 30 -n
```

Send Enter before the text:

```bash
tmux-poke -s '$160' -d 30 --enter-before
tmux-poke -s '$160' -d 30 -E -t continue
./tmux_poke.py -s '$160' -d 30 --enter-before
./tmux_poke.py -s '$160' -d 30 -E -t continue
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
