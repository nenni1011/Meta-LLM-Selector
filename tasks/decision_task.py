"""Task definition for Agent 4: Final Decision & Recommendation."""

from crewai import Task, Agent


def create_decision_task(agent: Agent, intake_output: str, scoring_output: str) -> Task:
    return Task(
        description=(
            f"Make the final LLM selection — pick exactly 3 models for the user.\n\n"
            f"## User Requirements\n{intake_output}\n\n"
            f"## Scored Candidates\n{scoring_output}\n\n"
            f"## Instructions\n"
            f"From the scored candidates above, select exactly 3 models:\n\n"
            f"1. **Budget Pick** (tier: 'budget')\n"
            f"   - The most cost-efficient model that still adequately meets the requirements\n"
            f"   - Prioritize free-tier models or lowest cost options\n"
            f"   - Must still be functional for the use case\n\n"
            f"2. **Balanced Pick** (tier: 'balanced')\n"
            f"   - The best balance of cost, performance, and speed\n"
            f"   - Should be the model you'd recommend if they asked 'what should I use?'\n"
            f"   - Usually has the highest overall_score\n\n"
            f"3. **Premium Pick** (tier: 'premium')\n"
            f"   - The absolute best quality model regardless of cost\n"
            f"   - Highest benchmark scores and best capabilities\n"
            f"   - For users who need the very best output quality\n\n"
            f"For each pick, write a **specific** 2-3 sentence justification:\n"
            f"- Reference actual benchmark scores, pricing, and capabilities\n"
            f"- Explain why THIS model for THIS use case\n"
            f"- Mention concrete trade-offs compared to other tiers\n\n"
            f"Assign a speed_label to each: 'fast', 'medium', or 'slow' based on latency data.\n"
        ),
        expected_output=(
            "Return a valid JSON array with exactly 3 recommendations:\n"
            "[\n"
            "  {\n"
            '    "tier": "budget",\n'
            '    "model_name": "Model Name",\n'
            '    "provider": "Provider",\n'
            '    "input_cost_per_million": 0.0,\n'
            '    "output_cost_per_million": 0.0,\n'
            '    "context_window": 128000,\n'
            '    "speed_label": "fast|medium|slow",\n'
            '    "justification": "2-3 sentences explaining why this model..."\n'
            "  },\n"
            '  { "tier": "balanced", ... },\n'
            '  { "tier": "premium", ... }\n'
            "]\n"
            "Return ONLY the JSON array, no additional text."
        ),
        agent=agent,
    )
