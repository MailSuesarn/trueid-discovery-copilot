"""Typed application configuration.

Loads configs/app.yaml (path via $APP_CONFIG) and applies env-var overrides. Keep all
tunables in the YAML — no magic numbers in code. Env vars always win over the file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class AppCfg(BaseModel):
    name: str = "TrueID Discovery & Monetization Copilot"
    default_language: str = "th"


class RouterCfg(BaseModel):
    enabled: bool = True
    cheap_intents: list[str] = []


class LLMCfg(BaseModel):
    mode: Literal["provider", "extractive", "mock"] = "provider"
    model: str = "gpt-5.5"
    model_cheap: str = "gpt-5.4-mini"
    reasoning_effort: str = "low"
    verbosity: str = "low"
    max_output_tokens: int = 1024
    request_timeout_s: int = 30
    max_retries: int = 2
    router: RouterCfg = RouterCfg()


class EmbeddingsCfg(BaseModel):
    model: str = "text-embedding-3-large"
    dimensions: int = 1024
    cache_path: str = "data/index/embeddings.npz"


class HybridCfg(BaseModel):
    use_bm25: bool = True
    use_dense: bool = True
    rrf_k: int = 60
    bm25_weight: float = 1.0
    dense_weight: float = 1.0


class RetrievalCfg(BaseModel):
    top_k: int = 5
    candidate_k: int = 20
    hybrid: HybridCfg = HybridCfg()


class GuardrailsCfg(BaseModel):
    pii_redaction: bool = True
    max_input_chars: int = 2000
    rate_limit_per_min: int = 60


class MonetizationCfg(BaseModel):
    enabled: bool = True
    max_discount_pct: int = 20
    eligible_actions: list[str] = ["play", "upgrade", "redeem", "none"]


class EvalThresholds(BaseModel):
    hit_at_3: float = 0.80
    action_accuracy: float = 0.90
    groundedness: float = 0.90


class EvalCfg(BaseModel):
    golden_path: str = "data/golden.jsonl"
    thresholds: EvalThresholds = EvalThresholds()


class ObservabilityCfg(BaseModel):
    log_level: str = "INFO"
    log_format: str = "json"
    cost_accounting: bool = True


class Settings(BaseModel):
    app: AppCfg = AppCfg()
    llm: LLMCfg = LLMCfg()
    embeddings: EmbeddingsCfg = EmbeddingsCfg()
    retrieval: RetrievalCfg = RetrievalCfg()
    guardrails: GuardrailsCfg = GuardrailsCfg()
    monetization: MonetizationCfg = MonetizationCfg()
    eval: EvalCfg = EvalCfg()
    observability: ObservabilityCfg = ObservabilityCfg()

    @property
    def has_openai_key(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY", "").strip())

    @property
    def effective_mode(self) -> str:
        """provider auto-degrades to extractive when no key is present."""
        if self.llm.mode == "provider" and not self.has_openai_key:
            return "extractive"
        return self.llm.mode


def _apply_env_overrides(data: dict) -> dict:
    llm = data.setdefault("llm", {})
    if v := os.getenv("LLM_MODE"):
        llm["mode"] = v
    if v := os.getenv("OPENAI_MODEL"):
        llm["model"] = v
    if v := os.getenv("OPENAI_MODEL_CHEAP"):
        llm["model_cheap"] = v
    emb = data.setdefault("embeddings", {})
    if v := os.getenv("OPENAI_EMBED_MODEL"):
        emb["model"] = v
    return data


@lru_cache
def get_settings() -> Settings:
    path = Path(os.getenv("APP_CONFIG", "configs/app.yaml"))
    data: dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data = _apply_env_overrides(data)
    return Settings(**data)
