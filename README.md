# tmux-continue

Small CLI for scheduling `continue` + Enter into an existing tmux session on the local machine.

## Why this approach

The script uses `tmux send-keys`, so it does not attach to the session, steal focus, or block normal use of that tmux session. When the scheduled time arrives, it resolves the session's currently active pane and types into that pane.

## Usage

Delay-based scheduling:

```bash
./tmux_continue.py --session '$160' --delay 30
./tmux_continue.py -s '$160' -d 30
```

Absolute local time scheduling:

```bash
./tmux_continue.py --session '$160' --at '2026-04-06 21:15'
./tmux_continue.py --session 160 --at '2026-04-06T21:15:30'
./tmux_continue.py -s 160 -a '2026-04-06T21:15:30'
```

Dry run:

```bash
./tmux_continue.py --session '$160' --delay 30 --dry-run
./tmux_continue.py -s '$160' -d 30 -n
```

## Notes

- `--session` accepts either a tmux session name or a session id.
- Numeric ids can be passed as `160`; the script also resolves them as tmux ids like `$160`.
- `--at` is interpreted in the machine's local timezone.
- `--text` defaults to `continue`, but it can be changed if needed.
- Short options are available: `-s`, `-d`, `-a`, `-t`, and `-n`.
