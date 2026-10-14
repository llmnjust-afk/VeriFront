#!/bin/bash
cd /data/lab/VeriFront
set -a; . /data/lab/.verifront_env; set +a
ok=0; fail=0; n=0
while IFS= read -r cmd; do
  n=$((n+1))
  echo "[SFX$2] [$n] $(date +%H:%M:%S)"
  if eval "$cmd" >> /data/lab/logs/sfx_r$2.log 2>&1; then ok=$((ok+1)); else fail=$((fail+1)); echo "[SFX$2] FAIL $n" >> /data/lab/logs/sfx_r$2.log; fi
done < $1
echo "SFX$2-DONE ok=$ok fail=$fail"
