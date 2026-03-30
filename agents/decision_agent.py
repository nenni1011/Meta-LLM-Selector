"""Agent 4: Decision Agent — Produces final 3 ranked recommendations with justifications."""

from crewai import Agent, LLM


def create_decision_agent(llm: LLM) -> Agent:
    return Agent(
        role="AI Strategy Advisor & Final Decision Maker",
        goal=(
            "Review all scored candidates and select exactly 3 final recommendations:\n"
            "1. **Budget Pick** — Best cost-efficient option (cheapest that still meets requirements)\n"
            "2. **Balanced Pick** — Best value (optimal balance of cost, performance, and speed)\n"
            "3. **Premium Pick** — Best overall quality (top benchmarks, regardless of cost)\n\n"
            "For each pick, write a clear 2-3 sentence justification explaining WHY this specific "
            "model was chosen for this specific use case. Reference concrete data points "
            "(benchmark scores, pricing, context window, speed) in your justification."
        ),
        backstory=(
            "You are a chief AI officer who has deployed LLMs at scale across dozens of companies. "
            "You understand the trade-offs between cost, performance, and speed intimately. "
            "Your recommendations are always backed by data and tailored to the specific use case. "
            "You communicate clearly and concisely."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
