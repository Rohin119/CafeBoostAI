/* ============================================================
   CafeBoost AI — script.js
   Full frontend logic: analyze, render results, animations
   ============================================================ */

// ── State ──────────────────────────────────────────────────
let isAnalyzing = false;

// ── Loading step animation ──────────────────────────────────
const STEPS = ["step1", "step2", "step3", "step4"];
const STEP_MESSAGES = [
  "Scraping website via Anakin Wire…",
  "Extracting and cleaning content…",
  "Running Gemini AI analysis…",
  "Building your report…",
];
let stepTimer = null;
let currentStep = 0;

function startStepAnimation() {
  currentStep = 0;
  STEPS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.className = "loading-step flex items-center gap-3 text-sm";
  });
  advanceStep();
}

function advanceStep() {
  if (currentStep >= STEPS.length) return;
  // Mark previous steps done
  for (let i = 0; i < currentStep; i++) {
    const el = document.getElementById(STEPS[i]);
    if (el) el.classList.add("done");
  }
  // Mark current step active
  const active = document.getElementById(STEPS[currentStep]);
  if (active) active.classList.add("active");

  const msgEl = document.getElementById("loadingMsg");
  if (msgEl) msgEl.textContent = STEP_MESSAGES[currentStep] || "";

  currentStep++;
  if (currentStep < STEPS.length) {
    stepTimer = setTimeout(advanceStep, 4000);
  }
}

function stopStepAnimation() {
  if (stepTimer) clearTimeout(stepTimer);
  // Mark all steps done
  STEPS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove("active");
      el.classList.add("done");
    }
  });
}

// ── Main analysis function ──────────────────────────────────
async function startAnalysis() {
  if (isAnalyzing) return;

  const input = document.getElementById("urlInput");
  const btn = document.getElementById("analyzeBtn");
  let url = input.value.trim();

  // Validate
  if (!url) {
    shakeInput();
    return;
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
    input.value = url;
  }

  isAnalyzing = true;
  hideError();

  // UI: show loading
  btn.disabled = true;
  btn.innerHTML = `<span class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></span>Analyzing…`;

  document.getElementById("resultsSection").classList.add("hidden");
  document.getElementById("features").classList.add("hidden");
  showSection("loadingSection");
  startStepAnimation();

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || `Server error ${response.status}`);
    }

    stopStepAnimation();
    await sleep(600); // brief pause so user sees "done"

    hideSection("loadingSection");
    renderReport(data.report, url);
    showSection("resultsSection");
    document.getElementById("analyzedUrl").textContent = url;

  } catch (err) {
    console.error("[CafeBoost]", err);
    hideSection("loadingSection");
    document.getElementById("features").classList.remove("hidden");
    showError(err.message || "Something went wrong. Please try again.");
  } finally {
    isAnalyzing = false;
    btn.disabled = false;
    btn.innerHTML = `Analyze Site <svg class="inline ml-1.5 -mt-0.5" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`;
  }
}

// ── Render report ───────────────────────────────────────────
function renderReport(report, url) {
  if (!report) return;

  // Scores
  animateScore("overallScore", "overallRing", report.overall_score, "#F97316");
  animateScore("seoScore", "seoRing", report.seo_score, "#60A5FA");
  animateScore("uxScore", "uxRing", report.ux_score, "#34D399");
  animateScore("businessScore", "businessRing", report.business_score, "#A78BFA");

  // Summary
  setText("summaryText", report.summary || "Analysis complete.");

  // Problems
  const problems = report.problems || [];
  document.getElementById("problemCount").textContent = problems.length;
  renderList("problemsList", problems, "#F87171", "●");

  // Missing features
  renderList("missingList", report.missing_features || [], "#FCD34D", "◆");

  // Strengths
  renderList("strengthsList", report.strengths || [], "#34D399", "✓");

  // Marketing
  renderList("marketingList", report.marketing_suggestions || [], "#A78BFA", "→");

  // Priority fixes
  renderPriorityList("priorityList", report.priority_fixes || []);

  // Improvements
  renderImprovements("improvementsList", report.improvements || []);

  // Scroll to results
  setTimeout(() => {
    document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

// ── Score ring animation ────────────────────────────────────
function animateScore(textId, ringId, score, color) {
  const textEl = document.getElementById(textId);
  const ringEl = document.getElementById(ringId);
  if (!textEl || !ringEl) return;

  const circumference = 2 * Math.PI * 32; // 201.06
  const offset = circumference - (score / 100) * circumference;

  // Animate number
  let current = 0;
  const duration = 1200;
  const start = performance.now();
  const tick = (now) => {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    current = Math.round(eased * score);
    textEl.textContent = current;
    if (progress < 1) requestAnimationFrame(tick);
    else textEl.textContent = score;
  };
  requestAnimationFrame(tick);

  // Animate ring
  setTimeout(() => {
    ringEl.style.strokeDashoffset = offset;
  }, 100);

  // Color tint based on score
  const scoreColor = score >= 70 ? color : score >= 45 ? "#FCD34D" : "#F87171";
  ringEl.style.stroke = scoreColor;
  textEl.style.color = scoreColor;
}

// ── List renderers ──────────────────────────────────────────
function renderList(containerId, items, dotColor, symbol) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<li class="result-item"><span class="text-brand-subtle italic">None identified</span></li>`;
    return;
  }
  container.innerHTML = items
    .map(
      (item) => `
    <li class="result-item fade-up">
      <span class="dot flex-shrink-0" style="background:${dotColor}; margin-top:6px; width:5px; height:5px; border-radius:50%;"></span>
      <span>${escapeHtml(item)}</span>
    </li>`
    )
    .join("");
}

function renderPriorityList(containerId, items) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = items
    .map(
      (item, i) => `
    <li class="priority-item fade-up">
      <span class="priority-num">${i + 1}</span>
      <span>${escapeHtml(item)}</span>
    </li>`
    )
    .join("");
}

function renderImprovements(containerId, items) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<p class="text-brand-subtle text-sm italic">No specific improvements identified.</p>`;
    return;
  }
  container.innerHTML = items
    .map(
      (item, i) => `
    <div class="improvement-item fade-up" style="animation-delay:${i * 0.08}s; opacity:0">
      <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-brand-orange/10 flex items-center justify-center mt-0.5">
        <span class="text-brand-orange font-display font-800 text-xs">${String(i + 1).padStart(2, "0")}</span>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1.5 flex-wrap">
          <h4 class="font-display font-600 text-sm text-white">${escapeHtml(item.title || "Improvement")}</h4>
          <span class="priority-badge priority-${item.priority || "Medium"}">${item.priority || "Medium"}</span>
          <span class="text-brand-subtle text-xs ml-auto">Impact: <span class="text-brand-text">${item.impact || "Medium"}</span></span>
        </div>
        <p class="text-brand-subtle text-xs leading-relaxed">${escapeHtml(item.description || "")}</p>
      </div>
    </div>`
    )
    .join("");
}

// ── Utility helpers ─────────────────────────────────────────
function showSection(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
}
function hideSection(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
}
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}
function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function showError(msg) {
  document.getElementById("errorMsg").textContent = msg;
  document.getElementById("errorBanner").classList.remove("hidden");
}
function hideError() {
  document.getElementById("errorBanner").classList.add("hidden");
}
function shakeInput() {
  const input = document.getElementById("urlInput");
  input.classList.add("shake");
  setTimeout(() => input.classList.remove("shake"), 500);
}
function resetAnalysis() {
  hideSection("resultsSection");
  document.getElementById("features").classList.remove("hidden");
  document.getElementById("urlInput").value = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Enter key support ───────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("urlInput");
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") startAnalysis();
    });
    input.focus();
  }
});