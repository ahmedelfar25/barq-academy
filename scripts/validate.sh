#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8090}"

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

echo "== Container status =="
docker compose ps

echo
echo "== Required endpoints =="

for endpoint in / /health /ready /instance /records /counter; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    echo "$endpoint -> $status"

    [[ "$status" == "200" ]] || fail "$endpoint returned HTTP $status"
done

echo
echo "== Instance identity =="

instances=$(for i in {1..15}; do
    curl -s "$BASE_URL/instance"
done | python3 -c '
import sys, json
ids = {json.loads(line)["instance_id"] for line in sys.stdin if line.strip()}
print("\n".join(sorted(ids)))
')

echo "$instances"

instance_count=$(printf '%s\n' "$instances" | grep -c . || true)

[[ "$instance_count" -ge 3 ]] || fail "Expected traffic from at least three instances"
for expected in app-01 app-02 app-03; do
    echo "$instances" | grep -qx "$expected" || fail "$expected did not receive traffic"
done
echo
echo "== Database =="

records=$(curl -s "$BASE_URL/records")

echo "$records" | python3 -c '
import json, sys
data = json.load(sys.stdin)
records = data.get("records", [])
if not records:
    raise SystemExit("No records returned")
print(f"records={len(records)}")
'

echo
echo "== Redis counter =="

counter1=$(curl -s "$BASE_URL/counter" | python3 -c 'import json,sys; print(json.load(sys.stdin)["counter"])')
counter2=$(curl -s "$BASE_URL/counter" | python3 -c 'import json,sys; print(json.load(sys.stdin)["counter"])')

echo "counter1=$counter1"
echo "counter2=$counter2"

[[ "$counter2" -gt "$counter1" ]] || fail "Redis counter did not increment"

echo
echo "== Network isolation =="

ports=$(docker ps --format '{{.Names}}\t{{.Ports}}')

echo "$ports"

if echo "$ports" | grep -E 'postgres.*0\.0\.0\.0|redis.*0\.0\.0\.0|app-01.*0\.0\.0\.0|app-02.*0\.0\.0\.0|app-03.*0\.0\.0\.0'; then
    fail "Internal service exposed on host port"
fi

echo
echo "== Security =="

for container in app-01 app-02 app-03; do
    user=$(docker inspect "$container" --format '{{.Config.User}}')
    readonly=$(docker inspect "$container" --format '{{.HostConfig.ReadonlyRootfs}}')

    echo "$container: user=$user readonly=$readonly"

    [[ "$user" == "app" ]] || fail "$container is not running as app"
    [[ "$readonly" == "true" ]] || fail "$container root filesystem is writable"
done

echo
echo "================================"
echo "VALIDATION PASSED"
echo "================================"
