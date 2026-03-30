"""Pydantic state models for Meta-LLM-Selector pipeline."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ModelCandidate(BaseModel):
    """Raw model data fetched during research phase."""

    name: str = Field(description="Model name (e.g. GPT-4o, Claude 3.5 Sonnet)")
    provider: str = Field(default="", description="Provider (OpenAI, Anthropic, Google, etc.)")
    input_cost_per_million: Optional[float] = Field(default=None, description="USD per 1M input tokens")
    output_cost_per_million: Optional[float] = Field(default=None, description="USD per 1M output tokens")
    context_window: Optional[int] = Field(default=None, description="Max context window in tokens")
    latency_ms: Optional[float] = Field(default=None, description="Median output latency in ms")
    throughput_tps: Optional[float] = Field(default=None, description="Tokens per second throughput")
    mmlu_score: Optional[float] = Field(default=None, description="MMLU benchmark score")
    humaneval_score: Optional[float] = Field(default=None, description="HumanEval benchmark score")
    coding_score: Optional[float] = Field(default=None, description="General coding benchmark score")
    tool_calling: Optional[bool] = Field(default=None, description="Whether the model supports tool/function calling")
    multimodal: bool = Field(default=False, description="Whether the model supports image/audio input")
    source_url: str = Field(default="", description="Source URL for the data")
    notes: str = Field(default="", description="Extra notes from research")


class ScoredModel(BaseModel):
    """Model candidate with computed scores and tier assignment."""

    name: str
    provider: str = ""
    tier: str = Field(description="budget | balanced | premium")
    overall_score: float = Field(description="Weighted composite score 0-100")
    cost_score: float = Field(default=0.0, description="Cost efficiency score 0-100")
    performance_score: float = Field(default=0.0, description="Benchmark/quality score 0-100")
    speed_score: float = Field(default=0.0, description="Latency/throughput score 0-100")
    fit_score: float = Field(default=0.0, description="Use-case fit score 0-100")
    input_cost_per_million: Optional[float] = None
    output_cost_per_million: Optional[float] = None
    context_window: Optional[int] = None
    latency_ms: Optional[float] = None
    throughput_tps: Optional[float] = None


class ModelRecommendation(BaseModel):
    """Final recommendation card for one tier."""

    tier: str = Field(description="budget | balanced | premium")
    model_name: str
    provider: str = ""
    input_cost_per_million: Optional[float] = None
    output_cost_per_million: Optional[float] = None
    context_window: Optional[int] = None
    speed_label: str = Field(default="", description="fast | medium | slow")
    justification: str = Field(description="2-3 sentences explaining why this model was chosen")


class MetaLLMState(BaseModel):
    """Central state object that flows through all agents."""

    # ── Gathered by Intake Agent ──
    raw_prompt: str = Field(default="", description="Original user input")
    task_type: str = Field(
        default="general",
        description="coding | writing | analysis | chat | agentic | multimodal | general",
    )
    use_case_detail: str = Field(default="", description="Expanded description of the use case")
    context_window_needed: str = Field(default="medium", description="small (<8k) | medium (8-32k) | large (32-128k) | very_large (>128k)")
    latency_requirement: str = Field(default="interactive", description="realtime | interactive | batch")
    tool_calling_needed: bool = Field(default=False)
    budget_tier: str = Field(default="medium", description="free | low | medium | high | no_limit")
    scale: str = Field(default="personal", description="personal | startup | enterprise")
    output_format: str = Field(default="text", description="text | code | json | mixed")

    # ── Populated by Research Agent ──
    candidate_models: List[ModelCandidate] = Field(default_factory=list)

    # ── Populated by Scoring Agent ──
    scored_candidates: List[ScoredModel] = Field(default_factory=list)

    # ── Populated by Decision Agent ──
    recommendations: List[ModelRecommendation] = Field(default_factory=list)
