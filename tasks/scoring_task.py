"""Task definition for Agent 3: Scoring & Filtering."""

from crewai import Task, Agent


def create_scoring_task(agent: Agent, intake_output: str, research_output: str) -> Task:
    return Task(
        description=(
            f"Score and rank the researched LLM models against the user's requirements.\n\n"
            f"## User Requirements\n{intake_output}\n\n"
            f"## Candidate Models (from research)\n{research_output}\n\n"
            f"## Scoring Instructions\n"
            f"For each candidate model, compute scores on a 0-100 scale:\n\n"
            f"### 1. Cost Score (0-100)\n"
            f"- Free models: 100\n"
            f"- <$0.50/M input tokens: 85\n"
            f"- $0.50-$3/M: 65\n"
            f"- $3-$15/M: 40\n"
            f"- >$15/M: 20\n\n"
            f"### 2. Performance Score (0-100)\n"
            f"- Based on MMLU, HumanEval, coding_score as available\n"
            f"- If task_type is 'coding', weight HumanEval/coding_score 2x\n"
            f"- Normalize to 0-100 relative to the best model in the set\n\n"
            f"### 3. Speed Score (0-100)\n"
            f"- Based on latency_ms and throughput_tps\n"
            f"- Lower latency and higher throughput = higher score\n\n"
            f"### 4. Fit Score (0-100)\n"
            f"- Does the model match context_window_needed? (+25)\n"
            f"- Does it support tool_calling if needed? (+25)\n"
            f"- Is it multimodal if needed? (+25)\n"
            f"- Does the output format match? (+25)\n\n"
            f"### Weights (adjust based on requirements)\n"
            f"- If budget_tier is free/low: cost=40%, perf=25%, speed=15%, fit=20%\n"
            f"- If budget_tier is medium: cost=25%, perf=30%, speed=20%, fit=25%\n"
            f"- If budget_tier is high/no_limit: cost=10%, perf=40%, speed=20%, fit=30%\n"
            f"- If latency_requirement is realtime: increase speed weight by 15%\n\n"
            f"### Tier Assignment\n"
            f"- Sort by overall_score\n"
            f"- Top 3 by cost_score → potential 'budget' picks\n"
            f"- Top 3 by overall_score → potential 'balanced' picks\n"
            f"- Top 3 by performance_score → potential 'premium' picks\n"
        ),
        expected_output=(
            "Return a valid JSON array of scored models, sorted by overall_score descending:\n"
            "[\n"
            "  {\n"
            '    "name": "Model Name",\n'
            '    "provider": "Provider",\n'
            '    "tier": "budget|balanced|premium",\n'
            '    "overall_score": 82.5,\n'
            '    "cost_score": 90.0,\n'
            '    "performance_score": 75.0,\n'
            '    "speed_score": 80.0,\n'
            '    "fit_score": 85.0,\n'
            '    "input_cost_per_million": 0.5,\n'
            '    "output_cost_per_million": 1.5,\n'
            '    "context_window": 128000,\n'
            '    "latency_ms": 500,\n'
            '    "throughput_tps": 100\n'
            "  }\n"
            "]\n"
            "Return ONLY the JSON array. Include all models, not just top picks."
        ),
        agent=agent,
    )
