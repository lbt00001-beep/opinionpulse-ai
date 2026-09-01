// Global State
let currentAnalysisId = null;
let currentMentions = [];
let currentReportMarkdown = "";
let availableModels = [];
let selectedModelId = "google/gemini-3.5-flash-lite";
let donutChartInstance = null;
let barChartInstance = null;
let timelineChartInstance = null;
let timerInterval = null;
let startTime = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  loadModels();
  loadSettings();
  loadHistory();
  initCharts();
});

// Set Quick Search Query
function setQuery(text) {
  const input = document.getElementById("topicInput");
  input.value = text;
  input.focus();
}

// Show Toast Notification
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toastMsg");
  const toastIcon = document.getElementById("toastIcon");
  
  toastMsg.innerText = message;
  if (isError) {
    toastIcon.className = "fa-solid fa-circle-exclamation text-rose-400";
    toast.className = "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl bg-darkbg-700 border border-rose-500/50 text-white text-xs font-medium shadow-2xl flex items-center gap-2 transition-all";
  } else {
    toastIcon.className = "fa-solid fa-circle-check text-emerald-400";
    toast.className = "fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl bg-darkbg-700 border border-emerald-500/50 text-white text-xs font-medium shadow-2xl flex items-center gap-2 transition-all";
  }
  
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

// Load Models from API
async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    availableModels = data.models || [];
    renderModelCards();
  } catch (err) {
    console.error("Error loading models:", err);
  }
}

// Render Model selection cards in settings modal
function renderModelCards() {
  const container = document.getElementById("modelCardsContainer");
  if (!container) return;
  
  container.innerHTML = availableModels.map(m => {
    const isSelected = m.id === selectedModelId;
    return `
      <div 
        onclick="selectModel('${m.id}')"
        class="p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-1.5 ${
          isSelected 
            ? 'bg-brand-500/10 border-brand-500 shadow-md shadow-brand-500/10' 
            : 'bg-darkbg-900/60 border-darkbg-700 hover:border-slate-600'
        }"
      >
        <div class="flex items-center justify-between">
          <span class="font-bold text-xs text-white">${m.name}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-darkbg-800 text-brand-300 font-semibold border border-brand-500/20">${m.badge || m.provider}</span>
        </div>
        <p class="text-[11px] text-slate-400 leading-tight">${m.description}</p>
        <div class="flex items-center justify-between text-[10px] text-slate-400 mt-1 pt-1.5 border-t border-darkbg-700/60">
          <span>Coste: <strong class="text-slate-300">${m.input_cost}</strong></span>
          <span class="font-mono text-slate-400">${m.provider}</span>
        </div>
      </div>
    `;
  }).join("");
}

function selectModel(modelId) {
  selectedModelId = modelId;
  renderModelCards();
  
  const m = availableModels.find(x => x.id === modelId);
  const navName = document.getElementById("navModelName");
  if (navName && m) {
    navName.innerText = m.name;
  }
  
  const customInput = document.getElementById("customModelInput");
  if (customInput) {
    customInput.value = modelId;
  }
}

// Load Settings from API
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    
    if (data.selected_model) {
      selectedModelId = data.selected_model;
      const m = availableModels.find(x => x.id === selectedModelId);
      if (m && document.getElementById("navModelName")) {
        document.getElementById("navModelName").innerText = m.name;
      }
      renderModelCards();
    }
    
    const keyInput = document.getElementById("settingApiKey");
    if (keyInput && data.has_key) {
      keyInput.placeholder = data.openrouter_api_key_masked || "sk-or-v1-*** (Configurada)";
    }
    
    if (data.mcp_settings) {
      if (document.getElementById("settingExaKey")) {
        document.getElementById("settingExaKey").value = data.mcp_settings.exa_api_key || "";
      }
      if (document.getElementById("settingApifyKey")) {
        document.getElementById("settingApifyKey").value = data.mcp_settings.apify_api_token || "";
      }
    }
  } catch (err) {
    console.error("Error loading settings:", err);
  }
}

// Save Settings
async function saveSettings() {
  const keyVal = document.getElementById("settingApiKey").value.trim();
  const customModel = document.getElementById("customModelInput").value.trim();
  const exaKey = document.getElementById("settingExaKey")?.value.trim() || "";
  const apifyKey = document.getElementById("settingApifyKey")?.value.trim() || "";
  
  const finalModel = customModel || selectedModelId;
  
  const payload = {
    selected_model: finalModel,
    mcp_settings: {
      exa_api_key: exaKey,
      apify_api_token: apifyKey
    }
  };
  
  if (keyVal) {
    payload.openrouter_api_key = keyVal;
  }
  
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Ajustes guardados correctamente");
      selectedModelId = finalModel;
      const m = availableModels.find(x => x.id === finalModel);
      if (document.getElementById("navModelName")) {
        document.getElementById("navModelName").innerText = m ? m.name : finalModel;
      }
      closeSettingsModal();
    } else {
      showToast(data.detail || "Error al guardar ajustes", true);
    }
  } catch (err) {
    showToast("Error de conexión con el servidor", true);
  }
}

// Test OpenRouter API Key
async function testApiKey() {
  const keyInput = document.getElementById("settingApiKey");
  const testRes = document.getElementById("keyTestResult");
  const btn = document.getElementById("btnTestKey");
  
  btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin mr-1"></i> Verificando...`;
  btn.disabled = true;
  testRes.classList.add("hidden");
  
  try {
    const res = await fetch("/api/test-key", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ api_key: keyInput.value.trim() })
    });
    const data = await res.json();
    
    testRes.classList.remove("hidden");
    if (data.valid) {
      testRes.className = "text-xs text-emerald-400 font-medium";
      testRes.innerHTML = `<i class="fa-solid fa-circle-check"></i> Clave válida. Créditos/Límite activos en OpenRouter.`;
    } else {
      testRes.className = "text-xs text-rose-400 font-medium";
      testRes.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.error || 'Clave no válida'}`;
    }
  } catch (err) {
    testRes.classList.remove("hidden");
    testRes.className = "text-xs text-rose-400 font-medium";
    testRes.innerText = "Error al contactar con OpenRouter";
  } finally {
    btn.innerHTML = `<i class="fa-solid fa-vial-circle-check mr-1"></i> Probar Clave`;
    btn.disabled = false;
  }
}

// Toggle API Key Visibility
function toggleKeyVisibility() {
  const input = document.getElementById("settingApiKey");
  const icon = document.getElementById("eyeIcon");
  if (input.type === "password") {
    input.type = "text";
    icon.className = "fa-solid fa-eye-slash";
  } else {
    input.type = "password";
    icon.className = "fa-solid fa-eye";
  }
}

// Settings Modal controls
function openSettingsModal() {
  document.getElementById("settingsModal").classList.remove("hidden");
}
function closeSettingsModal() {
  document.getElementById("settingsModal").classList.add("hidden");
}

// Help Modal controls
function openHelpModal() {
  document.getElementById("helpModal").classList.remove("hidden");
}
function closeHelpModal() {
  document.getElementById("helpModal").classList.add("hidden");
}

// History Drawer controls
function toggleHistoryDrawer() {
  const drawer = document.getElementById("historyDrawer");
  drawer.classList.toggle("translate-x-full");
  if (!drawer.classList.contains("translate-x-full")) {
    loadHistory();
  }
}

// Load History Items
async function loadHistory() {
  const container = document.getElementById("historyListContainer");
  if (!container) return;
  
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    const history = data.history || [];
    
    if (history.length === 0) {
      container.innerHTML = `<p class="text-xs text-slate-500 text-center py-6">No hay análisis guardados aún.</p>`;
      return;
    }
    
    container.innerHTML = history.map(item => {
      const nsi = item.metrics?.weighted_nsi !== undefined ? item.metrics.weighted_nsi : (item.metrics?.net_sentiment_index || 0);
      const nsiColor = nsi > 0 ? "text-emerald-400 bg-emerald-500/10" : (nsi < 0 ? "text-rose-400 bg-rose-500/10" : "text-slate-300 bg-slate-700");
      const dt = item.created_at ? item.created_at.replace("T", " ").slice(0, 16) : "";
      
      return `
        <div class="p-3 rounded-xl bg-darkbg-900/80 border border-darkbg-700 hover:border-brand-500/50 transition flex flex-col gap-2 group">
          <div class="flex items-center justify-between">
            <button onclick="loadHistoryItem('${item.id}')" class="text-left font-bold text-xs text-white hover:text-brand-300 truncate max-w-[180px]">
              ${item.topic}
            </button>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${nsiColor}">
              NSI: ${nsi > 0 ? '+' : ''}${nsi}%
            </span>
          </div>
          <div class="flex items-center justify-between text-[10px] text-slate-400">
            <span>${dt}</span>
            <div class="flex items-center gap-1.5">
              <button onclick="loadHistoryItem('${item.id}')" class="text-brand-400 hover:underline">Ver</button>
              <button onclick="deleteHistoryItem('${item.id}')" class="text-slate-500 hover:text-rose-400"><i class="fa-solid fa-trash"></i></button>
            </div>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading history:", err);
  }
}

// Load a specific historical analysis
async function loadHistoryItem(analysisId) {
  try {
    const res = await fetch(`/api/history/${analysisId}`);
    if (!res.ok) throw new Error("No se pudo cargar");
    const item = await res.json();
    
    currentAnalysisId = item.id;
    currentMentions = item.mentions_sample || [];
    currentReportMarkdown = item.report_markdown || "";
    
    document.getElementById("topicInput").value = item.topic;
    displayAnalysisResults(item.metrics, currentMentions, currentReportMarkdown, item.model_used);
    
    document.getElementById("historyDrawer").classList.add("translate-x-full");
    showToast(`Informe de "${item.topic}" cargado`);
  } catch (err) {
    showToast("Error al cargar informe del historial", true);
  }
}

// Delete historical analysis
async function deleteHistoryItem(analysisId) {
  try {
    await fetch(`/api/history/${analysisId}`, { method: "DELETE" });
    loadHistory();
    showToast("Informe eliminado del historial");
  } catch (err) {
    showToast("Error al eliminar", true);
  }
}

// Initialize Chart.js Charts
function initCharts() {
  // 1. Donut Chart
  const donutCtx = document.getElementById("sentimentDonutChart").getContext("2d");
  donutChartInstance = new Chart(donutCtx, {
    type: "doughnut",
    data: {
      labels: ["Positivo", "Neutral", "Negativo"],
      datasets: [{
        data: [0, 100, 0],
        backgroundColor: ["#10b981", "#64748b", "#f43f5e"],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "72%",
      plugins: {
        legend: { display: false }
      }
    }
  });

  // 2. Bar Chart
  const barCtx = document.getElementById("platformBarChart").getContext("2d");
  barChartInstance = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: ["Reddit", "Medios", "Redes"],
      datasets: [
        { label: "Positivo", data: [0, 0, 0], backgroundColor: "#10b981" },
        { label: "Neutral", data: [0, 0, 0], backgroundColor: "#64748b" },
        { label: "Negativo", data: [0, 0, 0], backgroundColor: "#f43f5e" }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
        y: { stacked: true, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { size: 10 } } }
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1", boxWidth: 10, font: { size: 10 } } }
      }
    }
  });

  // 3. Timeline Line Chart (Evolución Cronológica)
  const timelineCtx = document.getElementById("timelineChart")?.getContext("2d");
  if (timelineCtx) {
    timelineChartInstance = new Chart(timelineCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [{
          label: "Índice Neto de Sentimiento (NSI %)",
          data: [],
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.12)",
          borderWidth: 2.5,
          pointBackgroundColor: "#38bdf8",
          pointBorderColor: "#ffffff",
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.35
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { color: "rgba(255,255,255,0.04)" },
            ticks: { color: "#94a3b8", font: { size: 10 } }
          },
          y: {
            min: -100,
            max: 100,
            grid: { color: "rgba(255,255,255,0.05)" },
            ticks: {
              color: "#94a3b8",
              font: { size: 10 },
              callback: (val) => `${val > 0 ? '+' : ''}${val}%`
            }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `NSI Ponderado: ${context.parsed.y > 0 ? '+' : ''}${context.parsed.y}%`
            }
          }
        }
      }
    });
  }
}

// Update Charts with fresh metrics
function updateCharts(metrics) {
  if (!metrics) return;
  
  const dist = metrics.distribution || { positive: 0, neutral: 100, negative: 0 };
  
  // Update Donut
  if (donutChartInstance) {
    donutChartInstance.data.datasets[0].data = [dist.positive, dist.neutral, dist.negative];
    donutChartInstance.update();
  }
  
  document.getElementById("pctPos").innerText = `${dist.positive}%`;
  document.getElementById("pctNeu").innerText = `${dist.neutral}%`;
  document.getElementById("pctNeg").innerText = `${dist.negative}%`;
  
  // Update Bar Chart
  if (barChartInstance && metrics.platform_breakdown) {
    const platforms = Object.keys(metrics.platform_breakdown);
    const posData = platforms.map(p => metrics.platform_breakdown[p].positive || 0);
    const neuData = platforms.map(p => metrics.platform_breakdown[p].neutral || 0);
    const negData = platforms.map(p => metrics.platform_breakdown[p].negative || 0);
    
    barChartInstance.data.labels = platforms;
    barChartInstance.data.datasets[0].data = posData;
    barChartInstance.data.datasets[1].data = neuData;
    barChartInstance.data.datasets[2].data = negData;
    barChartInstance.update();
  }

  // Update Timeline Line Chart
  if (timelineChartInstance && metrics.timeline && metrics.timeline.length > 0) {
    timelineChartInstance.data.labels = metrics.timeline.map(p => p.display_date);
    timelineChartInstance.data.datasets[0].data = metrics.timeline.map(p => p.nsi);
    
    // Dynamic point colors depending on sentiment polarity
    timelineChartInstance.data.datasets[0].pointBackgroundColor = metrics.timeline.map(p => 
      p.nsi > 5 ? "#10b981" : (p.nsi < -5 ? "#f43f5e" : "#38bdf8")
    );
    timelineChartInstance.update();
  }
}

// Main Search & Analysis Handler (SSE Streaming)
async function handleSearch(e) {
  e.preventDefault();
  const topic = document.getElementById("topicInput").value.trim();
  if (!topic) return;

  const sourceReddit = document.getElementById("sourceReddit").checked;
  const sourceNews = document.getElementById("sourceNews").checked;
  const sourceSocial = document.getElementById("sourceSocial").checked;
  const timeRange = document.getElementById("timeRangeSelect")?.value || "all";
  
  const sources = [];
  if (sourceReddit) sources.push("reddit");
  if (sourceNews) sources.push("news");
  if (sourceSocial) sources.push("social_web");
  
  if (sources.length === 0) {
    showToast("Por favor selecciona al menos una fuente de datos", true);
    return;
  }

  // UI Setup for execution
  const searchBtn = document.getElementById("searchBtn");
  searchBtn.disabled = true;
  searchBtn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i>`;
  
  const stepper = document.getElementById("loadingStepper");
  const dashboard = document.getElementById("resultsDashboard");
  const reportContainer = document.getElementById("reportMarkdownContainer");
  
  stepper.classList.remove("hidden");
  dashboard.classList.add("hidden");
  reportContainer.innerHTML = "";
  currentReportMarkdown = "";
  
  // Timer
  startTime = Date.now();
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    document.getElementById("stepperElapsed").innerText = `${elapsed}s`;
  }, 100);

  // Stepper Step 1 Active
  setStepperStage(1, `Recolectando menciones en Reddit, Prensa y Redes (${timeRange}) para "${topic}"...`);

  // Connect to SSE Endpoint
  const url = `/api/analyze/stream?topic=${encodeURIComponent(topic)}&sources=${encodeURIComponent(sources.join(","))}&time_range=${encodeURIComponent(timeRange)}&model=${encodeURIComponent(selectedModelId)}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.stage === "harvesting") {
        setStepperStage(1, data.message);
      } else if (data.stage === "scoring") {
        setStepperStage(2, data.message);
      } else if (data.stage === "metrics_ready") {
        setStepperStage(3, "Redactando informe ejecutivo con IA...");
        stepper.classList.add("hidden");
        dashboard.classList.remove("hidden");
        
        currentMentions = data.mentions_sample || [];
        displayAnalysisResults(data.metrics, currentMentions, "", selectedModelId);
      } else if (data.stage === "report_start") {
        setStepperStage(3, data.message);
      } else if (data.stage === "report_chunk") {
        currentReportMarkdown += data.chunk;
        reportContainer.innerHTML = marked.parse(currentReportMarkdown);
      } else if (data.stage === "done") {
        currentAnalysisId = data.analysis_id;
        eventSource.close();
        finishSearch();
        loadHistory();
      }
    } catch (err) {
      console.error("SSE parse error:", err);
    }
  };

  eventSource.onerror = (err) => {
    console.error("SSE connection error:", err);
    eventSource.close();
    finishSearch();
    showToast("Análisis completado o conexión cerrada");
  };
}

function setStepperStage(stageNum, message) {
  document.getElementById("stepperTitle").innerText = `Fase ${stageNum} de 3`;
  document.getElementById("stepperDetail").innerText = message;
  
  for (let i = 1; i <= 3; i++) {
    const stepEl = document.getElementById(`step${i}`);
    if (i < stageNum) {
      stepEl.className = "flex items-center gap-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/40 text-emerald-300";
    } else if (i === stageNum) {
      stepEl.className = "flex items-center gap-2 p-2.5 rounded-lg bg-brand-500/10 border border-brand-500/40 text-brand-300 animate-pulse";
    } else {
      stepEl.className = "flex items-center gap-2 p-2.5 rounded-lg bg-darkbg-900/40 border border-darkbg-700 text-slate-500";
    }
  }
}

function finishSearch() {
  if (timerInterval) clearInterval(timerInterval);
  const searchBtn = document.getElementById("searchBtn");
  searchBtn.disabled = false;
  searchBtn.innerHTML = `<span>Analizar</span> <i class="fa-solid fa-arrow-right"></i>`;
  document.getElementById("loadingStepper").classList.add("hidden");
}

// Display results in the dashboard
function displayAnalysisResults(metrics, mentions, reportMarkdown, modelUsed) {
  const dashboard = document.getElementById("resultsDashboard");
  dashboard.classList.remove("hidden");

  // Domain Category and Weights Banner
  const domainCategory = metrics.detected_domain || "General / Multitemático";
  document.getElementById("kpiDomainCategory").innerText = domainCategory;
  
  const weights = metrics.active_weights || {};
  const chipsContainer = document.getElementById("weightsChipsContainer");
  if (chipsContainer) {
    chipsContainer.innerHTML = Object.entries(weights)
      .filter(([k, v]) => typeof v === "number")
      .map(([plat, w]) => `
        <span class="px-2 py-1 rounded-md bg-darkbg-900 border border-darkbg-700 text-[11px] flex items-center gap-1">
          <span class="text-slate-400">${plat}:</span>
          <strong class="text-brand-300 font-mono">${Math.round(w * 100)}%</strong>
        </span>
      `).join("");
  }
  
  const expEl = document.getElementById("kpiWeightingExplanation");
  if (expEl) {
    if (domainCategory.includes("Finanzas")) {
      expEl.innerText = "Mayor peso a prensa económica contrastada (45%) y foros de inversión (35%) para filtrar ruido.";
    } else if (domainCategory.includes("Tecnología")) {
      expEl.innerText = "Mayor peso a comunidades técnicas de Reddit (45%) y debate de desarrolladores en X (30%).";
    } else if (domainCategory.includes("Entretenimiento")) {
      expEl.innerText = "Mayor peso a viralidad y reacción de audiencia en Redes Sociales (45%) y fans en Reddit (35%).";
    } else if (domainCategory.includes("Política")) {
      expEl.innerText = "Mayor peso a medios editoriales (40%) y debate social en X/Twitter (35%).";
    } else {
      expEl.innerText = "Ponderación balanceada multicanal adaptada a la relevancia del contenido.";
    }
  }

  // Trend Badge
  const trend = metrics.trend || { direction: "Estable", delta: 0.0, icon: "fa-arrows-left-right", color: "text-slate-300", badge: "bg-slate-700/40 border-slate-600/30" };
  const trendBadge = document.getElementById("kpiTrendBadge");
  const trendIcon = document.getElementById("kpiTrendIcon");
  const trendText = document.getElementById("kpiTrendText");

  if (trendBadge && trendIcon && trendText) {
    trendBadge.className = `text-xs font-bold px-2.5 py-1 rounded-lg flex items-center gap-1.5 ${trend.badge || 'bg-slate-700/40 border border-slate-600/30'} ${trend.color || 'text-slate-300'}`;
    trendIcon.className = `fa-solid ${trend.icon || 'fa-arrows-left-right'}`;
    trendText.innerText = `${trend.direction} (${trend.delta > 0 ? '+' : ''}${trend.delta}%)`;
  }

  // KPI: Polarization & Social Friction Index
  const pol = metrics.polarization || { score: 0, label: "Consenso", level: "low", description: "", badge_color: "text-slate-300 bg-slate-800 border-slate-700", icon: "fa-handshake" };
  const polScore = document.getElementById("kpiPolarizationScore");
  const polBadge = document.getElementById("kpiPolarizationBadge");
  const polDesc = document.getElementById("kpiPolarizationDesc");
  const polBar = document.getElementById("polarizationProgressBar");
  const polIcon = document.getElementById("kpiPolarizationIcon");
  const polIconBox = document.getElementById("polarizationBadgeIcon");

  if (polScore) polScore.innerText = `${pol.score}%`;
  if (polBadge) {
    polBadge.innerText = pol.label.replace(/^[^a-zA-ZáéíóúÁÉÍÓÚñÑ]+/, '').trim();
    polBadge.className = `text-[10px] font-bold px-2 py-0.5 rounded border ${pol.badge_color || 'text-slate-300 bg-slate-800 border-slate-700'}`;
  }
  if (polDesc) polDesc.innerText = pol.description || "Nivel de bimodalidad y enfrentamiento entre bandos";
  if (polBar) {
    polBar.style.width = `${pol.score}%`;
    polBar.className = pol.score >= 70 ? "h-full bg-rose-500 transition-all duration-700" : (pol.score >= 40 ? "h-full bg-amber-500 transition-all duration-700" : "h-full bg-emerald-500 transition-all duration-700");
  }
  if (polIcon && pol.icon) {
    polIcon.className = `fa-solid ${pol.icon}`;
  }
  if (polIconBox) {
    polIconBox.className = pol.score >= 70 ? "w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center text-sm" : "w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-sm";
  }

  // KPI: Net Sentiment Index (Weighted)
  const nsi = metrics.weighted_nsi !== undefined ? metrics.weighted_nsi : (metrics.net_sentiment_index || 0);
  const kpiNSI = document.getElementById("kpiNSI");
  const kpiNSILabel = document.getElementById("kpiNSILabel");
  const nsiBar = document.getElementById("nsiProgressBar");
  const nsiIcon = document.getElementById("nsiBadgeIcon");

  kpiNSI.innerText = `${nsi > 0 ? '+' : ''}${nsi}%`;
  
  // Bar width from 0% (-100) to 100% (+100)
  const barWidth = Math.min(100, Math.max(0, (nsi + 100) / 2));
  nsiBar.style.width = `${barWidth}%`;

  if (pol.score >= 60 && Math.abs(nsi) <= 20) {
    kpiNSILabel.innerText = "🔥 Polarización Extrema";
    kpiNSILabel.className = "text-xs font-medium text-rose-400 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30";
    nsiBar.className = "h-full bg-amber-500 transition-all duration-700";
    nsiIcon.className = "w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center text-sm";
    nsiIcon.innerHTML = `<i class="fa-solid fa-fire-flame-curved"></i>`;
  } else if (nsi >= 15) {
    kpiNSILabel.innerText = "Mayoría Positiva";
    kpiNSILabel.className = "text-xs font-medium text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10";
    nsiBar.className = "h-full bg-emerald-500 transition-all duration-700";
    nsiIcon.className = "w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-sm";
    nsiIcon.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i>`;
  } else if (nsi <= -15) {
    kpiNSILabel.innerText = "Mayoría Crítica";
    kpiNSILabel.className = "text-xs font-medium text-rose-400 px-2 py-0.5 rounded bg-rose-500/10";
    nsiBar.className = "h-full bg-rose-500 transition-all duration-700";
    nsiIcon.className = "w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center text-sm";
    nsiIcon.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i>`;
  } else {
    kpiNSILabel.innerText = "Opinión Dividida / Mixta";
    kpiNSILabel.className = "text-xs font-medium text-amber-400 px-2 py-0.5 rounded bg-amber-500/10";
    nsiBar.className = "h-full bg-amber-500 transition-all duration-700";
    nsiIcon.className = "w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center text-sm";
    nsiIcon.innerHTML = `<i class="fa-solid fa-scale-unbalanced"></i>`;
  }

  // KPI: Total Mentions
  document.getElementById("kpiTotalMentions").innerText = metrics.total_count || 0;
  
  // KPI: Predominant Emotion
  const emotions = Object.entries(metrics.emotion_breakdown || {}).sort((a, b) => b[1] - a[1]);
  document.getElementById("kpiEmotion").innerText = emotions.length > 0 ? emotions[0][0] : "Neutral & Informativo";

  // KPI: Model Name
  const m = availableModels.find(x => x.id === modelUsed);
  document.getElementById("kpiModelUsed").innerText = m ? m.name : modelUsed;

  // Key Phrases Tags
  const phrasesContainer = document.getElementById("keyPhrasesContainer");
  phrasesContainer.innerHTML = (metrics.key_phrases || []).map(phrase => `
    <span class="px-2.5 py-1 rounded-lg bg-darkbg-900 border border-darkbg-700 text-slate-300 text-xs hover:border-brand-500/50 transition">
      #${phrase}
    </span>
  `).join("");

  // Update Charts (Donut, Bar & Timeline Line Chart)
  updateCharts(metrics);

  // Render Mentions Feed
  renderMentionsFeed(mentions);

  // Render Markdown Report
  if (reportMarkdown) {
    document.getElementById("reportMarkdownContainer").innerHTML = marked.parse(reportMarkdown);
  }
}

// Render Mentions list
function renderMentionsFeed(mentions, filter = "all") {
  const container = document.getElementById("mentionsFeedList");
  if (!container) return;

  const validMentions = Array.isArray(mentions) ? mentions : [];
  const filtered = filter === "all" 
    ? validMentions 
    : validMentions.filter(m => m.sentiment_label === filter);
    
  const countBadge = document.getElementById("mentionsCountBadge");
  if (countBadge) {
    countBadge.innerText = `${filtered.length} citas`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center text-center py-10 px-4 border border-dashed border-darkbg-700 rounded-xl">
        <i class="fa-solid fa-comments text-2xl text-slate-600 mb-2"></i>
        <p class="text-xs text-slate-400 font-medium">No hay menciones en esta categoría</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Prueba a seleccionar el filtro "Todos"</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(m => {
    const isPos = m.sentiment_label === "Positivo";
    const isNeg = m.sentiment_label === "Negativo";
    const badgeColor = isPos 
      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" 
      : (isNeg ? "text-rose-400 bg-rose-500/10 border-rose-500/30" : "text-slate-300 bg-slate-700/50 border-slate-600/30");
      
    const platStr = String(m.platform || "");
    let platformIcon = '<i class="fa-solid fa-globe text-purple-400"></i>';
    if (platStr.includes("Reddit")) {
      platformIcon = '<i class="fa-brands fa-reddit text-orange-500"></i>';
    } else if (platStr.includes("Medios") || platStr.includes("Noticias") || platStr.includes("Prensa")) {
      platformIcon = '<i class="fa-solid fa-newspaper text-blue-400"></i>';
    } else if (platStr.includes("Twitter") || platStr.includes("X")) {
      platformIcon = '<i class="fa-brands fa-x-twitter text-slate-200"></i>';
    } else if (platStr.includes("Facebook")) {
      platformIcon = '<i class="fa-brands fa-facebook text-blue-500"></i>';
    } else if (platStr.includes("LinkedIn")) {
      platformIcon = '<i class="fa-brands fa-linkedin text-sky-400"></i>';
    }

    const dateStr = m.iso_date || m.published_at || "Reciente";
    const engagementStr = m.engagement ? `<span class="text-[10px] text-slate-400 bg-darkbg-800 px-1.5 py-0.5 rounded border border-darkbg-700">${m.engagement}</span>` : "";

    const scoreVal = m.sentiment_score !== undefined ? (m.sentiment_score > 0 ? `+${m.sentiment_score}` : `${m.sentiment_score}`) : '0.0';
    const confVal = m.confidence !== undefined ? `${m.confidence}%` : '80%';
    const methodSnippet = m.method_info ? `<div class="text-[10px] text-slate-500 italic truncate" title="${m.method_info}"><i class="fa-solid fa-microscope text-brand-400 mr-1"></i>${m.method_info}</div>` : '';

    return `
      <div class="p-3.5 rounded-xl bg-darkbg-900/90 border border-darkbg-700/80 hover:border-slate-600 transition flex flex-col gap-2 text-xs shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5 font-semibold text-white truncate max-w-[190px]">
            ${platformIcon}
            <span class="truncate">${m.source_name || m.platform || 'Fuente Web'}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="px-1.5 py-0.5 rounded bg-darkbg-800 text-[10px] font-mono text-slate-400 border border-darkbg-700" title="Confianza estadística de clasificación">
              Conf: <strong class="text-slate-300">${confVal}</strong>
            </span>
            <span class="px-2 py-0.5 rounded-full border text-[10px] font-bold ${badgeColor}">
              ${m.sentiment_label || 'Neutral'} (${scoreVal})
            </span>
          </div>
        </div>

        <p class="text-slate-300 leading-relaxed">${m.content || m.title || 'Sin contenido'}</p>

        ${methodSnippet}

        <div class="flex items-center justify-between pt-2 border-t border-darkbg-800 text-[10px] text-slate-400">
          <span class="truncate max-w-[170px]">${m.author || 'Usuario'} • <span class="text-slate-500">${dateStr}</span></span>
          <div class="flex items-center gap-2">
            ${engagementStr}
            ${m.url ? `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="text-brand-400 hover:text-brand-300 hover:underline flex items-center gap-1">Ver fuente <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// Filter mentions by sentiment
function filterMentions(type) {
  const btnAll = document.getElementById("btnFilterAll");
  const btnPos = document.getElementById("btnFilterPos");
  const btnNeg = document.getElementById("btnFilterNeg");
  const btnNeu = document.getElementById("btnFilterNeu");

  [btnAll, btnPos, btnNeg, btnNeu].forEach(b => {
    b.className = "px-2.5 py-1 rounded-md bg-darkbg-700 hover:bg-darkbg-600 text-slate-300";
  });

  if (type === "all") btnAll.className = "px-2.5 py-1 rounded-md bg-brand-600 text-white font-medium";
  if (type === "Positivo") btnPos.className = "px-2.5 py-1 rounded-md bg-emerald-600 text-white font-medium";
  if (type === "Negativo") btnNeg.className = "px-2.5 py-1 rounded-md bg-rose-600 text-white font-medium";
  if (type === "Neutral") btnNeu.className = "px-2.5 py-1 rounded-md bg-slate-600 text-white font-medium";

  renderMentionsFeed(currentMentions, type);
}

// Copy report markdown
function copyReportMarkdown() {
  if (!currentReportMarkdown) {
    showToast("No hay informe para copiar", true);
    return;
  }
  navigator.clipboard.writeText(currentReportMarkdown).then(() => {
    showToast("Informe copiado al portapapeles");
  });
}

// Download report as markdown
function downloadReportMD() {
  if (!currentReportMarkdown) {
    showToast("No hay informe para descargar", true);
    return;
  }
  const topic = document.getElementById("topicInput").value.trim() || "analisis_sentimiento";
  const blob = new Blob([currentReportMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `informe_sentimiento_${topic.replace(/\s+/g, "_")}.md`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("Informe descargado como Markdown");
}

// Print / Export to PDF (Full Report without clipping)
function printReportToPDF() {
  if (!currentReportMarkdown) {
    showToast("No hay informe para exportar a PDF", true);
    return;
  }

  const topic = document.getElementById("topicInput").value.trim() || "Tema Analizado";
  const modelEl = document.getElementById("kpiModelUsed");
  const modelName = modelEl ? modelEl.innerText : selectedModelId;
  const nsiEl = document.getElementById("kpiNSI");
  const nsiVal = nsiEl ? nsiEl.innerText : "+0.0%";
  const domainEl = document.getElementById("kpiDomainCategory");
  const domainVal = domainEl ? domainEl.innerText : "General";

  // Fill print header
  const printTopic = document.getElementById("printHeaderTopic");
  if (printTopic) printTopic.innerText = topic;
  const printDate = document.getElementById("printHeaderDate");
  if (printDate) printDate.innerText = `Fecha: ${new Date().toLocaleDateString('es-ES')} ${new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit'})}`;
  const printModel = document.getElementById("printHeaderModel");
  if (printModel) printModel.innerText = `Modelo: ${modelName}`;
  const printDomain = document.getElementById("printHeaderDomain");
  if (printDomain) printDomain.innerText = domainVal;
  const printNSI = document.getElementById("printHeaderNSI");
  if (printNSI) printNSI.innerText = nsiVal;

  window.print();
}
