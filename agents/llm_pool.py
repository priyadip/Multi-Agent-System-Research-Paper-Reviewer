"""
LLMPool - rotate LLM calls across multiple OpenAI-compatible providers.

Purpose: spread requests across several free-tier providers (Groq, Gemini,
Cerebras, OpenRouter) so no single provider's rate limit is hit. Every call goes
to the next provider in round-robin; on a rate-limit/error it fails over to the
next provider automatically.

All four providers expose an OpenAI-compatible Chat Completions API, so a single
`openai` client (with a per-provider base_url) works for all of them.
"""

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
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.0-flash",
        "keys_url": "https://aistudio.google.com/apikey",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "model": "llama-3.3-70b",
        "keys_url": "https://cloud.cerebras.ai",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "keys_url": "https://openrouter.ai/keys",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
        "keys_url": "https://build.nvidia.com",
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
            client = OpenAI(api_key=key, base_url=cfg["base_url"])
            model = model_overrides.get(name, cfg["model"])
            self.entries.append((name, client, model))
        self._i = 0

    def __bool__(self):
        return len(self.entries) > 0

    @property
    def provider_names(self) -> List[str]:
        return [name for name, _, _ in self.entries]

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Send a chat request, rotating providers and failing over on errors."""
        if not self.entries:
            return "Error: no API providers configured. Paste at least one key."

        n = len(self.entries)
        errors = []
        # Try up to 2 full rotations so a transient rate limit can recover.
        for _ in range(n * 2):
            name, client, model = self.entries[self._i % n]
            self._i += 1
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content
            except Exception as e:
                # Any failure (rate limit, bad model, network) -> try next provider.
                errors.append(f"{name}: {str(e)[:70]}")
                continue

        return "Error: all providers failed — " + " | ".join(errors[:4])
