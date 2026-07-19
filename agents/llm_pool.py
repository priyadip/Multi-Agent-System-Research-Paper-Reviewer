"""
LLMPool - rotate LLM calls across multiple OpenAI-compatible providers.

Purpose: spread requests across several free-tier providers (Groq, Gemini,
Cerebras, OpenRouter) so no single provider's rate limit is hit. Every call goes
to the next provider in round-robin; on a rate-limit/error it fails over to the
next provider automatically.

All four providers expose an OpenAI-compatible Chat Completions API, so a single
`openai` client (with a per-provider base_url) works for all of them.
"""

import time
from typing import List, Tuple, Dict


# Per-provider endpoint + a sensible default model.
# NOTE: model IDs change over time — update them from each provider's docs if a
# call returns "model not found". Groq IDs are verified via models.list().
PROVIDERS: Dict[str, Dict[str, str]] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.1-8b-instant",
        "keys_url": "https://console.groq.com/keys",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "deepseek-ai/deepseek-v4-flash",
        "keys_url": "https://build.nvidia.com",
        # DeepSeek is a reasoning model; disable "thinking" for fast, direct answers.
        "extra_body": {"chat_template_kwargs": {"thinking": False}},
    },
}


class LLMPool:
    """Round-robin pool of OpenAI-compatible providers with failover."""

    def __init__(self, provider_keys: List[Tuple[str, str]],
                 model_overrides: Dict[str, str] = None, rotate: bool = True,
                 attempts_per_provider: int = 1):
        """
        Args:
            provider_keys: list of (provider_name, api_key) to include in the pool.
            model_overrides: optional {provider_name: model_id} to override defaults.
            rotate: True = round-robin across providers (spread load). False = always
                    try the FIRST provider (primary), only fall through to the next on
                    failure (primary + fallback).
            attempts_per_provider: how many times to retry each provider (with
                    exponential backoff) on TRANSIENT errors (503/429/404/timeout/empty)
                    before moving to the next provider. Higher = accuracy-first (keep
                    trying the strong model until it responds).
        """
        self.rotate = rotate
        self.attempts_per_provider = max(1, attempts_per_provider)
        from openai import OpenAI
        model_overrides = model_overrides or {}
        self.entries = []  # list of (name, client, model)
        for name, key in provider_keys:
            if not key or name not in PROVIDERS:
                continue
            cfg = PROVIDERS[name]
            # max_retries=0: fail fast so the pool's own failover moves to the next
            # provider immediately instead of the SDK sleeping on 429 backoff.
            # Timeout tuned so a slow/hung provider fails fast enough to fall back
            # to the fallback provider without a long stall.
            client = OpenAI(api_key=key, base_url=cfg["base_url"],
                            max_retries=0, timeout=60.0)
            model = model_overrides.get(name, cfg["model"])
            extra_body = cfg.get("extra_body")
            self.entries.append((name, client, model, extra_body))
        self._i = 0
        self.down = set()  # circuit breaker: indices of providers that failed

    def __bool__(self):
        return len(self.entries) > 0

    @property
    def provider_names(self) -> List[str]:
        return [entry[0] for entry in self.entries]

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Send a chat request. Providers are tried in order (primary first when
        rotate=False). Each provider is retried up to `attempts_per_provider` times on
        TRANSIENT errors (503/429/404/timeout/empty) with exponential backoff before
        falling through to the next provider. PERMANENT errors (401/402/403) disable a
        provider via the circuit breaker. Calls are strictly sequential."""
        if not self.entries:
            return "Error: no API providers configured. Paste at least one key."

        n = len(self.entries)
        errors = []
        start = (self._i % n) if self.rotate else 0

        for step in range(n):
            idx = (start + step) % n
            if idx in self.down:
                continue
            name, client, model, extra_body = self.entries[idx]

            # Retry THIS provider up to attempts_per_provider times on transient errors.
            for attempt in range(self.attempts_per_provider):
                try:
                    kwargs = dict(model=model, messages=messages,
                                  temperature=temperature, max_tokens=max_tokens)
                    if extra_body:
                        kwargs["extra_body"] = extra_body
                    resp = client.chat.completions.create(**kwargs)
                    m = resp.choices[0].message
                    # Reasoning models (e.g. DeepSeek) may return the answer in
                    # reasoning_content when content is empty.
                    content = m.content or getattr(m, "reasoning_content", None) \
                        or getattr(m, "reasoning", None)
                    if content:
                        if self.rotate:
                            self._i = idx + 1  # next round-robin call moves on
                        return content
                    errors.append(f"{name}: empty response")  # transient
                except Exception as e:
                    msg = str(e)
                    errors.append(f"{name}: {msg[:70]}")
                    # Only auth/payment errors are permanent. NVIDIA's 404 (model
                    # briefly unavailable), 503 (workers busy), 429 (rate limit) and
                    # timeouts are all transient and worth retrying.
                    if any(c in msg for c in ("401", "402", "403")):
                        self.down.add(idx)
                        break  # don't retry a permanently-failed provider
                # Transient failure: back off, then retry the same provider.
                if attempt < self.attempts_per_provider - 1:
                    wait = min(25.0, 2.0 * (1.6 ** attempt))  # 2, 3.2, 5.1, ... cap 25s
                    print(f"[LLMPool] {name} transient failure; retry "
                          f"{attempt + 2}/{self.attempts_per_provider} in {wait:.0f}s")
                    time.sleep(wait)
            # Exhausted this provider's attempts (or it was disabled) -> next provider.

        return "Error: all providers failed — " + " | ".join(errors[-5:])
