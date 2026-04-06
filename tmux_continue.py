#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_tmux(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["tmux", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        fail("tmux is not installed or not in PATH")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or "tmux command failed"
        fail(stderr)
    return completed.stdout.strip()


def resolve_session_target(target: str) -> str:
    candidates = [target]
    if target.isdigit():
        candidates.insert(0, f"${target}")

    for candidate in candidates:
        result = subprocess.run(
            ["tmux", "has-session", "-t", candidate],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate

    fail(f"tmux session not found: {target}")


def get_active_pane_for_session(session_target: str) -> str:
    pane_id = run_tmux("display-message", "-p", "-t", session_target, "#{pane_id}")
    if not pane_id.startswith("%"):
        fail(f"could not resolve an active pane for session {session_target}")
    return pane_id


def parse_local_datetime(value: str) -> datetime:
    normalized = value.strip().replace("T", " ")
    try:
        scheduled_at = datetime.fromisoformat(normalized)
    except ValueError as exc:
        fail(
            "invalid --at value. Use local time in ISO-like format, for example "
            "'2026-04-06 21:15' or '2026-04-06T21:15:30'"
        )

    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone().replace(tzinfo=None)
    return scheduled_at


def parse_delay(value: str) -> float:
    normalized = value.strip()
    if not normalized:
        fail("delay value cannot be empty")

    if ":" not in normalized:
        try:
            delay_seconds = float(normalized)
        except ValueError:
            fail("invalid --delay value. Use seconds or h:m or h:m:s")
        if delay_seconds < 0:
            fail("--delay must be zero or greater")
        return delay_seconds

    parts = normalized.split(":")
    if len(parts) not in (2, 3):
        fail("invalid --delay value. Use h:m or h:m:s")

    if not all(re.fullmatch(r"\d+", part) for part in parts):
        fail("invalid --delay value. Hours, minutes, and seconds must be integers")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) == 3 else 0

    if minutes >= 60:
        fail("invalid --delay value. Minutes must be less than 60")
    if seconds >= 60:
        fail("invalid --delay value. Seconds must be less than 60")

    return float(hours * 3600 + minutes * 60 + seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Schedule typing 'continue' and Enter into an existing tmux session."
    )
    parser.add_argument(
        "-s",
        "--session",
        required=True,
        help="tmux session id or name. Numeric ids can be passed as 160 or $160.",
    )

    schedule_group = parser.add_mutually_exclusive_group(required=True)
    schedule_group.add_argument(
        "-d",
        "--delay",
        type=parse_delay,
        help="Delay before sending input. Accepts seconds or h:m or h:m:s.",
    )
    schedule_group.add_argument(
        "-a",
        "--at",
        help="Exact local time to send input, for example '2026-04-06 21:15' or '2026-04-06T21:15:30'.",
    )

    parser.add_argument(
        "-t",
        "--text",
        default="continue",
        help="Text to send before Enter. Defaults to 'continue'.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would happen without sending anything.",
    )
    return parser.parse_args()


def seconds_until(schedule_args: argparse.Namespace) -> float:
    if schedule_args.delay is not None:
        return schedule_args.delay

    scheduled_at = parse_local_datetime(schedule_args.at)
    now = datetime.now()
    delay = (scheduled_at - now).total_seconds()
    if delay < 0:
        fail(f"--at time is in the past: {scheduled_at.isoformat(sep=' ')}")
    return delay


def main() -> None:
    if shutil.which("tmux") is None:
        fail("tmux is not installed or not in PATH")

    args = parse_args()
    session_target = resolve_session_target(args.session)
    delay_seconds = seconds_until(args)
    send_text = args.text

    scheduled_for = datetime.now().timestamp() + delay_seconds
    scheduled_label = datetime.fromtimestamp(scheduled_for).isoformat(sep=" ", timespec="seconds")

    if args.dry_run:
        pane_id = get_active_pane_for_session(session_target)
        print(
            f"dry-run: would send {send_text!r} + Enter to {pane_id} in session {session_target} at {scheduled_label}"
        )
        return

    print(f"scheduled {send_text!r} + Enter for session {session_target} at {scheduled_label}", flush=True)

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    pane_id = get_active_pane_for_session(session_target)
    run_tmux("send-keys", "-t", pane_id, send_text, "Enter")
    print(f"sent {send_text!r} + Enter to {pane_id} in session {session_target} at {scheduled_label}")


if __name__ == "__main__":
    main()
