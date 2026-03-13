"""
timer_client.py — Helper module for talking to microservice_timer

Any microservice can import this and call check_reset() to find out
whether it should wipe/reset its data.

USAGE EXAMPLE (inside another microservice):
    from timer_client import check_reset

    result = check_reset("microservice6")
    if result["should_reset"]:
        print("Resetting data...")
        # ... clear your data here ...
    else:
        print(f"No reset needed. Next reset after {result['interval']} "
              f"from {result['last_reset']}")

No direct calls to microservice_timer.py are made — all communication
happens through plain text files, matching the project-wide protocol.
"""

import os
import time
import sys
from datetime import datetime

REQUEST_FILE        = "timer_request.txt"
RESPONSE_FILE       = "timer_response.txt"
REQUEST_READY_FLAG  = "timer_request_ready.flag"
RESPONSE_READY_FLAG = "timer_response_ready.flag"
DATETIME_FMT        = "%Y-%m-%d %H:%M:%S"
TIMEOUT             = 5.0
POLL_INTERVAL       = 0.05


def check_reset(service_name: str) -> dict:
    """
    Ask the timer microservice whether this service should reset.

    Returns a dict:
        {
            "should_reset" : bool,
            "current_time" : str  (YYYY-MM-DD HH:MM:SS),
            "last_reset"   : str  (YYYY-MM-DD HH:MM:SS or "never"),
            "interval"     : str  ("daily" or "weekly"),
        }

    Exits with an error message if the timer service is not running.
    """
    # Write the request
    with open(REQUEST_FILE, "w") as f:
        f.write(service_name + "\n")
    open(REQUEST_READY_FLAG, "w").close()

    # Wait for response
    deadline = time.time() + TIMEOUT
    while not os.path.exists(RESPONSE_READY_FLAG):
        if time.time() > deadline:
            print("[timer_client] ERROR: Timed out waiting for timer microservice.")
            print("               Is microservice_timer.py running?")
            sys.exit(1)
        time.sleep(POLL_INTERVAL)

    # Read response: YES/NO,<now>,<last_reset>,<interval>
    with open(RESPONSE_FILE, "r") as f:
        line = f.read().strip()
    os.remove(RESPONSE_READY_FLAG)

    parts = line.split(",", 3)
    return {
        "should_reset" : parts[0] == "YES",
        "current_time" : parts[1] if len(parts) > 1 else "unknown",
        "last_reset"   : parts[2] if len(parts) > 2 else "never",
        "interval"     : parts[3] if len(parts) > 3 else "unknown",
    }
