#\!/usr/bin/env bash
set -e
bad=0
check() {
  want="$1"; role="$2"
  got=$(ss -tulpen | awk '{print $5,$7}' | grep -E ":$want\b" | wc -l)
  if [ "$got" -ne 1 ]; then
    echo "PORT $want expected exactly 1 binder for $role, found $got"
    bad=1
  fi
}
check 5555 "ROUTER (command_router.py)"
check 5556 "PULL (telemetry bridge)"
check 5557 "PUB (Elite Guard)"
check 5558 "PULL (confirm listener)"
exit $bad
