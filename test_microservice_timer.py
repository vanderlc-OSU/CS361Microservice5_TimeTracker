"""
test_microservice_timer.py — Unit tests for the timer microservice

Run the timer microservice first:  python microservice_timer.py
Then run this file             :  python test_microservice_timer.py

Tests verify:
  1. Service responds to a reset check
  2. First-ever request always gets YES (never reset before)
  3. Immediate second request gets NO (just reset)
  4. Response fields are correctly formatted
  5. Multiple different service names are tracked independently
"""

import os
import sys
import time
from datetime import datetime

# Use the shared client helper — no direct import of microservice_timer
from timer_client import check_reset

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


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

    # Clean slate — remove any saved reset records for our test services
    LAST_RESET_FILE = "last_reset.txt"
    test_services = ["test_service_A", "test_service_B"]
    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, "r") as f:
            lines = f.readlines()
        filtered = [l for l in lines if not any(s in l for s in test_services)]
        with open(LAST_RESET_FILE, "w") as f:
            f.writelines(filtered)

    # ── Test 1: service responds at all ──────────────────────────────────
    print("=== Test 1: Service is reachable ===\n")
    result = check_reset("test_service_A")
    check_true("Timer service returns a dict with expected keys",
               all(k in result for k in ("should_reset", "current_time", "last_reset", "interval")))

    # ── Test 2: first request always triggers reset ───────────────────────
    print("=== Test 2: First request → should_reset = True ===\n")
    # test_service_A already ran above and got YES, last_reset is now set.
    # Use test_service_B which has no history.
    result = check_reset("test_service_B")
    check("First-ever request should_reset", result["should_reset"], True)

    # ── Test 3: immediate second request → no reset ───────────────────────
    print("=== Test 3: Immediate repeat request → should_reset = False ===\n")
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
    r_a = check_reset("test_service_A")   # already reset above → should be NO
    r_b = check_reset("test_service_B")   # already reset above → should be NO
    check("service_A independent NO", r_a["should_reset"], False)
    check("service_B independent NO", r_b["should_reset"], False)

    # ── Test 7: last_reset is populated after first reset ─────────────────
    print("=== Test 7: last_reset field is populated (not 'never') ===\n")
    check_true("last_reset is not 'never' after first reset",
               r_b["last_reset"] != "never")

    # ── summary ───────────────────────────────────────────────────────────
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests.")
    print("\nThis concludes the microservice_timer unit tests.")
    print("Thank you for testing with us.")


if __name__ == "__main__":
    run_tests()
