"""Task definition for Agent 2: Research via Exa."""

from crewai import Task, Agent


def create_research_task(agent: Agent, intake_output: str) -> Task:
    return Task(
        description=(
            f"Research the current LLM market to find candidate models for the user's use case.\n\n"
            f"## Parsed Requirements\n{intake_output}\n\n"
            f"## Instructions\n"
            f"1. Use the **exa_benchmark_search** tool to search artificialanalysis.ai for:\n"
            f"   - Latest LLM benchmark comparisons (MMLU, HumanEval, coding benchmarks)\n"
            f"   - Performance metrics (speed, throughput, latency)\n"
            f"   - Quality rankings across providers\n\n"
            f"2. Use the **exa_pricing_search** tool to find:\n"
            f"   - Current API pricing for major LLM providers\n"
            f"   - Cost per million tokens (input and output separately)\n"
            f"   - Free tier availability\n\n"
            f"3. Use the **exa_search** tool for:\n"
            f"   - Model capability details (tool calling, context window, multimodal)\n"
            f"   - Recent model releases or updates\n\n"
            f"Research at least these providers: OpenAI, Anthropic, Google, Meta/Llama, "
            f"Mistral, DeepSeek, Cohere. Include 8-12 models.\n"
        ),
        expected_output=(
            "Return a valid JSON array of model candidates. Each object must have:\n"
            "[\n"
            "  {\n"
            '    "name": "Model Name",\n'
            '    "provider": "Provider",\n'
            '    "input_cost_per_million": 0.0 or null,\n'
            '    "output_cost_per_million": 0.0 or null,\n'
            '    "context_window": 128000 or null,\n'
            '    "latency_ms": 500 or null,\n'
            '    "throughput_tps": 100 or null,\n'
            '    "mmlu_score": 88.0 or null,\n'
            '    "humaneval_score": 90.0 or null,\n'
            '    "coding_score": 85.0 or null,\n'
            '    "tool_calling": true/false or null,\n'
            '    "multimodal": true/false,\n'
            '    "source_url": "https://...",\n'
            '    "notes": "Any relevant notes"\n'
            "  }\n"
            "]\n"
            "Return ONLY the JSON array, no additional text. Use null for unknown values."
        ),
        agent=agent,
    )
