#!/usr/bin/env bash
# VeriFront P0 smoke test: environment probe + full unit test suite (Prompt_V2 Appendix A).
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0

echo "== VeriFront smoke test =="
echo "-- python --"; python3 --version || fail=1
echo "-- git --";    git --version    || fail=1
echo "-- docker --"
if command -v docker >/dev/null 2>&1; then
  docker --version
else
  echo "WARN: docker NOT found — SAB official evaluation is containerized (docs/protocol_pilot.md §6); resolve before P0 evaluation runs."
fi
echo "-- gpu --"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo "WARN: no GPU visible (P3 local-model serving will need one)"
fi
echo "-- disk --"; df -h / | tail -1
echo "-- unit tests --"
python3 -m pytest -q || fail=1
echo "== result: $([ "$fail" -eq 0 ] && echo PASS || echo FAIL) =="
exit $fail
