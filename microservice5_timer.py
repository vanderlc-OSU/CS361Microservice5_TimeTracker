"""
microservice_timer.py — Time, Date & Reset Scheduler Microservice

PURPOSE:
    Acts as a central clock/reset authority for other microservices.
    Other microservices write a request file asking "should I reset?"
    This service responds YES or NO based on the reset interval the
    user configured.

USER CONFIGURATION (set once at startup via user_config.txt):
    Write one of the following to user_config.txt before starting:
        daily
        weekly
    The service reads this file on startup and remembers the interval.
    If user_config.txt is missing the service will prompt the user in
    the terminal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE PROTOCOL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUEST  — written by the CALLING microservice:
    File : timer_request.txt
    Body : <service_name>
    e.g. : microservice6

    Then the caller creates: timer_request_ready.flag

RESPONSE — written by THIS service:
    File : timer_response.txt
    Body (one of):
        YES,<current_datetime>,<last_reset_datetime>,<interval>
        NO,<current_datetime>,<last_reset_datetime>,<interval>

    Then this service creates: timer_response_ready.flag

    YES = the calling service should reset its data now
    NO  = not yet, no reset needed

RESET RECORD:
    Stored in: last_reset.txt
    Body     : <ISO datetime of last reset>,<service_name>
    This file is updated every time a YES is issued.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATETIME FORMAT: YYYY-MM-DD HH:MM:SS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import time
from datetime import datetime, timedelta

# ── file names ────────────────────────────────────────────────────────────────
USER_CONFIG_FILE     = "user_config.txt"
LAST_RESET_FILE      = "last_reset.txt"
REQUEST_FILE         = "timer_request.txt"
RESPONSE_FILE        = "timer_response.txt"
REQUEST_READY_FLAG   = "timer_request_ready.flag"
RESPONSE_READY_FLAG  = "timer_response_ready.flag"

POLL_INTERVAL        = 0.05
DATETIME_FMT         = "%Y-%m-%d %H:%M:%S"


def now_str() -> str:
    return datetime.now().strftime(DATETIME_FMT)


def load_config() -> str:
    """Read daily/weekly from user_config.txt, or ask the user."""
    if os.path.exists(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE, "r") as f:
            interval = f.read().strip().lower()
        if interval in ("daily", "weekly"):
            print(f"[timer] Loaded reset interval from {USER_CONFIG_FILE}: {interval!r}")
            return interval
        print(f"[timer] WARNING: {USER_CONFIG_FILE} contains unknown value {interval!r}")

    while True:
        choice = input("[timer] Reset interval — enter 'daily' or 'weekly': ").strip().lower()
        if choice in ("daily", "weekly"):
            with open(USER_CONFIG_FILE, "w") as f:
                f.write(choice + "\n")
            print(f"[timer] Saved interval to {USER_CONFIG_FILE}")
            return choice
        print("       Please type exactly 'daily' or 'weekly'.")


def load_last_reset(service_name: str) -> datetime | None:
    """Return the last reset datetime for this service, or None."""
    if not os.path.exists(LAST_RESET_FILE):
        return None
    with open(LAST_RESET_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",", 1)
            if len(parts) == 2 and parts[1].strip() == service_name:
                try:
                    return datetime.strptime(parts[0].strip(), DATETIME_FMT)
                except ValueError:
                    pass
    return None


def save_last_reset(service_name: str, dt: datetime):
    """Update (or insert) the last reset record for this service."""
    lines = []
    updated = False
    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",", 1)
                if len(parts) == 2 and parts[1].strip() == service_name:
                    lines.append(f"{dt.strftime(DATETIME_FMT)},{service_name}\n")
                    updated = True
                else:
                    lines.append(line)
    if not updated:
        lines.append(f"{dt.strftime(DATETIME_FMT)},{service_name}\n")
    with open(LAST_RESET_FILE, "w") as f:
        f.writelines(lines)


def should_reset(last_reset: datetime | None, interval: str) -> bool:
    """Return True if enough time has passed since the last reset."""
    if last_reset is None:
        return True
    delta = datetime.now() - last_reset
    if interval == "daily":
        return delta >= timedelta(days=1)
    else:
        return delta >= timedelta(weeks=1)


def run_server():
    for f in (REQUEST_FILE, RESPONSE_FILE, REQUEST_READY_FLAG, RESPONSE_READY_FLAG):
        if os.path.exists(f):
            os.remove(f)

    interval = load_config()

    print(f"\n[timer] Microservice running | interval={interval!r} | {now_str()}")
    print(f"  Request file : {REQUEST_FILE}")
    print(f"  Response file: {RESPONSE_FILE}")
    print(f"  Reset record : {LAST_RESET_FILE}\n")

    while True:
        if not os.path.exists(REQUEST_READY_FLAG):
            time.sleep(POLL_INTERVAL)
            continue

        try:
            with open(REQUEST_FILE, "r") as f:
                service_name = f.read().strip()
        except Exception as exc:
            service_name = "unknown"
            print(f"[timer] WARNING: could not read request file: {exc}")

        os.remove(REQUEST_READY_FLAG)

        now = datetime.now()
        last_reset = load_last_reset(service_name)
        reset_needed = should_reset(last_reset, interval)
        last_str = last_reset.strftime(DATETIME_FMT) if last_reset else "never"
        answer = "YES" if reset_needed else "NO"

        if reset_needed:
            save_last_reset(service_name, now)

        response_line = f"{answer},{now.strftime(DATETIME_FMT)},{last_str},{interval}"
        with open(RESPONSE_FILE, "w") as f:
            f.write(response_line + "\n")
        open(RESPONSE_READY_FLAG, "w").close()

        print(f"[timer] {service_name!r} -> {answer}  "
              f"(last reset: {last_str}, interval: {interval})")


if __name__ == "__main__":
    run_server()
