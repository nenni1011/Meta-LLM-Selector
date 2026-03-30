#!/usr/bin/env python3
"""Meta-LLM-Selector — Terminal-based AI agent to find the best LLM for your use case."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich import box

from state import MetaLLMState, ModelRecommendation

console = Console()


# ─── Guided prompts to help users provide detailed input ───

GUIDED_QUESTIONS: list = [
    {
        "key": "primary_task",
        "question": "What is your primary task?",
        "hint": "e.g., coding assistant, content writing, data analysis, chatbot, agentic workflows, multimodal (image+text)",
    },
    {
        "key": "detail",
        "question": "Describe your use case in a bit more detail",
        "hint": "e.g., I'm building a customer support bot that needs to handle product FAQs and process returns",
    },
    {
        "key": "scale",
        "question": "What's the scale of your project?",
        "hint": "personal project / startup product / enterprise deployment",
    },
    {
        "key": "budget",
        "question": "What's your budget sensitivity?",
        "hint": "free-tier only / low (<$1/M tokens) / medium ($1-10/M) / high ($10-30/M) / no limit",
    },
    {
        "key": "latency",
        "question": "What latency do you need?",
        "hint": "real-time (chat/streaming) / interactive (few seconds ok) / batch (minutes ok)",
    },
    {
        "key": "context",
        "question": "How much context do you need to process?",
        "hint": "short (<8K tokens ~4 pages) / medium (8-32K) / large (32-128K) / very large (>128K, entire codebases/books)",
    },
    {
        "key": "tool_calling",
        "question": "Do you need function/tool calling or API integration?",
        "hint": "yes / no / not sure",
    },
    {
        "key": "extra",
        "question": "Any other requirements?",
        "hint": "e.g., must support JSON mode, needs vision, must run locally, etc. (press Enter to skip)",
    },
]


def display_banner() -> None:
    """Display the application banner."""
    banner = Text()
    banner.append("╔══════════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║          ", style="bold cyan")
    banner.append("META-LLM-SELECTOR", style="bold white on blue")
    banner.append("               ║\n", style="bold cyan")
    banner.append("║    ", style="bold cyan")
    banner.append("Find the Best LLM for Your Use Case", style="italic white")
    banner.append("     ║\n", style="bold cyan")
    banner.append("╚══════════════════════════════════════════════╝", style="bold cyan")
    console.print(banner)
    console.print()


def validate_api_keys() -> bool:
    """Check that required API keys are set."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    exa_key = os.getenv("EXA_API_KEY", "")

    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        console.print(
            Panel(
                "[bold red]GEMINI_API_KEY is not configured![/bold red]\n\n"
                "1. Get your key at: [link=https://aistudio.google.com/apikey]https://aistudio.google.com/apikey[/link]\n"
                "2. Add it to your .env file:\n"
                "   [dim]GEMINI_API_KEY=your_actual_key_here[/dim]",
                title="Missing API Key",
                border_style="red",
            )
        )
        return False

    if not exa_key or exa_key == "your_exa_api_key_here":
        console.print(
            Panel(
                "[bold red]EXA_API_KEY is not configured![/bold red]\n\n"
                "1. Get your key at: [link=https://dashboard.exa.ai/api-keys]https://dashboard.exa.ai/api-keys[/link]\n"
                "2. Add it to your .env file:\n"
                "   [dim]EXA_API_KEY=your_actual_key_here[/dim]",
                title="Missing API Key",
                border_style="red",
            )
        )
        return False

    return True


def get_input_mode() -> str:
    """Ask user whether they want guided or freeform input."""
    console.print(
        Panel(
            "[bold]How would you like to describe your use case?[/bold]\n\n"
            "  [cyan]1[/cyan] — Guided mode (we'll ask you questions step by step)\n"
            "  [cyan]2[/cyan] — Freeform mode (paste or type your requirement directly)",
            border_style="blue",
        )
    )
    choice = Prompt.ask("Choose mode", choices=["1", "2"], default="1")
    return "guided" if choice == "1" else "freeform"


def collect_guided_input() -> str:
    """Walk the user through guided questions and build a requirement prompt."""
    console.print()
    console.print(
        Panel(
            "[bold green]Let's understand your use case![/bold green]\n"
            "[dim]Answer each question below. The more detail, the better the recommendations.[/dim]",
            border_style="green",
        )
    )
    console.print()

    answers = {}
    for q in GUIDED_QUESTIONS:
        console.print(f"  [bold cyan]▸ {q['question']}[/bold cyan]")
        console.print(f"    [dim]{q['hint']}[/dim]")
        answer = Prompt.ask("   ")
        if answer.strip():
            answers[q["key"]] = answer.strip()
        console.print()

    # Build a structured prompt from answers
    parts = []
    if "primary_task" in answers:
        parts.append(f"Primary task: {answers['primary_task']}")
    if "detail" in answers:
        parts.append(f"Use case details: {answers['detail']}")
    if "scale" in answers:
        parts.append(f"Scale: {answers['scale']}")
    if "budget" in answers:
        parts.append(f"Budget: {answers['budget']}")
    if "latency" in answers:
        parts.append(f"Latency requirement: {answers['latency']}")
    if "context" in answers:
        parts.append(f"Context window needs: {answers['context']}")
    if "tool_calling" in answers:
        parts.append(f"Tool/function calling: {answers['tool_calling']}")
    if "extra" in answers:
        parts.append(f"Additional requirements: {answers['extra']}")

    return "\n".join(parts)


def collect_freeform_input() -> str:
    """Let the user type or paste their requirement freely."""
    console.print()
    console.print(
        Panel(
            "[bold green]Describe your use case[/bold green]\n"
            "[dim]Include as much detail as you can: what you're building, "
            "scale, budget, latency needs, etc.[/dim]",
            border_style="green",
        )
    )
    console.print()
    user_input = Prompt.ask("  [bold cyan]Your requirement[/bold cyan]")
    return user_input.strip()


def display_recommendations(state: MetaLLMState) -> None:
    """Display the final 3 recommendations as styled terminal cards."""
    console.print()
    console.print(
        Panel(
            "[bold white]RECOMMENDATIONS[/bold white]",
            style="bold blue",
            expand=False,
        )
    )
    console.print()

    tier_styles = {
        "budget": {"border": "green", "emoji": "💰", "label": "BUDGET PICK — Cost Efficient"},
        "balanced": {"border": "yellow", "emoji": "⚖️", "label": "BALANCED PICK — Best Value"},
        "premium": {"border": "red", "emoji": "🏆", "label": "PREMIUM PICK — Top Quality"},
    }

    for rec in state.recommendations:
        style = tier_styles.get(rec.tier, tier_styles["balanced"])

        # Build cost string
        cost_parts = []
        if rec.input_cost_per_million is not None:
            cost_parts.append(f"${rec.input_cost_per_million:.2f}/M input")
        if rec.output_cost_per_million is not None:
            cost_parts.append(f"${rec.output_cost_per_million:.2f}/M output")
        cost_str = " | ".join(cost_parts) if cost_parts else "Pricing varies"

        # Build context string
        ctx_str = ""
        if rec.context_window:
            if rec.context_window >= 1_000_000:
                ctx_str = f"{rec.context_window / 1_000_000:.1f}M tokens"
            else:
                ctx_str = f"{rec.context_window // 1_000}K tokens"

        # Build the card content
        lines = [
            f"[bold white]{rec.model_name}[/bold white]  [dim]by {rec.provider}[/dim]",
            "",
        ]
        info_parts = []
        if cost_str:
            info_parts.append(f"[green]Cost:[/green] {cost_str}")
        if ctx_str:
            info_parts.append(f"[blue]Context:[/blue] {ctx_str}")
        if rec.speed_label:
            speed_color = {"fast": "green", "medium": "yellow", "slow": "red"}.get(rec.speed_label, "white")
            info_parts.append(f"[{speed_color}]Speed:[/{speed_color}] {rec.speed_label}")

        lines.append("  │  ".join(info_parts))
        lines.append("")
        lines.append(f"[italic]{rec.justification}[/italic]")

        console.print(
            Panel(
                "\n".join(lines),
                title=f"{style['emoji']}  {style['label']}",
                border_style=style["border"],
                padding=(1, 2),
            )
        )
        console.print()

    # Summary table
    if state.scored_candidates:
        console.print(
            Panel("[bold]Full Scored Candidates[/bold]", style="dim", expand=False)
        )
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Model", min_width=20)
        table.add_column("Provider", min_width=10)
        table.add_column("Tier", min_width=10)
        table.add_column("Overall", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Perf", justify="right")
        table.add_column("Speed", justify="right")
        table.add_column("Fit", justify="right")

        for m in sorted(state.scored_candidates, key=lambda x: x.overall_score, reverse=True):
            tier_color = {"budget": "green", "balanced": "yellow", "premium": "red"}.get(m.tier, "white")
            table.add_row(
                m.name,
                m.provider,
                f"[{tier_color}]{m.tier}[/{tier_color}]",
                f"{m.overall_score:.1f}",
                f"{m.cost_score:.1f}",
                f"{m.performance_score:.1f}",
                f"{m.speed_score:.1f}",
                f"{m.fit_score:.1f}",
            )
        console.print(table)
        console.print()


def display_fallback_output(state: MetaLLMState) -> None:
    """Display raw state if structured parsing failed."""
    console.print(
        Panel(
            "[yellow]Could not parse structured recommendations. Showing raw pipeline output.[/yellow]",
            border_style="yellow",
        )
    )
    console.print()
    console.print(f"[bold]Task Type:[/bold] {state.task_type}")
    console.print(f"[bold]Use Case:[/bold] {state.use_case_detail}")
    console.print(f"[bold]Candidates found:[/bold] {len(state.candidate_models)}")
    console.print(f"[bold]Scored models:[/bold] {len(state.scored_candidates)}")
    console.print(f"[bold]Recommendations:[/bold] {len(state.recommendations)}")

    if state.candidate_models:
        console.print("\n[bold cyan]Candidate Models:[/bold cyan]")
        for m in state.candidate_models:
            console.print(f"  • {m.name} ({m.provider}) — {m.notes[:80] if m.notes else 'No notes'}")

    if state.recommendations:
        console.print("\n[bold cyan]Recommendations:[/bold cyan]")
        for r in state.recommendations:
            console.print(f"  • [{r.tier}] {r.model_name}: {r.justification[:120]}")


def main() -> None:
    """Main entry point for the CLI application."""
    # Load environment variables
    load_dotenv()

    display_banner()

    # Validate API keys
    if not validate_api_keys():
        sys.exit(1)

    # Get input mode
    mode = get_input_mode()

    # Collect user requirements
    if mode == "guided":
        user_prompt = collect_guided_input()
    else:
        user_prompt = collect_freeform_input()

    if not user_prompt.strip():
        console.print("[red]No requirement provided. Exiting.[/red]")
        sys.exit(1)

    # Show what we're working with
    console.print()
    console.print(
        Panel(
            user_prompt,
            title="Your Requirement",
            border_style="blue",
        )
    )
    console.print()

    # Run the pipeline
    console.print(
        Panel(
            "[bold]Starting Meta-LLM analysis pipeline...[/bold]\n\n"
            "  [cyan]Agent 1:[/cyan] Analyzing your requirements\n"
            "  [cyan]Agent 2:[/cyan] Researching LLM benchmarks & pricing\n"
            "  [cyan]Agent 3:[/cyan] Scoring candidates against your needs\n"
            "  [cyan]Agent 4:[/cyan] Making final recommendations\n\n"
            "[dim]This may take 1-2 minutes depending on search results.[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    from crew import run_pipeline

    try:
        state = run_pipeline(user_prompt)
    except Exception as e:
        console.print(f"\n[bold red]Pipeline error:[/bold red] {e}")
        console.print("[dim]Check your API keys and network connection.[/dim]")
        sys.exit(1)

    # Display results
    if state.recommendations:
        display_recommendations(state)
    else:
        display_fallback_output(state)

    console.print(
        Panel(
            "[bold green]Analysis complete![/bold green] 🎉\n"
            "[dim]Tip: Run again with different requirements to compare recommendations.[/dim]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
