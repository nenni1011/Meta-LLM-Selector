"""Tests for Meta-LLM-Selector — state models, JSON parsing, and pipeline helpers."""

from __future__ import annotations

import json
import pytest

from state import (
    MetaLLMState,
    ModelCandidate,
    ModelRecommendation,
    ScoredModel,
)
from crew import _extract_json, _safe_parse_json


# ═══════════════════════════════════════════════
# State Model Tests
# ═══════════════════════════════════════════════


class TestMetaLLMState:
    """Tests for the central state model."""

    def test_default_state(self):
        state = MetaLLMState()
        assert state.task_type == "general"
        assert state.budget_tier == "medium"
        assert state.latency_requirement == "interactive"
        assert state.tool_calling_needed is False
        assert state.candidate_models == []
        assert state.scored_candidates == []
        assert state.recommendations == []

    def test_state_with_data(self):
        state = MetaLLMState(
            raw_prompt="I need a coding assistant",
            task_type="coding",
            use_case_detail="Build a VS Code copilot alternative",
            context_window_needed="large",
            budget_tier="low",
            tool_calling_needed=True,
        )
        assert state.task_type == "coding"
        assert state.context_window_needed == "large"
        assert state.tool_calling_needed is True

    def test_state_with_candidates(self):
        candidate = ModelCandidate(
            name="GPT-4o",
            provider="OpenAI",
            input_cost_per_million=2.50,
            context_window=128000,
            tool_calling=True,
        )
        state = MetaLLMState(candidate_models=[candidate])
        assert len(state.candidate_models) == 1
        assert state.candidate_models[0].name == "GPT-4o"


class TestModelCandidate:
    """Tests for ModelCandidate."""

    def test_minimal_candidate(self):
        c = ModelCandidate(name="TestModel")
        assert c.name == "TestModel"
        assert c.provider == ""
        assert c.input_cost_per_million is None
        assert c.multimodal is False

    def test_full_candidate(self):
        c = ModelCandidate(
            name="Claude 3.5 Sonnet",
            provider="Anthropic",
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
            context_window=200000,
            latency_ms=800,
            throughput_tps=50,
            mmlu_score=89.0,
            humaneval_score=92.0,
            coding_score=88.0,
            tool_calling=True,
            multimodal=True,
            source_url="https://artificialanalysis.ai",
            notes="Top coding model",
        )
        assert c.context_window == 200000
        assert c.tool_calling is True

    def test_candidate_from_dict(self):
        data = {
            "name": "Gemini Pro",
            "provider": "Google",
            "input_cost_per_million": 1.25,
            "output_cost_per_million": 5.0,
            "context_window": 1000000,
        }
        c = ModelCandidate(**data)
        assert c.name == "Gemini Pro"
        assert c.context_window == 1000000


class TestScoredModel:
    """Tests for ScoredModel."""

    def test_scored_model(self):
        m = ScoredModel(
            name="GPT-4o",
            provider="OpenAI",
            tier="premium",
            overall_score=88.5,
            cost_score=40.0,
            performance_score=95.0,
            speed_score=75.0,
            fit_score=90.0,
        )
        assert m.tier == "premium"
        assert m.overall_score == 88.5


class TestModelRecommendation:
    """Tests for ModelRecommendation."""

    def test_recommendation(self):
        r = ModelRecommendation(
            tier="balanced",
            model_name="Claude 3.5 Sonnet",
            provider="Anthropic",
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
            context_window=200000,
            speed_label="medium",
            justification="Best balance of cost and quality for coding tasks.",
        )
        assert r.tier == "balanced"
        assert "coding" in r.justification


# ═══════════════════════════════════════════════
# JSON Parsing Tests
# ═══════════════════════════════════════════════


class TestExtractJson:
    """Tests for _extract_json helper."""

    def test_plain_json_object(self):
        text = '{"task_type": "coding", "budget_tier": "low"}'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert parsed["task_type"] == "coding"

    def test_json_in_code_block(self):
        text = 'Here is the result:\n```json\n{"task_type": "coding"}\n```\nDone.'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert parsed["task_type"] == "coding"

    def test_json_array(self):
        text = 'Models found:\n[{"name": "GPT-4o"}, {"name": "Claude"}]'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_json_array_in_code_block(self):
        text = '```\n[{"name": "GPT-4o"}]\n```'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert parsed[0]["name"] == "GPT-4o"

    def test_no_json(self):
        text = "Just some plain text"
        result = _extract_json(text)
        assert result == "Just some plain text"


class TestSafeParseJson:
    """Tests for _safe_parse_json helper."""

    def test_valid_json(self):
        result = _safe_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_trailing_comma(self):
        result = _safe_parse_json('{"key": "value",}')
        assert result == {"key": "value"}

    def test_invalid_json_fallback(self):
        result = _safe_parse_json("not json at all", fallback="[]")
        assert result == []

    def test_array_parse(self):
        result = _safe_parse_json('[{"name": "model1"}, {"name": "model2"}]', fallback="[]")
        assert len(result) == 2

    def test_json_in_markdown(self):
        text = "Result:\n```json\n{\"task_type\": \"coding\"}\n```"
        result = _safe_parse_json(text)
        assert result["task_type"] == "coding"


# ═══════════════════════════════════════════════
# Integration-style tests (no API calls)
# ═══════════════════════════════════════════════


class TestStateFlow:
    """Test that state can be built up step by step as the pipeline would."""

    def test_full_state_flow(self):
        # Step 1: Create state from user input
        state = MetaLLMState(raw_prompt="I need a coding assistant for my startup")

        # Step 2: Simulate intake parsing
        intake_data = {
            "task_type": "coding",
            "use_case_detail": "Coding assistant for startup",
            "context_window_needed": "large",
            "latency_requirement": "interactive",
            "tool_calling_needed": True,
            "budget_tier": "medium",
            "scale": "startup",
            "output_format": "code",
        }
        for field, value in intake_data.items():
            setattr(state, field, value)

        assert state.task_type == "coding"
        assert state.scale == "startup"

        # Step 3: Add candidates
        state.candidate_models.append(
            ModelCandidate(name="GPT-4o", provider="OpenAI", input_cost_per_million=2.5)
        )
        state.candidate_models.append(
            ModelCandidate(name="Gemini Flash", provider="Google", input_cost_per_million=0.075)
        )
        assert len(state.candidate_models) == 2

        # Step 4: Add scored models
        state.scored_candidates.append(
            ScoredModel(name="GPT-4o", tier="premium", overall_score=88.0)
        )
        state.scored_candidates.append(
            ScoredModel(name="Gemini Flash", tier="budget", overall_score=72.0)
        )
        assert len(state.scored_candidates) == 2

        # Step 5: Add recommendations
        state.recommendations.append(
            ModelRecommendation(
                tier="budget",
                model_name="Gemini Flash",
                justification="Cheapest option with good coding support.",
            )
        )
        state.recommendations.append(
            ModelRecommendation(
                tier="premium",
                model_name="GPT-4o",
                justification="Top coding benchmarks.",
            )
        )
        assert len(state.recommendations) == 2

    def test_serialization_roundtrip(self):
        """Test that state can be serialized to JSON and back."""
        state = MetaLLMState(
            raw_prompt="test",
            task_type="coding",
            candidate_models=[
                ModelCandidate(name="TestModel", provider="TestProvider")
            ],
        )
        json_str = state.model_dump_json()
        restored = MetaLLMState.model_validate_json(json_str)
        assert restored.task_type == "coding"
        assert restored.candidate_models[0].name == "TestModel"
