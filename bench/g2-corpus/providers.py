"""G2 provider registry. Every provider speaks the OpenAI chat-completions
dialect; a model is used ONLY if its provider's env key is set (or Ollama is
up locally). Model lists are the preferred defaults - override with
run_g2.py --models. `delay` = minimum seconds between calls (free-tier RPM).
"""
from __future__ import annotations
import json, os, urllib.request

PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "env_key": None,                       # local, keyless
        "models": ["llama3.2", "qwen2.5:7b", "llama3.1:8b", "qwen2.5:14b"],
        "delay": 0.0,
    },
    # model ids verified against each provider's live /models on 2026-07-20
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "models": ["llama-3.3-70b-versatile", "openai/gpt-oss-120b",
                   "qwen/qwen3.6-27b", "llama-3.1-8b-instant"],
        "delay": 3.0,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "env_key": "GEMINI_API_KEY",
        "models": ["gemini-3.5-flash"],   # 3-flash-preview free tier = 20 req/day, unusable
        "delay": 5.0,
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "models": ["zai-glm-4.7", "gemma-4-31b"],
        "delay": 1.5,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "models": ["nvidia/nemotron-3-super-120b-a12b:free"],
        "delay": 4.0,
    },
}


def ollama_tags(timeout=3):
    """Installed local models + digests (the reproducibility pin for Ollama)."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout) as r:
            data = json.loads(r.read())
        return {m["name"]: m["digest"][:12] for m in data.get("models", [])}
    except Exception:
        return None


def available(only=None):
    """[(provider, model, base_url, api_key, delay, pin)] for reachable providers."""
    out = []
    for name, cfg in PROVIDERS.items():
        if only and name not in only:
            continue
        if name == "ollama":
            tags = ollama_tags()
            if tags is None:
                continue
            names = {t.split(":")[0] if t.endswith(":latest") else t: t for t in tags}
            for want in cfg["models"]:
                hit = names.get(want) or (want if want in tags else None)
                if hit:
                    out.append((name, hit, cfg["base_url"], None, cfg["delay"],
                                f"digest={tags[hit]}"))
            continue
        key = os.environ.get(cfg["env_key"] or "", "")
        if not key:
            continue
        for m in cfg["models"]:
            out.append((name, m, cfg["base_url"], key, cfg["delay"], ""))
    return out
