"""
CanonCache — LM Studio Auto-Detection & API Client
Handles model discovery, health checks, and completions.
"""

import json
import time
import socket
import threading
import requests
from typing import Optional, Generator

# LM Studio default ports to probe
CANDIDATE_PORTS = [1234, 1235, 1236, 8080, 8000, 5000]
CANDIDATE_HOSTS = ["127.0.0.1", "localhost"]
TIMEOUT = 5  # seconds


class LMStudioClient:
    """OpenAI-compatible client for LM Studio local inference server."""

    def __init__(self):
        self.base_url: Optional[str] = None
        self.models: list[dict] = []
        self.active_model: Optional[str] = None
        self._lock = threading.Lock()

    # ── Discovery ────────────────────────────────────────────────────────────

    def auto_detect(self) -> bool:
        """Probe all candidate host:port pairs and pick the first live server."""
        for host in CANDIDATE_HOSTS:
            for port in CANDIDATE_PORTS:
                url = f"http://{host}:{port}"
                try:
                    # Fast socket probe first (cheaper than HTTP)
                    s = socket.create_connection((host, port), timeout=1)
                    s.close()
                    # Now check the actual /v1/models endpoint
                    resp = requests.get(f"{url}/v1/models", timeout=TIMEOUT)
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("data", [])
                        if models:
                            with self._lock:
                                self.base_url = url
                                self.models = models
                                self.active_model = models[0]["id"]
                            return True
                except Exception:
                    continue
        return False

    def refresh_models(self) -> list[str]:
        """Refresh model list from a known base_url."""
        if not self.base_url:
            return []
        try:
            resp = requests.get(f"{self.base_url}/v1/models", timeout=TIMEOUT)
            if resp.status_code == 200:
                self.models = resp.json().get("data", [])
                return [m["id"] for m in self.models]
        except Exception:
            pass
        return []

    def is_alive(self) -> bool:
        """Quick health check."""
        if not self.base_url:
            return False
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    # ── Inference ────────────────────────────────────────────────────────────

    def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict:
        """
        Run a single completion.
        Returns: {"text": str, "latency_ms": float, "tokens_used": int, "error": Optional[str]}
        """
        if not self.base_url or not self.active_model:
            return {"text": "", "latency_ms": 0, "tokens_used": 0, "error": "No model connected."}

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.active_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        t0 = time.perf_counter()
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120,
            )
            latency = (time.perf_counter() - t0) * 1000
            if resp.status_code != 200:
                return {"text": "", "latency_ms": latency, "tokens_used": 0, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            return {"text": text, "latency_ms": latency, "tokens_used": total_tokens, "error": None}
        except requests.exceptions.Timeout:
            return {"text": "", "latency_ms": 0, "tokens_used": 0, "error": "Request timed out (120s)."}
        except Exception as e:
            return {"text": "", "latency_ms": 0, "tokens_used": 0, "error": str(e)}

    def stream_complete(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Streaming chat completion — yields text delta chunks."""
        if not self.base_url or not self.active_model:
            yield "[ERROR] No model connected."
            return

        payload = {
            "model": self.active_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            with requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=120,
            ) as resp:
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            yield f"\n[ERROR] {e}"
