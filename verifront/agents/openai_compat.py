"""Minimal OpenAI-compatible chat client (stdlib only; works with frontier APIs
and local vLLM/SGLang servers alike).

Security: the API key is taken from the constructor or the environment; it is
never logged and never persisted by this module.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class ChatError(RuntimeError):
    pass


_RETRY_STATUS = {429, 500, 502, 503, 504}


class OpenAICompatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        timeout_s: float = 120.0,
        max_retries: int = 2,
        backoff_s: float = 2.0,
        snapshot: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.snapshot = snapshot
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        if api_key is None:
            api_key = os.environ.get(api_key_env, "")
        self.api_key = api_key

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """POST /chat/completions; returns {content, token_usage, model, latency_s}."""
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            body["seed"] = seed
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            start = time.monotonic()
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=json.dumps(body).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                latency = time.monotonic() - start
                usage = payload.get("usage") or {}
                choice = (payload.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                return {
                    "content": message.get("content"),
                    "token_usage": {
                        "prompt": int(usage.get("prompt_tokens", 0)),
                        "completion": int(usage.get("completion_tokens", 0)),
                    },
                    "model": payload.get("model", self.model),
                    "latency_s": latency,
                    "raw": payload,
                }
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code not in _RETRY_STATUS or attempt == self.max_retries:
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = e
                if attempt == self.max_retries:
                    break
            time.sleep(self.backoff_s * (attempt + 1))
        raise ChatError(f"chat request failed after retries: {last_err!r}")
