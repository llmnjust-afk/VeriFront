#!/bin/bash
cd /data/lab/VeriFront
set -a; . /data/lab/.verifront_env; set +a
ok=0; fail=0; n=0
while IFS= read -r cmd; do
  n=$((n+1))
  echo "[WORKER FB] [$n/48] $(date +%H:%M:%S)"
  if eval "$cmd" >> /data/lab/logs/fb_run.log 2>&1; then
    ok=$((ok+1))
  else
    fail=$((fail+1)); echo "[WORKER FB] FAIL cmd $n" >> /data/lab/logs/fb_run.log
  fi
done < /data/lab/fb_cmds.txt
echo "WORKER-FB-DONE ok=$ok fail=$fail"
