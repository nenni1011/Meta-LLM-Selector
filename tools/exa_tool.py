"""Exa search tool wrapped for CrewAI agents."""

from __future__ import annotations

import os
from typing import List, Optional

from crewai.tools import BaseTool
from exa_py import Exa
from exa_py.api import Result


def _get_exa_client() -> Exa:
    """Return a shared Exa client, raising a clear error if key is missing."""
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key or api_key == "your_exa_api_key_here":
        raise ValueError(
            "EXA_API_KEY is not set. Please add it to your .env file.\n"
            "Get a key at: https://dashboard.exa.ai/api-keys"
        )
    return Exa(api_key=api_key)


def _format_results(results: List[Result], max_text: int = 2000) -> str:
    """Format a list of Exa Result objects into a readable string."""
    if not results:
        return "No results found."
    parts: List[str] = []
    for r in results:
        text = (r.text or "")[:max_text]
        parts.append(f"### {r.title}\n**URL:** {r.url}\n{text}\n")
    return "\n---\n".join(parts)


class ExaSearchTool(BaseTool):
    """Searches the web using Exa's semantic search and returns text contents."""

    name: str = "exa_search"
    description: str = (
        "Search the web using Exa for LLM model benchmarks, pricing, "
        "and capabilities. Pass a natural language query. "
        "Returns relevant text snippets with source URLs."
    )

    def _run(self, query: str) -> str:
        client = _get_exa_client()
        response = client.search(
            query,
            type="auto",
            num_results=5,
            contents={"text": {"max_characters": 3000}},
        )
        return _format_results(response.results)


class ExaBenchmarkTool(BaseTool):
    """Targeted search on artificialanalysis.ai for LLM benchmarks."""

    name: str = "exa_benchmark_search"
    description: str = (
        "Search artificialanalysis.ai specifically for LLM model benchmarks, "
        "performance comparisons, pricing data, and speed metrics. "
        "Pass a query about model capabilities or comparison."
    )

    def _run(self, query: str) -> str:
        client = _get_exa_client()
        response = client.search(
            query,
            type="auto",
            num_results=5,
            include_domains=["artificialanalysis.ai"],
            contents={"text": {"max_characters": 4000}},
        )
        if not response.results:
            # Fallback: broader search without domain restriction
            response = client.search(
                f"LLM benchmark comparison {query}",
                type="auto",
                num_results=5,
                contents={"text": {"max_characters": 3000}},
            )
        return _format_results(response.results, max_text=3000)


class ExaPricingTool(BaseTool):
    """Targeted search for LLM pricing information."""

    name: str = "exa_pricing_search"
    description: str = (
        "Search the web for current LLM API pricing information. "
        "Targets pricing pages, cost comparison sites, and provider docs. "
        "Pass a query about model pricing or cost."
    )

    def _run(self, query: str) -> str:
        client = _get_exa_client()
        response = client.search(
            query,
            type="auto",
            num_results=5,
            include_domains=[
                "openrouter.ai",
                "artificialanalysis.ai",
                "together.ai",
                "openai.com",
                "anthropic.com",
                "cloud.google.com",
            ],
            contents={"text": {"max_characters": 3000}},
        )
        if not response.results:
            # Fallback: broader pricing search without domain restriction
            response = client.search(
                f"LLM API pricing cost per token {query}",
                type="auto",
                num_results=5,
                contents={"text": {"max_characters": 3000}},
            )
        return _format_results(response.results)
