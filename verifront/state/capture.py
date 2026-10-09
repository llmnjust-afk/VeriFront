"""Capture the pre-state of a replacement point (Prompt_V2 §4.1).

Covers: filesystem manifest (SHA-256), environment digest (python/package
versions, env vars), agent-observable context digest, process probes (arbitrary
named callables supplied by the execution environment), and external state
(marked unsupported when it cannot be controlled).
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

DEFAULT_PROBED_PACKAGES = ["openai", "vllm", "torch", "transformers", "openhands"]


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_fs_manifest(paths: List[os.PathLike | str]) -> Dict[str, Dict[str, Any]]:
    """{path_str: {sha256, size}}; missing paths recorded explicitly as missing=False."""
    manifest: Dict[str, Dict[str, Any]] = {}
    for p in paths:
        pp = Path(p)
        key = str(pp)
        if pp.is_file():
            manifest[key] = {"sha256": _sha256_of_file(pp), "size": pp.stat().st_size, "missing": False}
        else:
            manifest[key] = {"missing": True}
    return manifest


def capture_env_digest(
    packages: Optional[List[str]] = None,
    env_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    pkgs = packages if packages is not None else DEFAULT_PROBED_PACKAGES
    versions = {}
    for name in pkgs:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
        "env": {k: os.environ.get(k) for k in (env_keys or [])},
    }


def agent_context_digest(context: str) -> str:
    """Digest of the agent-observable context. Normalization (timestamps etc.)
    is the equivalence layer's job; this digest is exact-bytes."""
    return hashlib.sha256(context.encode("utf-8")).hexdigest()


@dataclass
class PreState:
    """Everything a paired arm must share before the replaced step executes."""

    fs_manifest: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    env_digest: Dict[str, Any] = field(default_factory=dict)
    agent_context: str = ""
    process_probe: Optional[Dict[str, Any]] = None
    external: Optional[Dict[str, Any]] = None  # None => external state not controlled
    extra: Dict[str, Any] = field(default_factory=dict)


def probe_values(probes: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:
    """Run named probe callables; errors are recorded, never raised."""
    out: Dict[str, Any] = {}
    for name, fn in probes.items():
        try:
            out[name] = fn()
        except Exception as e:  # noqa: BLE001 - probe failure must be visible, not fatal
            out[name] = f"<probe_error:{type(e).__name__}>"
    return out
