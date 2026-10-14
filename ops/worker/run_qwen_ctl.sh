#!/bin/bash
set -a && . /data/lab/.verifront_env && set +a
cd /data/lab/VeriFront
ok=0; fail=0; n=0
while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  n=$((n+1))
  out=$(eval "$cmd" 2>&1 | tail -1)
  echo "[$n/40] $out"
  case "$out" in
    *BALANCE*|*"余额"*) echo "BALANCE-STOP"; exit 42;;
  esac
  case "$out" in
    *'"eval_success": 1'*|*'"eval_success": 0'*) ok=$((ok+1));;
    *) fail=$((fail+1));;
  esac
done < /data/lab/scan_cmds.txt
echo "WORKER-DONE ok=$ok fail=$fail total=$n"
