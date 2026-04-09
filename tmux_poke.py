#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

VERSION = "0.1.2"
ENTER_DELAY_SECONDS = 1.0


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def format_timestamp(moment: datetime, reference_now: datetime) -> str:
    if moment.second == 0 and moment.microsecond == 0:
        time_format = "%H:%M"
    else:
        time_format = "%H:%M:%S"

    if moment.date() == reference_now.date():
        return moment.strftime(time_format)

    return moment.strftime(f"%Y-%m-%d {time_format}")


def run_tmux(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["tmux", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        fail("Tmux is not installed or not in PATH")
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

    fail(f"Tmux session not found: {target}")


def get_active_pane_for_session(session_target: str) -> str:
    pane_id = run_tmux("display-message", "-p", "-t", session_target, "#{pane_id}")
    if not pane_id.startswith("%"):
        fail(f"Could not resolve an active pane for session {session_target}")
    return pane_id


def parse_local_datetime(value: str, reference_now: datetime) -> datetime:
    normalized = value.strip().replace("T", " ")
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", normalized)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        if hours >= 24:
            fail("Invalid --at value. Hours must be less than 24")

        scheduled_at = reference_now.replace(
            hour=hours,
            minute=minutes,
            second=0,
            microsecond=0,
        )
        if scheduled_at <= reference_now:
            scheduled_at += timedelta(days=1)
        return scheduled_at

    try:
        scheduled_at = datetime.fromisoformat(normalized)
    except ValueError:
        fail(
            "Invalid --at value. Use local time as 'HH:MM', "
            "'2026-04-06 21:15', or '2026-04-06T21:15:30'"
        )

    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone().replace(tzinfo=None)
    return scheduled_at


def parse_delay(value: str) -> float:
    normalized = value.strip()
    if not normalized:
        fail("Delay value cannot be empty")

    if ":" not in normalized:
        try:
            delay_seconds = float(normalized)
        except ValueError:
            fail("Invalid --delay value. Use seconds or h:m or h:m:s")
        if delay_seconds < 0:
            fail("Delay must be zero or greater")
        return delay_seconds

    parts = normalized.split(":")
    if len(parts) not in (2, 3):
        fail("Invalid --delay value. Use h:m or h:m:s")

    if not all(re.fullmatch(r"\d+", part) for part in parts):
        fail("Invalid --delay value. Hours, minutes, and seconds must be integers")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) == 3 else 0

    if minutes >= 60:
        fail("Invalid --delay value. Minutes must be less than 60")
    if seconds >= 60:
        fail("Invalid --delay value. Seconds must be less than 60")

    return float(hours * 3600 + minutes * 60 + seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Schedule typing text and Enter into an existing tmux session."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
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
        help=(
            "Exact local time to send input, for example '21:15', "
            "'2026-04-06 21:15', or '2026-04-06T21:15:30'."
        ),
    )

    parser.add_argument(
        "-t",
        "--text",
        default="continue",
        help="Text to send before Enter. Defaults to 'continue'.",
    )
    parser.add_argument(
        "-E",
        "--enter-before",
        action="store_true",
        help="Send Enter before typing the text.",
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

    now = datetime.now()
    scheduled_at = parse_local_datetime(schedule_args.at, now)
    delay = (scheduled_at - now).total_seconds()
    if delay <= 0:
        fail(f"At time is not in the future: {scheduled_at.isoformat(sep=' ')}")
    return delay


def main() -> None:
    if shutil.which("tmux") is None:
        fail("Tmux is not installed or not in PATH")

    args = parse_args()
    session_target = resolve_session_target(args.session)
    delay_seconds = seconds_until(args)
    send_text = args.text
    enter_before = args.enter_before

    schedule_now = datetime.now()
    text_scheduled_for = schedule_now.timestamp() + delay_seconds
    if enter_before:
        initial_enter_scheduled_for = text_scheduled_for
        text_scheduled_for += ENTER_DELAY_SECONDS
    else:
        initial_enter_scheduled_for = None
    enter_scheduled_for = text_scheduled_for + ENTER_DELAY_SECONDS
    text_scheduled_dt = datetime.fromtimestamp(text_scheduled_for)
    enter_scheduled_dt = datetime.fromtimestamp(enter_scheduled_for)
    text_scheduled_label = format_timestamp(
        text_scheduled_dt,
        schedule_now,
    )
    enter_scheduled_label = format_timestamp(
        enter_scheduled_dt,
        schedule_now,
    )
    initial_enter_scheduled_label = (
        format_timestamp(
            datetime.fromtimestamp(initial_enter_scheduled_for),
            schedule_now,
        )
        if initial_enter_scheduled_for is not None
        else None
    )

    if args.dry_run:
        pane_id = get_active_pane_for_session(session_target)
        if enter_before:
            print(
                f"Dry-run: would send Enter to {pane_id} in session "
                f"{session_target} at {initial_enter_scheduled_label}; type "
                f"{send_text!r} at {text_scheduled_label}; send Enter at "
                f"{enter_scheduled_label}"
            )
        else:
            print(
                f"Dry-run: would type {send_text!r} to {pane_id} in session "
                f"{session_target} at {text_scheduled_label}; send Enter at "
                f"{enter_scheduled_label}"
            )
        return

    if enter_before:
        print(
            f"Scheduled Enter for session {session_target} at "
            f"{initial_enter_scheduled_label}; text {send_text!r} at "
            f"{text_scheduled_label}; Enter at {enter_scheduled_label}",
            flush=True,
        )
    else:
        print(
            f"Scheduled {send_text!r} for session {session_target} at "
            f"{text_scheduled_label}; Enter at {enter_scheduled_label}",
            flush=True,
        )

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    pane_id = get_active_pane_for_session(session_target)
    if enter_before:
        run_tmux("send-keys", "-t", pane_id, "C-m")
        sent_enter_at = datetime.now()
        print(
            f"Sent Enter to {pane_id} in session {session_target} at "
            f"{format_timestamp(sent_enter_at, sent_enter_at)}",
            flush=True,
        )
        time.sleep(ENTER_DELAY_SECONDS)

    run_tmux("send-keys", "-t", pane_id, "-l", send_text)
    typed_at = datetime.now()
    print(
        f"Typed {send_text!r} to {pane_id} in session {session_target} at "
        f"{format_timestamp(typed_at, typed_at)}; Enter scheduled at "
        f"{enter_scheduled_label}",
        flush=True,
    )

    time.sleep(ENTER_DELAY_SECONDS)

    run_tmux("send-keys", "-t", pane_id, "C-m")
    final_enter_at = datetime.now()
    print(
        f"Sent Enter to {pane_id} in session {session_target} at "
        f"{format_timestamp(final_enter_at, final_enter_at)}"
    )


if __name__ == "__main__":
    main()
