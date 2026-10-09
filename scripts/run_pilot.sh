#!/usr/bin/env bash
# P3 pilot orchestrator scaffold. Real orchestration lands only after P0/P1 acceptance.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VeriFront pilot runner (scaffold) =="
if [ -z "${FRONTIER_API_KEY:-}" ]; then
  echo "MISSING env: FRONTIER_API_KEY — refusing to run real experiments."
  echo "Export FRONTIER_API_KEY / FRONTIER_BASE_URL after P0 provider selection."
fi

python3 - <<'PY'
import yaml

cfg = yaml.safe_load(open("configs/experiment.yaml", encoding="utf-8"))
print("stage plan (Prompt_V2 §7):")
for stage, spec in cfg["stages"].items():
    print(f"  {stage}: {spec}")
print("gates:", cfg["gates"])
print("pre_registration:", cfg["pre_registration"])
missing = [k for k in ("frontier_token_cap_per_run", "usd_cap_total") if cfg["budget"].get(k) is None]
if missing:
    print("NOTE: budget fields not yet measured (P0 TODO):", ", ".join(missing))
print("STATUS: scaffold only — complete P0 (repo pinning, smoke tasks, cost table) before real runs.")
PY
