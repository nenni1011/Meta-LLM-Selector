/* Meta-LLM Selector — Frontend Logic */
(function () {
  "use strict";

  // ── DOM refs ──
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const heroSection = $("#hero");
  const inputSection = $("#inputSection");
  const processingSection = $("#processingSection");
  const resultsSection = $("#resultsSection");
  const errorOverlay = $("#errorOverlay");

  const btnGetStarted = $("#btnGetStarted");
  const btnGuided = $("#btnGuided");
  const btnFreeform = $("#btnFreeform");
  const modeToggle = $(".mode-toggle");
  const guidedMode = $("#guidedMode");
  const freeformMode = $("#freeformMode");

  const btnPrev = $("#btnPrev");
  const btnNext = $("#btnNext");
  const stepperFill = $("#stepperFill");
  const stepperLabel = $("#stepperLabel");

  const freeformInput = $("#freeformInput");
  const charCount = $("#charCount");
  const btnAnalyze = $("#btnAnalyze");

  const terminalBody = $("#terminalBody");
  const recCardsContainer = $("#recCards");
  const scoredTableBody = $("#scoredTable tbody");
  const resultsSummary = $("#resultsSummary");
  const scoredTableWrap = $("#scoredTableWrap");

  const btnStartOver = $("#btnStartOver");
  const btnDismissError = $("#btnDismissError");
  const errorMessage = $("#errorMessage");
  const apiStatus = $("#apiStatus");

  // ── State ──
  let currentStep = 0;
  const totalSteps = 8;
  const guidedAnswers = {};

  const STAGE_NAMES = {
    1: "Analyzing Requirements",
    2: "Researching LLM Market",
    3: "Scoring & Ranking",
    4: "Making Recommendations",
  };

  const GUIDED_QUESTIONS = [
    { id: "q0", key: "primary_task", prefix: "Primary task: " },
    { id: "q1", key: "use_case", prefix: "Use case: " },
    { id: "q2", key: "context", prefix: "Context window: " },
    { id: "q3", key: "latency", prefix: "Latency: " },
    { id: "q4", key: "budget", prefix: "Budget: " },
    { id: "q5", key: "scale", prefix: "Scale: " },
    { id: "q6", key: "tool_calling", prefix: "Tool calling: " },
    { id: "q7", key: "output_format", prefix: "Output format: " },
  ];

  // ── Init ──
  function init() {
    checkHealth();
    bindEvents();
  }

  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data.gemini_configured && data.exa_configured) {
        apiStatus.textContent = "● APIs connected";
        apiStatus.className = "nav-status ok";
      } else {
        const missing = [];
        if (!data.gemini_configured) missing.push("Gemini");
        if (!data.exa_configured) missing.push("Exa");
        apiStatus.textContent = `● ${missing.join(", ")} not configured`;
        apiStatus.className = "nav-status error";
      }
    } catch {
      apiStatus.textContent = "● Offline";
      apiStatus.className = "nav-status error";
    }
  }

  // ── Events ──
  function bindEvents() {
    btnGetStarted.addEventListener("click", () => {
      inputSection.scrollIntoView({ behavior: "smooth" });
    });

    btnGuided.addEventListener("click", () => setMode("guided"));
    btnFreeform.addEventListener("click", () => setMode("freeform"));

    btnPrev.addEventListener("click", prevStep);
    btnNext.addEventListener("click", nextStep);

    // Chip selection
    document.addEventListener("click", (e) => {
      if (!e.target.classList.contains("chip")) return;
      const group = e.target.closest(".chip-group");
      group.querySelectorAll(".chip").forEach((c) => c.classList.remove("selected"));
      e.target.classList.add("selected");
    });

    // Enter key in text inputs navigates to next step
    $$(".stepper-question input").forEach((input) => {
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") nextStep();
      });
    });

    freeformInput.addEventListener("input", () => {
      charCount.textContent = `${freeformInput.value.length} chars`;
    });

    btnAnalyze.addEventListener("click", () => {
      if (freeformInput.value.trim().length < 10) {
        freeformInput.focus();
        return;
      }
      startAnalysis(freeformInput.value.trim());
    });

    btnStartOver.addEventListener("click", resetAll);
    btnDismissError.addEventListener("click", () => {
      errorOverlay.classList.add("hidden");
      resetAll();
    });
  }

  // ── Mode Toggle ──
  function setMode(mode) {
    if (mode === "guided") {
      btnGuided.classList.add("active");
      btnFreeform.classList.remove("active");
      guidedMode.classList.add("active");
      freeformMode.classList.remove("active");
      modeToggle.removeAttribute("data-active");
    } else {
      btnFreeform.classList.add("active");
      btnGuided.classList.remove("active");
      freeformMode.classList.add("active");
      guidedMode.classList.remove("active");
      modeToggle.setAttribute("data-active", "freeform");
    }
  }

  // ── Stepper ──
  function updateStepper() {
    const questions = $$(".stepper-question");
    questions.forEach((q, i) => {
      q.classList.toggle("active", i === currentStep);
    });
    stepperFill.style.width = `${((currentStep + 1) / totalSteps) * 100}%`;
    stepperLabel.textContent = `Step ${currentStep + 1} of ${totalSteps}`;
    btnPrev.disabled = currentStep === 0;
    btnNext.textContent = currentStep === totalSteps - 1 ? "Analyze →" : "Next →";
  }

  function getStepValue(step) {
    const q = GUIDED_QUESTIONS[step];
    const el = $(`#${q.id}`);
    if (el) return el.value.trim();
    const chipGroup = $(`.stepper-question[data-step="${step}"] .chip-group`);
    if (chipGroup) {
      const selected = chipGroup.querySelector(".chip.selected");
      return selected ? selected.dataset.value : "";
    }
    return "";
  }

  function nextStep() {
    // Save current step value
    const val = getStepValue(currentStep);
    if (currentStep <= 1 && !val) {
      const input = $(`#${GUIDED_QUESTIONS[currentStep].id}`);
      if (input) input.focus();
      return;
    }
    guidedAnswers[GUIDED_QUESTIONS[currentStep].key] = val;

    if (currentStep >= totalSteps - 1) {
      // Build prompt from guided answers
      const prompt = buildGuidedPrompt();
      startAnalysis(prompt);
      return;
    }
    currentStep++;
    updateStepper();
  }

  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
      updateStepper();
    }
  }

  function buildGuidedPrompt() {
    const parts = [];
    for (const q of GUIDED_QUESTIONS) {
      const v = guidedAnswers[q.key];
      if (v) parts.push(`${q.prefix}${v}`);
    }
    return parts.join(". ") + ".";
  }

  // ── Analysis ──
  async function startAnalysis(prompt) {
    showSection("processing");
    resetProcessing();
    addTerminalLine("Starting Meta-LLM analysis pipeline...");
    addTerminalLine(`Prompt: "${prompt.slice(0, 120)}${prompt.length > 120 ? "..." : ""}"`, true);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              handleEvent(event);
            } catch { /* skip malformed */ }
          }
        }
      }

      // Process remaining buffer
      if (buffer.startsWith("data: ")) {
        try {
          const event = JSON.parse(buffer.slice(6));
          handleEvent(event);
        } catch { /* skip */ }
      }
    } catch (err) {
      showError(err.message || "Failed to connect to the server.");
    }
  }

  function handleEvent(event) {
    switch (event.type) {
      case "stage":
        updateStage(event.stage, event.status, event.name);
        if (event.status === "running") {
          addTerminalLine(`Agent ${event.stage}: ${event.name || STAGE_NAMES[event.stage]} started...`);
        } else if (event.status === "done") {
          addTerminalLine(`Agent ${event.stage}: Complete ✓`, true);
        }
        break;

      case "thinking":
        updateStageOutput(event.stage, event.content);
        addTerminalLine(event.content);
        break;

      case "result":
        renderResults(event.data);
        break;

      case "error":
        showError(event.message);
        break;

      case "done":
        addTerminalLine("Pipeline complete.", true);
        break;
    }
  }

  // ── Processing UI ──
  function resetProcessing() {
    $$(".pipeline-stage").forEach((el) => {
      el.className = "pipeline-stage";
      el.querySelector(".stage-status").textContent = "Waiting";
      el.querySelector(".stage-output").textContent = "";
    });
    terminalBody.innerHTML = "";
  }

  function updateStage(stage, status, name) {
    const el = $(`.pipeline-stage[data-stage="${stage}"]`);
    if (!el) return;

    if (status === "running") {
      el.classList.add("running");
      el.classList.remove("done");
      el.querySelector(".stage-status").textContent = "Running...";
      if (name) el.querySelector(".stage-name").textContent = name;
    } else if (status === "done") {
      el.classList.remove("running");
      el.classList.add("done");
      el.querySelector(".stage-status").textContent = "Done ✓";
    }
  }

  function updateStageOutput(stage, content) {
    const el = $(`.pipeline-stage[data-stage="${stage}"] .stage-output`);
    if (el && content) {
      el.textContent = content;
    }
  }

  function addTerminalLine(text, highlight) {
    const line = document.createElement("div");
    line.className = "terminal-line";
    const prompt = document.createElement("span");
    prompt.className = "terminal-prompt";
    prompt.textContent = "▸";
    const textEl = document.createElement("span");
    textEl.className = "terminal-text" + (highlight ? " highlight" : "");
    textEl.textContent = text;
    line.appendChild(prompt);
    line.appendChild(textEl);
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  // ── Results ──
  function renderResults(data) {
    if (!data || !data.recommendations || data.recommendations.length === 0) {
      showError("No recommendations returned. The pipeline may have encountered an issue.");
      return;
    }

    resultsSummary.textContent = `Analyzed for: ${data.task_type || "your use case"} — ${data.budget_tier || "all budgets"}`;

    // Render cards
    recCardsContainer.innerHTML = "";
    const tierOrder = ["Budget", "Balanced", "Premium"];

    // Sort recommendations by tier order
    const sorted = [...data.recommendations].sort(
      (a, b) => tierOrder.indexOf(a.tier) - tierOrder.indexOf(b.tier)
    );

    sorted.forEach((rec, i) => {
      const card = document.createElement("div");
      const tierClass = rec.tier.toLowerCase().replace(/\s+/g, "-");
      card.className = `rec-card ${tierClass}`;
      card.innerHTML = `
        <span class="rec-tier">${escapeHtml(rec.tier)}</span>
        <div class="rec-model">${escapeHtml(rec.model_name)}</div>
        <div class="rec-provider">${escapeHtml(rec.provider)}</div>
        <div class="rec-stats">
          <div class="rec-stat">
            <span class="rec-stat-label">Input cost</span>
            <span class="rec-stat-value">$${formatNum(rec.input_cost_per_million)}/M</span>
          </div>
          <div class="rec-stat">
            <span class="rec-stat-label">Output cost</span>
            <span class="rec-stat-value">$${formatNum(rec.output_cost_per_million)}/M</span>
          </div>
          <div class="rec-stat">
            <span class="rec-stat-label">Context</span>
            <span class="rec-stat-value">${formatContext(rec.context_window)}</span>
          </div>
          <div class="rec-stat">
            <span class="rec-stat-label">Speed</span>
            <span class="rec-stat-value">${escapeHtml(rec.speed_label || "—")}</span>
          </div>
        </div>
        <div class="rec-justification">${escapeHtml(rec.justification)}</div>
      `;
      recCardsContainer.appendChild(card);

      // Staggered reveal
      setTimeout(() => card.classList.add("visible"), 150 * (i + 1));
    });

    // Render scored table
    scoredTableBody.innerHTML = "";
    if (data.scored_candidates && data.scored_candidates.length > 0) {
      scoredTableWrap.classList.remove("hidden");
      data.scored_candidates.forEach((m) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${escapeHtml(m.name)}</td>
          <td>${escapeHtml(m.provider)}</td>
          <td>${escapeHtml(m.tier)}</td>
          <td>${formatScore(m.overall_score)}</td>
          <td>${formatScore(m.cost_score)}</td>
          <td>${formatScore(m.performance_score)}</td>
          <td>${formatScore(m.speed_score)}</td>
          <td>${formatScore(m.fit_score)}</td>
        `;
        scoredTableBody.appendChild(tr);
      });
    } else {
      scoredTableWrap.classList.add("hidden");
    }

    // Show results section after a short delay
    setTimeout(() => showSection("results"), 600);
  }

  // ── Section Navigation ──
  function showSection(name) {
    if (name === "processing") {
      processingSection.classList.remove("hidden");
      resultsSection.classList.add("hidden");
      processingSection.scrollIntoView({ behavior: "smooth" });
    } else if (name === "results") {
      resultsSection.classList.remove("hidden");
      resultsSection.scrollIntoView({ behavior: "smooth" });
    }
  }

  function resetAll() {
    // Reset stepper
    currentStep = 0;
    Object.keys(guidedAnswers).forEach((k) => delete guidedAnswers[k]);
    $$(".stepper-question input, .stepper-question textarea").forEach(
      (el) => (el.value = "")
    );
    $$(".chip.selected").forEach((c) => c.classList.remove("selected"));
    updateStepper();

    // Reset freeform
    freeformInput.value = "";
    charCount.textContent = "0 chars";

    // Hide processing & results
    processingSection.classList.add("hidden");
    resultsSection.classList.add("hidden");

    // Scroll to input
    inputSection.scrollIntoView({ behavior: "smooth" });
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorOverlay.classList.remove("hidden");
  }

  // ── Helpers ──
  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatNum(n) {
    if (n == null) return "—";
    const num = Number(n);
    if (num === 0) return "0.00";
    if (num < 0.01) return num.toFixed(4);
    if (num < 1) return num.toFixed(3);
    return num.toFixed(2);
  }

  function formatContext(n) {
    if (!n) return "—";
    const num = Number(n);
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K`;
    return String(num);
  }

  function formatScore(n) {
    if (n == null) return "—";
    const num = Number(n);
    const pct = Math.min(100, Math.max(0, num));
    return `${num.toFixed(0)} <span class="score-bar"><span class="score-bar-fill" style="width:${pct}%"></span></span>`;
  }

  // ── Boot ──
  init();
})();
