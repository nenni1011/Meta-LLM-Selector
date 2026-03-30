"""Task definition for Agent 1: Intake & Classification."""

from crewai import Task, Agent


def create_intake_task(agent: Agent, user_prompt: str) -> Task:
    return Task(
        description=(
            f"Analyze the following user requirement and extract structured parameters.\n\n"
            f"## User Requirement\n{user_prompt}\n\n"
            f"## Instructions\n"
            f"From the user's requirement above, determine:\n"
            f"1. **task_type**: One of: coding, writing, analysis, chat, agentic, multimodal, general\n"
            f"2. **use_case_detail**: A clear 1-2 sentence summary of what the user wants to do\n"
            f"3. **context_window_needed**: One of: small (<8k tokens), medium (8-32k), large (32-128k), very_large (>128k)\n"
            f"4. **latency_requirement**: One of: realtime (chat/streaming), interactive (a few seconds ok), batch (minutes ok)\n"
            f"5. **tool_calling_needed**: true/false — does the use case involve function calling, API integration, or agent tool use?\n"
            f"6. **budget_tier**: One of: free, low (<$1/M tokens), medium ($1-10/M), high ($10-30/M), no_limit\n"
            f"7. **scale**: One of: personal, startup, enterprise\n"
            f"8. **output_format**: One of: text, code, json, mixed\n\n"
            f"If any parameter is not mentioned, infer the most reasonable default based on context.\n"
        ),
        expected_output=(
            "Return a valid JSON object with exactly these keys:\n"
            "{\n"
            '  "task_type": "...",\n'
            '  "use_case_detail": "...",\n'
            '  "context_window_needed": "...",\n'
            '  "latency_requirement": "...",\n'
            '  "tool_calling_needed": true/false,\n'
            '  "budget_tier": "...",\n'
            '  "scale": "...",\n'
            '  "output_format": "..."\n'
            "}\n"
            "Return ONLY the JSON, no additional text."
        ),
        agent=agent,
    )
