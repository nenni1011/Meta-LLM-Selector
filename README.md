# 🤖 Meta-LLM-Selector

> **Find the best LLM for your use case — powered by a multi-agent AI pipeline.**

Meta-LLM-Selector is a tool that analyzes your requirements and recommends the **3 best LLM models** for your needs — available as both a **terminal CLI** and a **web UI**:

| Tier | What You Get |
|------|-------------|
| 💰 **Budget** | Most cost-efficient model that still meets your requirements |
| ⚖️ **Balanced** | Optimal balance of cost, performance, and speed |
| 🏆 **Premium** | Absolute best quality, regardless of cost |

Each recommendation includes a data-backed justification explaining *why* that model fits your specific use case.

---

## 🏗️ Architecture

```
User Terminal Input
        │
        ▼
┌─────────────────────────────┐
│  Agent 1: Intake Agent      │  ← Interactive Q&A / Freeform parsing
│  (Requirement Classifier)   │     Extracts: task type, budget, scale...
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Agent 2: Research Agent    │  ← Exa web search on:
│  (Benchmarks + Pricing)     │     • artificialanalysis.ai (benchmarks)
│                             │     • Provider pricing pages
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Agent 3: Scoring Agent     │  ← Weighted multi-criteria scoring
│  (Filter + Rank)            │     Cost × Performance × Speed × Fit
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Agent 4: Decision Agent    │  ← Final 3 picks with justifications
│  (Recommend)                │     Budget / Balanced / Premium
└──────────────┬──────────────┘
               │
               ▼
     Rich Terminal Output (3 cards)
```

**Tech Stack:**

| Component | Technology |
|-----------|-----------|
| Multi-agent framework | [CrewAI](https://github.com/crewAIInc/crewAI) |
| LLM backbone | Google Gemma 3 27B (via Google AI Studio / `gemini/` LiteLLM prefix) |
| Web search | [Exa](https://exa.ai) (semantic search API) |
| Benchmark data | [Artificial Analysis](https://artificialanalysis.ai/models) |
| Terminal UI | [Rich](https://github.com/Textualize/rich) |
| Web UI | [FastAPI](https://fastapi.tiangolo.com) + SSE streaming |
| State validation | [Pydantic v2](https://docs.pydantic.dev) |

---

## 📋 Prerequisites

- **Python 3.10+** (3.11 recommended — can be auto-installed with `uv`)
- A **Google Gemini API key** (free tier available)
- An **Exa API key** (free tier: 1000 searches/month)

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Meta-LLM-Selector.git
cd Meta-LLM-Selector
```

### 2. Create a virtual environment

```bash
# Option A: Using uv (recommended — auto-downloads Python 3.11)
pip install uv
uv python install 3.11
uv venv --python 3.11 .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Option B: Using standard venv (requires Python 3.10+ installed)
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `crewai[tools,google-genai]` installs the native Google Gen AI SDK required for Gemini models. Do **not** use the legacy `google-generativeai` package — it is a different library.

### 4. Set up API keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GEMINI_API_KEY=your_actual_gemini_key
EXA_API_KEY=your_actual_exa_key
```

### 5. Run Meta-LLM-Selector

**Option A: Terminal CLI**
```bash
python main.py
```

**Option B: Web UI**
```bash
python -m uvicorn web.app:app --reload
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🔑 How to Get API Keys

### Google Gemini API Key (Free)

1. Go to **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key and paste it in your `.env` file as `GEMINI_API_KEY`

> **Free tier:** 15 RPM, 1M tokens/min, 1500 requests/day — more than enough for this tool.

### Exa Search API Key (Free Tier)

1. Go to **[Exa Dashboard](https://dashboard.exa.ai/api-keys)**
2. Sign up for a free account
3. Navigate to **API Keys** section
4. Click **"Create new API key"**
5. Copy the key and paste it in your `.env` file as `EXA_API_KEY`

> **Free tier:** 1000 searches/month — each run uses ~3-5 searches.

---

## 🎯 Usage

### Guided Mode (Recommended)

The tool walks you through step-by-step questions:

```
▸ What is your primary task?
  e.g., coding assistant, content writing, data analysis, chatbot

▸ Describe your use case in a bit more detail
  e.g., Building a customer support bot for my SaaS product

▸ What's the scale of your project?
  personal project / startup product / enterprise deployment

▸ What's your budget sensitivity?
  free-tier only / low / medium / high / no limit

▸ What latency do you need?
  real-time / interactive / batch

▸ How much context do you need to process?
  short / medium / large / very large

▸ Do you need function/tool calling?
  yes / no / not sure

▸ Any other requirements?
  (optional)
```

### Freeform Mode

Paste your requirement directly:

```
I'm building a code review bot for my startup. It needs to analyze
entire pull requests (sometimes 50+ files), suggest improvements,
and integrate with our CI pipeline via function calling. Budget is
moderate — under $5/M tokens. Speed matters, ideally under 2 seconds
for initial response.
```

### Example Output

```
╭── 💰  BUDGET PICK — Cost Efficient ─────────────────────╮
│                                                          │
│  Gemini 2.0 Flash  by Google                             │
│                                                          │
│  Cost: $0.10/M input | $0.40/M output                   │
│  Context: 1M tokens  │  Speed: fast                      │
│                                                          │
│  Best free-tier throughput for code review. Its 1M        │
│  context window handles even the largest PRs easily.      │
│  Supports function calling for CI integration.            │
│                                                          │
╰──────────────────────────────────────────────────────────╯

╭── ⚖️  BALANCED PICK — Best Value ───────────────────────╮
│                                                          │
│  Claude 3.5 Sonnet  by Anthropic                         │
│                                                          │
│  Cost: $3.00/M input | $15.00/M output                   │
│  Context: 200K tokens  │  Speed: medium                   │
│                                                          │
│  Top-tier coding benchmarks (HumanEval 92%) at moderate   │
│  cost. 200K context handles large PRs. Strong tool        │
│  calling support for CI/CD integration pipelines.         │
│                                                          │
╰──────────────────────────────────────────────────────────╯

╭── 🏆  PREMIUM PICK — Top Quality ───────────────────────╮
│                                                          │
│  GPT-4o  by OpenAI                                       │
│                                                          │
│  Cost: $2.50/M input | $10.00/M output                   │
│  Context: 128K tokens  │  Speed: medium                   │
│                                                          │
│  Highest overall benchmark scores. Best structured JSON   │
│  output and function calling reliability. Worth the       │
│  premium for production code review at scale.             │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

---

## 🌐 Web UI

The web UI provides the same 4-agent pipeline as the CLI, with a dark AI-themed interface inspired by Apple and Nothing aesthetics.

### Features

- **Guided mode** — step-by-step questionnaire (8 questions, one at a time)
- **Freeform mode** — describe your use case in plain text
- **Real-time streaming** — watch agents think via Server-Sent Events
- **Pipeline visualizer** — 4-stage progress indicator with live status
- **Terminal output** — agent reasoning displayed in a terminal-style panel
- **Glassmorphism cards** — Budget / Balanced / Premium recommendation cards
- **Responsive** — works on desktop, tablet, and mobile

### Running the Web UI

```bash
source .venv/bin/activate
python -m uvicorn web.app:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the web UI |
| `GET` | `/api/health` | API health check + key status |
| `POST` | `/api/analyze` | Starts pipeline, returns SSE stream |

---

## 📁 Project Structure

```
Meta-LLM-Selector/
├── main.py                      # CLI entry point (Rich-powered interactive UI)
├── crew.py                      # CrewAI pipeline orchestrator (CLI + web)
├── state.py                     # Pydantic state models
│
├── agents/
│   ├── intake_agent.py          # Agent 1: Requirement parsing & classification
│   ├── research_agent.py        # Agent 2: Exa-powered benchmark/pricing research
│   ├── scoring_agent.py         # Agent 3: Multi-criteria scoring & ranking
│   └── decision_agent.py        # Agent 4: Final recommendation & justification
│
├── tasks/
│   ├── intake_task.py           # Task definition for Agent 1
│   ├── research_task.py         # Task definition for Agent 2
│   ├── scoring_task.py          # Task definition for Agent 3
│   └── decision_task.py         # Task definition for Agent 4
│
├── tools/
│   ├── exa_tool.py              # Exa search tools (benchmark, pricing, general)
│   └── __init__.py
│
├── web/                         # Web UI (FastAPI + SSE streaming)
│   ├── __init__.py
│   ├── app.py                   # FastAPI server with SSE streaming endpoint
│   └── static/
│       ├── index.html           # Single-page app (dark AI theme)
│       ├── style.css            # Apple+Nothing inspired dark theme
│       └── app.js               # Frontend logic (guided/freeform, SSE client)
│
├── tests/
│   ├── test_meta_llm.py         # Core pipeline tests (20 tests)
│   └── test_web.py              # Web API tests (9 tests)
│
├── .env.example                 # API key template
├── .env                         # Your API keys (git-ignored)
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
└── README.md                    # This file
```

---

## 🧪 Running Tests

```bash
# All tests (29 total: 20 core + 9 web)
pytest tests/ -v

# Just core pipeline tests
pytest tests/test_meta_llm.py -v

# Just web API tests
pytest tests/test_web.py -v
```

---

## 🔧 Troubleshooting

### `Google Gen AI native provider not available`

**Cause:** The `google-genai` package (new Google GenAI SDK) is missing. This is different from the legacy `google-generativeai` package.

**Fix:**
```bash
pip install "google-genai"
# or reinstall all requirements
pip install -r requirements.txt
```

### `429 RESOURCE_EXHAUSTED — limit: 0`

**Cause:** This is a **regional free-tier restriction**, not a usage overrun. Certain Gemini models (e.g. `gemini-2.0-flash`) have a `limit: 0` free tier in some regions (common outside the US). The pipeline will automatically retry with backoff on transient 429s, but `limit: 0` means the model is not available for free in your region.

**Fix:** Switch to `gemini-2.5-flash` (the default) which has broader free-tier coverage:
```env
# In your .env file
CREW_MODEL=gemini/gemini-2.5-flash
```

If you still get 429s, try the lighter model:
```env
CREW_MODEL=gemini/gemini-2.5-flash-lite
```

To find which models work with your key:
```bash
source .venv/bin/activate
python -c "
from dotenv import load_dotenv; load_dotenv()
from google import genai; import os
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
for m in client.models.list():
    print(m.name)
"
```

### `EXA_API_KEY is not set`
Ensure you copied `.env.example` to `.env` and filled in your key:
```bash
cp .env.example .env
# then edit .env and add your keys
```

### Pipeline returns no recommendations
This usually means the Exa search returned empty results or the model output couldn't be parsed. Check:
1. Your `EXA_API_KEY` is valid
2. You have remaining Exa API quota (free tier: 1000/month)
3. Your `CREW_MODEL` is set to a working model (see 429 fix above)

---

## ⚙️ Configuration

All configuration is done via `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `EXA_API_KEY` | Yes | — | Exa search API key |
| `CREW_MODEL` | No | `gemini/gemma-3-27b-it` | LLM model for CrewAI agents |
| `CREWAI_TRACING_ENABLED` | No | `false` | Disable CrewAI tracing prompts |

### Supported LLM Models

You can change `CREW_MODEL` to any LiteLLM-compatible model:

```env
# Google Gemma via Google AI Studio (recommended — same API key, free tier)
CREW_MODEL=gemini/gemma-3-27b-it       # default — best Gemma for reasoning + JSON
CREW_MODEL=gemini/gemma-3-12b-it       # faster, slightly less capable

# Google Gemini (also supported)
CREW_MODEL=gemini/gemini-2.5-flash     # previous default
CREW_MODEL=gemini/gemini-2.5-flash-lite  # fastest / cheapest

# OpenAI
CREW_MODEL=gpt-4o

# Anthropic
CREW_MODEL=anthropic/claude-3-5-sonnet-20241022
```

> **Why Gemma 3 27B?** It's the largest instruction-tuned Gemma model available on the free tier. The pipeline requires structured JSON output at every stage and multi-step reasoning over web search results — capabilities where 27B outperforms smaller Gemma variants. It uses the same `GEMINI_API_KEY` (served via Google AI Studio).

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [CrewAI](https://github.com/crewAIInc/crewAI) — Multi-agent orchestration framework
- [Exa](https://exa.ai) — Semantic web search API
- [Artificial Analysis](https://artificialanalysis.ai) — LLM benchmark data
- [Rich](https://github.com/Textualize/rich) — Beautiful terminal output
- [Google Gemini](https://ai.google.dev) — LLM backbone
