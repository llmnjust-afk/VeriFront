#!/usr/bin/env bash
# Reproducible evidence chain: why nested containers are impossible on this host.
# Run on the target machine before planning any Docker-based evaluation (P0).
set -uo pipefail

echo "== Capabilities =="
grep -E 'CapEff|CapPrm' /proc/self/status
python3 - <<'PY'
caps = int(open('/proc/self/status').read().split('CapEff:')[1].split()[0], 16)
names = {0: 'CHOWN', 12: 'NET_RAW', 18: 'SYS_CHROOT', 21: 'SYS_ADMIN', 27: 'MKNOD', 29: 'AUDIT_WRITE', 31: 'SETFCAP'}
for bit, name in sorted(names.items()):
    print(f"CAP_{name}: {'set' if (caps >> bit) & 1 else 'NOT SET'}")
PY

echo "== seccomp mode (2 = filter active) =="
grep Seccomp /proc/self/status

echo "== unprivileged user namespace =="
echo "max_user_namespaces: $(cat /proc/sys/user/max_user_namespaces 2>/dev/null)"
unshare -Ur echo USERNS-OK 2>&1 || true

echo "== mount namespace (needs CAP_SYS_ADMIN) =="
unshare -m echo MNT-OK 2>&1 || true

echo "== host docker socket =="
ls -la /var/run/docker.sock 2>&1 || true

echo "== fuse (needed by rootless overlay) =="
ls -la /dev/fuse 2>&1 || true

echo "== dockerd (if installed) =="
if command -v dockerd >/dev/null 2>&1; then
  echo "dockerd present. Known failure mode on locked-down containers:"
  echo "  docker run ... -> failed to register layer: unshare: operation not permitted"
else
  echo "dockerd not installed"
fi

echo "== interpretation =="
cat <<'TXT'
Docker requires EITHER CAP_SYS_ADMIN (privileged DiD) OR unprivileged user
namespaces (rootless). If both are absent and no host docker.sock is mounted,
NO container runtime can work inside this container. Record the deviation and
switch to pinned conda/venv evaluation (docs/protocol_pilot.md §6) or request a
privileged/socket-enabled machine from the platform.
TXT
