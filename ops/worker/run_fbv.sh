#!/bin/bash
cd /data/lab/VeriFront
set -a; . /data/lab/.verifront_env; set +a
LIST=$1; TAG=$2; OUT=/data/lab/logs/fbv_run$3.log
ok=0; fail=0; n=0
while IFS= read -r cmd; do
  n=$((n+1))
  echo "[W-$TAG] [$n] $(date +%H:%M:%S)"
  if eval "$cmd" >> "$OUT" 2>&1; then ok=$((ok+1)); else fail=$((fail+1)); echo "[W-$TAG] FAIL $n" >> "$OUT"; fi
done < "$LIST"
echo "W-$TAG-DONE ok=$ok fail=$fail"
