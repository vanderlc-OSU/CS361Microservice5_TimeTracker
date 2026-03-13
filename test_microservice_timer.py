"""
test_microservice_timer.py — Unit tests for the timer microservice

Run the timer microservice first:  python microservice_timer.py
Then run this file             :  python test_microservice_timer.py

No code from microservice_timer.py is imported or called directly.
All communication happens through plain text files only.
"""

import os
import time
import sys
from datetime import datetime

# ── file protocol constants (duplicated here — no imports from other services) ─
TIMER_REQUEST_FILE        = "timer_request.txt"
TIMER_RESPONSE_FILE       = "timer_response.txt"
TIMER_REQUEST_READY_FLAG  = "timer_request_ready.flag"
TIMER_RESPONSE_READY_FLAG = "timer_response_ready.flag"
DATETIME_FMT              = "%Y-%m-%d %H:%M:%S"
TIMEOUT                   = 5.0
POLL_INTERVAL             = 0.05


def check_reset(service_name: str) -> dict:
    """
    Ask the timer microservice whether this service should reset.
    Communicates purely through text files — no imports of timer code.
    """
    with open(TIMER_REQUEST_FILE, "w") as f:
        f.write(service_name + "\n")
    open(TIMER_REQUEST_READY_FLAG, "w").close()

    deadline = time.time() + TIMEOUT
    while not os.path.exists(TIMER_RESPONSE_READY_FLAG):
        if time.time() > deadline:
            print("[test] ERROR: Timed out — is microservice_timer.py running?")
            sys.exit(1)
        time.sleep(POLL_INTERVAL)

    with open(TIMER_RESPONSE_FILE, "r") as f:
        line = f.read().strip()
    os.remove(TIMER_RESPONSE_READY_FLAG)

    parts = line.split(",", 3)
    return {
        "should_reset": parts[0] == "YES",
        "current_time": parts[1] if len(parts) > 1 else "unknown",
        "last_reset":   parts[2] if len(parts) > 2 else "never",
        "interval":     parts[3] if len(parts) > 3 else "unknown",
    }


# ── test runner ───────────────────────────────────────────────────────────────

def run_tests():
    print("Welcome to the microservice_timer unit tests\n")

    passed = 0
    failed = 0

    def check(label, actual, expected):
        nonlocal passed, failed
        ok = actual == expected
        print(f"  Test    : {label}")
        print(f"  Expected: {expected!r}")
        print(f"  Actual  : {actual!r}")
        print(f"  -> {'Passed test' if ok else 'Failed test'}\n")
        if ok:
            passed += 1
        else:
            failed += 1

    def check_true(label, condition):
        nonlocal passed, failed
        print(f"  Test    : {label}")
        print(f"  -> {'Passed test' if condition else 'Failed test'}\n")
        if condition:
            passed += 1
        else:
            failed += 1

    # Clean slate for test services
    LAST_RESET_FILE = "last_reset.txt"
    test_services = ["test_service_A", "test_service_B"]
    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, "r") as f:
            lines = f.readlines()
        filtered = [l for l in lines if not any(s in l for s in test_services)]
        with open(LAST_RESET_FILE, "w") as f:
            f.writelines(filtered)

    # ── Test 1: service responds ──────────────────────────────────────────
    print("=== Test 1: Service is reachable ===\n")
    result = check_reset("test_service_A")
    check_true("Response contains all expected keys",
               all(k in result for k in ("should_reset", "current_time", "last_reset", "interval")))

    # ── Test 2: first request always resets ──────────────────────────────
    print("=== Test 2: First request -> should_reset = True ===\n")
    result = check_reset("test_service_B")
    check("First-ever request should_reset", result["should_reset"], True)

    # ── Test 3: immediate second request → no reset ───────────────────────
    print("=== Test 3: Immediate repeat request -> should_reset = False ===\n")
    result2 = check_reset("test_service_B")
    check("Second immediate request should_reset", result2["should_reset"], False)

    # ── Test 4: current_time is a valid datetime string ───────────────────
    print("=== Test 4: current_time is a valid datetime string ===\n")
    try:
        datetime.strptime(result2["current_time"], DATETIME_FMT)
        valid_dt = True
    except ValueError:
        valid_dt = False
    check_true("current_time parses as YYYY-MM-DD HH:MM:SS", valid_dt)

    # ── Test 5: interval is daily or weekly ───────────────────────────────
    print("=== Test 5: interval is 'daily' or 'weekly' ===\n")
    check_true("interval is a valid value",
               result2["interval"] in ("daily", "weekly"))

    # ── Test 6: two services tracked independently ────────────────────────
    print("=== Test 6: Different services tracked independently ===\n")
    r_a = check_reset("test_service_A")
    r_b = check_reset("test_service_B")
    check("service_A independent NO", r_a["should_reset"], False)
    check("service_B independent NO", r_b["should_reset"], False)

    # ── Test 7: last_reset populated after first reset ────────────────────
    print("=== Test 7: last_reset field is populated (not 'never') ===\n")
    check_true("last_reset is not 'never' after first reset",
               r_b["last_reset"] != "never")

    # ── summary ───────────────────────────────────────────────────────────
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests.")
    print("\nThis concludes the microservice_timer unit tests.")
    print("Thank you for testing with us.")


if __name__ == "__main__":
    run_tests()
