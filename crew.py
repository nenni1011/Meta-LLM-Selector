"""CrewAI pipeline orchestrator — wires agents, tasks, and state together."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, List, Union

from crewai import Crew, LLM, Process

from agents.intake_agent import create_intake_agent
from agents.research_agent import create_research_agent
from agents.scoring_agent import create_scoring_agent
from agents.decision_agent import create_decision_agent
from tasks.intake_task import create_intake_task
from tasks.research_task import create_research_task
from tasks.scoring_task import create_scoring_task
from tasks.decision_task import create_decision_task
from state import MetaLLMState, ModelCandidate, ScoredModel, ModelRecommendation


def _extract_json(text: str) -> str:
    """Extract JSON from agent output, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if match:
        return match.group(1).strip()
    # Try to find raw JSON array or object
    for pattern in [r"(\[[\s\S]*\])", r"(\{[\s\S]*\})"]:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return text.strip()


def _safe_parse_json(text: str, fallback: str = "{}") -> Union[Dict, List]:
    """Safely parse JSON from agent output."""
    raw = _extract_json(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try fixing common issues: trailing commas
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return json.loads(fallback)


def _build_llm() -> LLM:
    """Build a CrewAI LLM instance with the configured model and API key."""
    model = os.getenv("CREW_MODEL", "gemini/gemini-2.5-flash")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    return LLM(model=model, api_key=gemini_key)


def _run_crew(crew: Crew, retries: int = 3) -> str:
    """Run a Crew with exponential backoff on 429 rate-limit errors."""
    for attempt in range(retries):
        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                # Parse retry delay from the error message if present
                delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err, re.IGNORECASE)
                wait = float(delay_match.group(1)) if delay_match else (30 * (attempt + 1))
                logging.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{retries}). "
                    f"Waiting {wait:.0f}s before retry..."
                )
                if attempt < retries - 1:
                    time.sleep(wait)
                    continue
            raise
    return ""


def run_pipeline(user_prompt: str) -> MetaLLMState:
    """Run the full 4-agent pipeline and return populated MetaLLMState."""

    llm = _build_llm()
    state = MetaLLMState(raw_prompt=user_prompt)

    # ── Agent 1: Intake ──
    intake_agent = create_intake_agent(llm)
    intake_task = create_intake_task(intake_agent, user_prompt)

    intake_crew = Crew(
        agents=[intake_agent],
        tasks=[intake_task],
        process=Process.sequential,
        verbose=True,
    )
    intake_text = _run_crew(intake_crew)

    # Parse intake output into state
    parsed_intake = _safe_parse_json(intake_text)
    if isinstance(parsed_intake, dict):
        for field in [
            "task_type", "use_case_detail", "context_window_needed",
            "latency_requirement", "budget_tier", "scale", "output_format",
        ]:
            if field in parsed_intake:
                setattr(state, field, parsed_intake[field])
        if "tool_calling_needed" in parsed_intake:
            state.tool_calling_needed = bool(parsed_intake["tool_calling_needed"])

    # ── Agent 2: Research ──
    research_agent = create_research_agent(llm)
    research_task = create_research_task(research_agent, intake_text)

    research_crew = Crew(
        agents=[research_agent],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True,
    )
    research_text = _run_crew(research_crew)

    # Parse research output into state
    parsed_research = _safe_parse_json(research_text, fallback="[]")
    if isinstance(parsed_research, list):
        for model_data in parsed_research:
            if isinstance(model_data, dict):
                try:
                    state.candidate_models.append(ModelCandidate(**model_data))
                except Exception:
                    # Skip malformed entries
                    pass

    # ── Agent 3: Scoring ──
    scoring_agent = create_scoring_agent(llm)
    scoring_task = create_scoring_task(scoring_agent, intake_text, research_text)

    scoring_crew = Crew(
        agents=[scoring_agent],
        tasks=[scoring_task],
        process=Process.sequential,
        verbose=True,
    )
    scoring_text = _run_crew(scoring_crew)

    # Parse scoring output into state
    parsed_scoring = _safe_parse_json(scoring_text, fallback="[]")
    if isinstance(parsed_scoring, list):
        for model_data in parsed_scoring:
            if isinstance(model_data, dict):
                try:
                    state.scored_candidates.append(ScoredModel(**model_data))
                except Exception:
                    pass

    # ── Agent 4: Decision ──
    decision_agent = create_decision_agent(llm)
    decision_task = create_decision_task(decision_agent, intake_text, scoring_text)

    decision_crew = Crew(
        agents=[decision_agent],
        tasks=[decision_task],
        process=Process.sequential,
        verbose=True,
    )
    decision_text = _run_crew(decision_crew)

    # Parse decision output into state
    parsed_decisions = _safe_parse_json(decision_text, fallback="[]")
    if isinstance(parsed_decisions, list):
        for rec_data in parsed_decisions:
            if isinstance(rec_data, dict):
                try:
                    state.recommendations.append(ModelRecommendation(**rec_data))
                except Exception:
                    pass

    return state
