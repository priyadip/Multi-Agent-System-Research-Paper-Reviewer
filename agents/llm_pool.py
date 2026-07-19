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
                 model_overrides: Dict[str, str] = None):
        """
        Args:
            provider_keys: list of (provider_name, api_key) to include in the pool.
            model_overrides: optional {provider_name: model_id} to override defaults.
        """
        from openai import OpenAI
        model_overrides = model_overrides or {}
        self.entries = []  # list of (name, client, model)
        for name, key in provider_keys:
            if not key or name not in PROVIDERS:
                continue
            cfg = PROVIDERS[name]
            # max_retries=0: fail fast so the pool's own failover moves to the next
            # provider immediately instead of the SDK sleeping on 429 backoff.
            # Generous timeout: NVIDIA's free-tier reasoning models can take up to
            # ~90s. A truly hung request still fails via the circuit breaker.
            client = OpenAI(api_key=key, base_url=cfg["base_url"],
                            max_retries=0, timeout=120.0)
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
        """Send a chat request, rotating providers and failing over on errors."""
        if not self.entries:
            return "Error: no API providers configured. Paste at least one key."

        n = len(self.entries)
        errors = []

        # Up to 3 rounds: each round rotates once through the live providers. If a
        # round finds every live provider only *rate-limited* (transient), wait and
        # retry so free-tier per-minute limits can reset. Permanently-failed
        # providers (payment/model/auth/timeout) are disabled via the circuit breaker.
        for attempt in range(3):
            checked = 0
            had_transient = False
            while checked < n:
                idx = self._i % n
                self._i += 1
                if idx in self.down:
                    checked += 1
                    continue
                name, client, model, extra_body = self.entries[idx]
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
                        return content
                    # Empty response: treat as a transient failure and rotate.
                    errors.append(f"{name}: empty response")
                    had_transient = True
                    checked += 1
                    continue
                except Exception as e:
                    msg = str(e)
                    errors.append(f"{name}: {msg[:70]}")
                    permanent = (any(c in msg for c in ("401", "402", "403", "404"))
                                 or "timed out" in msg.lower() or "timeout" in msg.lower())
                    if permanent:
                        self.down.add(idx)
                    else:
                        had_transient = True  # e.g. 429 rate limit
                    checked += 1
                    continue

            # All live providers failed this round. If any were just rate-limited,
            # back off and try again (limits reset over ~a minute).
            if had_transient and attempt < 2:
                time.sleep(15 * (attempt + 1))  # 15s, then 30s
                continue
            break

        return "Error: all providers failed — " + " | ".join(errors[:5])
