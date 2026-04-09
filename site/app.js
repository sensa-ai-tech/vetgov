// 7/1 獸醫用藥新制追蹤器 — 前端邏輯
// 純原生 JS，無框架。讀 data.json 後渲染時間線、套用 filter、顯示統計。

const STANCE_LABEL = {
  supportive: "支持",
  opposed: "反對",
  neutral: "中立",
  mixed: "正反並陳",
};

const ORIGIN_LABEL = {
  seed: "人工整理",
  llm: "AI 萃取",
  human: "人工整理",
};

const state = {
  data: null,
  filters: { stance: "", importance: 0, origin: "" },
};

// ---------- fetch ----------

async function loadData() {
  try {
    const resp = await fetch("data.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    state.data = await resp.json();
    render();
  } catch (err) {
    console.error("data.json load failed:", err);
    renderError(err);
  }
}

// ---------- render ----------

function render() {
  const data = state.data;
  if (!data) return;

  // Hero meta
  document.getElementById("last-updated").textContent = formatDateTime(data.generated_at);
  document.getElementById("event-count").textContent = data.events.length;

  // Countdown
  renderCountdown(data.policy_effective_date || "2026-07-01");

  // Stats
  const counts = data.counts || {};
  setText("stat-events", data.events.length);
  setText("stat-sources", (data.sources_monitored || []).length);
  setText("stat-raw", counts.raw_total ?? "—");
  setText("stat-core", counts.raw_core ?? "—");

  // Timeline
  renderTimeline();

  // Sources
  renderSources(data.sources_monitored || []);
}

function renderCountdown(dateStr) {
  try {
    const target = new Date(dateStr + "T00:00:00+08:00");
    const now = new Date();
    const diffDays = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
    const value = diffDays > 0 ? String(diffDays) : (diffDays === 0 ? "0" : String(Math.abs(diffDays)));

    const setAll = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    setAll("cd-days", value);
    setAll("mq-days-1", value);
    setAll("mq-days-2", value);

    // Update hero ticker unit label if past the date
    if (diffDays < 0) {
      const unitEl = document.querySelector(".hero__ticker-unit");
      if (unitEl) unitEl.textContent = "DAYS SINCE";
    }
  } catch (e) {
    console.warn("countdown render failed", e);
  }
}

function renderTimeline() {
  const container = document.getElementById("timeline-list");
  const events = applyFilters(state.data.events);

  if (events.length === 0) {
    container.innerHTML = `<div class="empty">
      <h4>目前沒有符合條件的事件</h4>
      <p>試著放寬篩選條件，或等待下一次 ingest 執行（每日自動更新）。</p>
    </div>`;
    return;
  }

  container.innerHTML = events.map(renderItem).join("");
}

function renderItem(e) {
  const stance = e.stance || "neutral";
  const origin = e.origin || "seed";
  const imp = Number(e.importance) || 1;

  const sources = (e.sources || [])
    .filter(Boolean)
    .map((url, i) => `<a href="${escapeAttr(url)}" target="_blank" rel="noopener">原始來源 ${i + 1} ↗</a>`)
    .join("");

  const stakeholders = (e.stakeholders || []).length
    ? `<div class="ti-stakeholders">關係人：${e.stakeholders.map(escapeHtml).join("、")}</div>`
    : "";

  return `
    <article class="timeline-item imp-${imp}">
      <div class="ti-meta">
        <span class="ti-date">${escapeHtml(e.date || "日期不詳")}</span>
        <span class="ti-badge stance-${stance}">${STANCE_LABEL[stance] || stance}</span>
        <span class="ti-badge origin-${origin}">${ORIGIN_LABEL[origin] || origin}</span>
        <span class="ti-imp">重要性 ${imp}/5</span>
      </div>
      <h4 class="ti-title">${escapeHtml(e.title)}</h4>
      <p class="ti-summary">${escapeHtml(e.summary)}</p>
      ${stakeholders}
      ${sources ? `<div class="ti-sources">${sources}</div>` : ""}
    </article>
  `;
}

function renderSources(sources) {
  const ul = document.getElementById("sources-list");
  if (!sources.length) {
    ul.innerHTML = `<li class="empty-sources">尚未設定資料來源</li>`;
    return;
  }
  ul.innerHTML = sources
    .map(
      (s) => `<li>
        <span class="src-name">${escapeHtml(s.name)}</span>
        <span class="src-type">${escapeHtml(s.type || "rss")}</span>
      </li>`
    )
    .join("");
}

function renderError(err) {
  document.getElementById("timeline-list").innerHTML = `
    <div class="empty">
      <h4>無法載入 data.json</h4>
      <p>${escapeHtml(String(err))}</p>
      <p>如果你是在本地預覽，請確定已執行 <code>python -m src.cli build-site</code>。</p>
    </div>`;
}

// ---------- filters ----------

function applyFilters(events) {
  const { stance, importance, origin } = state.filters;
  return events.filter((e) => {
    if (stance && e.stance !== stance) return false;
    if (importance && Number(e.importance || 1) < Number(importance)) return false;
    if (origin && e.origin !== origin) return false;
    return true;
  });
}

function bindFilters() {
  const on = (id, key) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("change", (ev) => {
      state.filters[key] = ev.target.value;
      renderTimeline();
    });
  };
  on("filter-stance", "stance");
  on("filter-importance", "importance");
  on("filter-origin", "origin");
}

// ---------- utils ----------

function setText(id, v) {
  const el = document.getElementById(id);
  if (el) el.textContent = v;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(s) {
  return escapeHtml(s);
}

function formatDateTime(iso) {
  if (!iso) return "未知";
  try {
    const d = new Date(iso);
    return d.toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

// ---------- boot ----------

document.addEventListener("DOMContentLoaded", () => {
  bindFilters();
  loadData();
});
