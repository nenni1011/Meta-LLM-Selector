"""Agent 2: Research Agent — Fetches live benchmark, pricing, and capability data via Exa."""

from crewai import Agent, LLM

from tools.exa_tool import ExaBenchmarkTool, ExaPricingTool, ExaSearchTool


def create_research_agent(llm: LLM) -> Agent:
    return Agent(
        role="LLM Market Researcher",
        goal=(
            "Research the current LLM landscape using live web data. For the given use case, "
            "find relevant benchmarks (MMLU, HumanEval, coding scores), pricing information "
            "(cost per million tokens), context window sizes, speed metrics (latency and throughput), "
            "and capability data (tool calling, multimodal support). "
            "Focus on models from major providers: OpenAI, Anthropic, Google, Meta, Mistral, "
            "DeepSeek, Cohere, and others. Return at least 8-12 candidate models with as much "
            "structured data as possible."
        ),
        backstory=(
            "You are an expert AI market analyst who tracks every LLM release, benchmark update, "
            "and pricing change. You use Exa search to query artificialanalysis.ai for benchmarks, "
            "provider pricing pages for costs, and model documentation for capabilities. "
            "You are meticulous about separating verified data from speculation."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[ExaSearchTool(), ExaBenchmarkTool(), ExaPricingTool()],
    )
