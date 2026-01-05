#!/usr/bin/env python3
"""
Simple tmux-based dispatcher to launch the Codex CLI, send a predefined prompt,
and periodically print the last lines from the tmux pane for monitoring.
"""

from __future__ import annotations

import subprocess
import time
import uuid
from typing import Iterable

# Edit this prompt to drive the Codex CLI. It is sent after Codex starts.
PREDEFINED_PROMPT = (
    "Summarize the current working directory structure"
)

# How often to poll the tmux pane for output.
POLL_INTERVAL_SECONDS = 1

# Simple ANSI colors for pane output.
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"


def run_tmux(args: Iterable[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute a tmux command with sane defaults."""
    return subprocess.run(
        ["tmux", *args],
        check=check,
        text=True,
        capture_output=True,
    )


def create_session(session_name: str) -> None:
    run_tmux(["new-session", "-d", "-s", session_name])


def send_keys(target: str, line: str) -> None:
    # Use C-m to simulate Enter.
    run_tmux(["send-keys", "-t", target, line, "C-m"])


def capture_last_lines(target: str, lines: int = 10) -> str:
    result = run_tmux(
        ["capture-pane", "-t", target, "-p", "-S", f"-{lines}"],
        check=True,
    )
    # Defensive clamp in Python in case tmux returns more than requested.
    return "\n".join(result.stdout.splitlines()[-lines:])


def kill_session(session_name: str) -> None:
    run_tmux(["kill-session", "-t", session_name], check=False)


def main() -> None:
    session_name = f"codex_task_{uuid.uuid4().hex[:8]}"
    target = f"{session_name}:0.0"

    print(f"Starting tmux session '{session_name}' and launching Codex...")
    try:
        create_session(session_name)

        # Start Codex CLI in the pane.
        send_keys(target, "codex")
        time.sleep(1)  # Give Codex a moment to start.

        # Send the predefined prompt (supports multi-line strings).
        for line in PREDEFINED_PROMPT.splitlines():
            if line.strip() == "":
                send_keys(target, "")  # Preserve blank lines if present.
            else:
                send_keys(target, line)
        # Ensure the prompt is submitted (extra Enter after the last line).
        send_keys(target, "\n")

        print("Monitoring tmux pane output (last 1 lines). Press Ctrl+C to stop.")
        while True:
            output = capture_last_lines(target, lines=10)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] ---- tmux pane tail ----")
            print(f"{ANSI_CYAN}{output.rstrip()}{ANSI_RESET}")
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nInterrupted by user; shutting down tmux session.")
    except FileNotFoundError as exc:
        print(f"Required binary not found: {exc}. Ensure tmux and codex are installed.")
    except subprocess.CalledProcessError as exc:
        print(f"tmux command failed: {exc}\nstdout:\n{exc.stdout}\nstderr:\n{exc.stderr}")
    finally:
        kill_session(session_name)
        print(f"tmux session '{session_name}' terminated.")


if __name__ == "__main__":
    main()

