#!/usr/bin/env python3

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8080"
BACKEND = "app-01"
REQUESTS_DURING_FAILURE = 20
REQUESTS_AFTER_RECOVERY = 20


def run(cmd, check=True):
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def wait_for_health(container, timeout=60):
    deadline = time.time() + timeout

    while time.time() < deadline:
        result = run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Health.Status}}",
                container,
            ],
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip() == "healthy":
            return True

        time.sleep(2)

    return False


def request_instance():
    try:
        with urllib.request.urlopen(
            f"{BASE_URL}/instance",
            timeout=3,
        ) as response:
            body = response.read().decode()
            return response.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception:
        return 0, ""


def main():
    print("== Failure / Recovery Test ==")

    # Make sure the selected backend is running before the test.
    state = run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}",
            BACKEND,
        ]
    ).stdout.strip()

    if state != "running":
        print(f"{BACKEND} is not running. Starting it first...")
        run(["docker", "start", BACKEND])
        if not wait_for_health(BACKEND):
            print(f"FAIL: {BACKEND} did not become healthy.")
            return 1

    print(f"\nStopping {BACKEND}...")
    run(["docker", "stop", BACKEND])

    print("\n== Traffic during backend failure ==")

    total = 0
    successful = 0
    errors = 0
    other = 0
    app02_seen = 0

    for _ in range(REQUESTS_DURING_FAILURE):
        status, body = request_instance()
        total += 1

        if status == 200:
            successful += 1

            if '"instance_id":"app-02"' in body:
                app02_seen += 1

        elif status in (502, 503, 504):
            errors += 1
        else:
            other += 1

    print(f"total_requests={total}")
    print(f"successful_requests={successful}")
    print(f"gateway_errors={errors}")
    print(f"other_responses={other}")
    print(f"app-02_responses={app02_seen}")

    if app02_seen == 0:
        print("FAIL: surviving backend app-02 did not serve traffic.")
        run(["docker", "start", BACKEND], check=False)
        return 1

    if errors == 0:
        print("WARNING: no gateway errors observed during failure.")
        print("This can happen depending on request routing/timing.")

    print(f"\nStarting {BACKEND} again...")
    run(["docker", "start", BACKEND])

    if not wait_for_health(BACKEND):
        print(f"FAIL: {BACKEND} did not recover to healthy state.")
        return 1

    print(f"{BACKEND} is healthy again.")

    print("\n== Traffic after recovery ==")

    recovered_total = 0
    recovered_success = 0
    app01_seen = 0
    app02_seen_after = 0
    recovery_errors = 0

    for _ in range(REQUESTS_AFTER_RECOVERY):
        status, body = request_instance()
        recovered_total += 1

        if status == 200:
            recovered_success += 1

            if '"instance_id":"app-01"' in body:
                app01_seen += 1

            if '"instance_id":"app-02"' in body:
                app02_seen_after += 1
        else:
            recovery_errors += 1

    print(f"total_requests={recovered_total}")
    print(f"successful_requests={recovered_success}")
    print(f"recovery_errors={recovery_errors}")
    print(f"app-01_responses={app01_seen}")
    print(f"app-02_responses={app02_seen_after}")

    if app01_seen == 0:
        print("FAIL: recovered backend app-01 did not serve requests.")
        return 1

    if app02_seen_after == 0:
        print("FAIL: app-02 stopped serving traffic after recovery.")
        return 1

    if recovery_errors != 0:
        print("FAIL: errors remained after backend recovery.")
        return 1

    print("\n================================")
    print("FAILURE TEST PASSED")
    print("================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())

