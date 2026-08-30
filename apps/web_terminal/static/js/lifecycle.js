/**
 * DeepAlpha — ML Super-Pump Lifecycle & CRISP-DM Research Engine (lifecycle.js)
 * Standalone dedicated controller for Multi-Month Campaigns, 2-Way CRISP-DM Scatter Chart, and Multi-Year Empirical Event DB.
 */

let currentCampaignFilter = "ACTIVE";
let currentCampaignSort = "PROGRESS_DESC";
let currentCampaignViewMode = "LIST"; // Default: LIST view for better readability
let currentCampaignSearchQuery = "";
let cachedCampaignsData = null;
let cachedResearchData = null;

// ─── PAGINATION STATE ────────────────────────────────────────────────────────
let campaignCurrentPage = 1;
let campaignPageSize = 20; // 20 items per page by default (options: 10, 20, 50, 100, 0=all)

let datasetCurrentPage = 1;
let datasetPageSize = 25;
let cachedDatasetEvents = [];

let ledgerCurrentPage = 1;
let ledgerPageSize = 20;
let cachedLedgerRecords = [];

document.addEventListener("DOMContentLoaded", () => {
  fetchGapFillStatus();
  fetchCampaignsData();
  fetchResearchData();
  fetchBenchmarkLedger();
  fetchCorrectionStatus();
  runInteractiveMLPrediction(); // Immediately fetch live Binance Futures metrics on load
  setInterval(fetchCampaignsData, 5000);
  setInterval(fetchBenchmarkLedger, 10000);
  setInterval(fetchGapFillStatus, 15000);
  setInterval(fetchCorrectionStatus, 30000);
});

async function fetchCorrectionStatus() {
  try {
    const res = await fetch("/api/ml/accuracy_correction_status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    const audit = data.audit || {};
    const qualityScore = audit.data_quality_score_pct;
    const corrections = data.total_corrections_applied || 0;
    const totalEvents = audit.total_events || 388;
    const superPumps = audit.super_pumps_beyond_tier_ceiling || 0;

    const qualityEl = document.getElementById("stat-data-quality");
    const subEl = document.getElementById("ace-quality-sub");
    const cardEl = document.getElementById("ace-quality-card");
    const trainingEl = document.getElementById("stat-training-events");

    if (trainingEl) trainingEl.innerText = `${totalEvents} Event`;

    if (qualityEl && qualityScore !== undefined) {
      qualityEl.innerText = `${qualityScore}%`;
      // Color grade: green ≥ 99%, yellow ≥ 95%, red < 95%
      const color = qualityScore >= 99 ? "#00e676" : qualityScore >= 95 ? "#ffb300" : "#ff3366";
      qualityEl.style.color = color;
      if (cardEl) cardEl.style.borderLeftColor = color;
    }

    if (subEl) {
      if (corrections > 0) {
        subEl.innerText = `✅ ${corrections} đỉnh đã hiệu chỉnh | ${superPumps} super-pump`;
      } else if (superPumps > 0) {
        subEl.innerText = `⚠️ ${superPumps} đỉnh cần kiểm tra (bấm để sửa)`;
        subEl.style.color = "#ffb300";
      } else {
        subEl.innerText = `✅ Dữ liệu nhất quán – không cần sửa`;
        subEl.style.color = "#00e676";
      }
    }
  } catch (e) {
    console.debug("Error fetching correction status:", e);
  }
}

async function triggerRetroactiveCorrect() {
  const confirmed = confirm(
    "⚠️ Chạy Retroactive Correction trên toàn bộ 388+ sự kiện?\n\n" +
    "Quá trình này sẽ:\n" +
    "• Truy vấn Binance ATH cho mỗi sự kiện\n" +
    "• Cập nhật đỉnh sai vào training database\n" +
    "• Tự động retrain mô hình ML Tri-Ensemble v4\n\n" +
    "⏱ Thời gian ước tính: 5-10 phút\n\n" +
    "Tiếp tục?"
  );
  if (!confirmed) return;

  const subEl = document.getElementById("ace-quality-sub");
  const qualityEl = document.getElementById("stat-data-quality");
  if (subEl) subEl.innerText = "⏳ Đang chạy retroactive correction...";
  if (qualityEl) qualityEl.innerText = "...";

  try {
    const res = await fetch("/api/ml/retroactive_correct", { method: "POST" });
    if (!res.ok) {
      if (subEl) subEl.innerText = "❌ Lỗi server";
      return;
    }
    const data = await res.json();
    if (data.status === "success") {
      const r = data.result || {};
      alert(
        `✅ Retroactive Correction Hoàn Tất!\n\n` +
        `• Đã quét: ${r.total_events_scanned || 0} sự kiện\n` +
        `• Đỉnh đã sửa: ${r.corrections_applied || 0}\n` +
        `• Bỏ qua: ${r.skipped || 0}\n` +
        `• Retrain status: ${r.retrain_result?.status || "N/A"}`
      );
      fetchCorrectionStatus();
      fetchBenchmarkLedger();
    }
  } catch (e) {
    console.error("Error triggering retroactive correct:", e);
    if (subEl) subEl.innerText = "❌ Lỗi kết nối";
  }
}



async function fetchGapFillStatus() {
  try {
    const res = await fetch("/api/ml/gap_fill_status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    const badgeText = document.getElementById("offline-sync-text");
    if (badgeText) {
      const summary = data.latest_sync_summary || {};
      if (summary.gap_fill_triggered && summary.downtime_hours > 0) {
        badgeText.innerText = `🟢 Đã bù ${summary.downtime_hours}h máy tắt (${summary.total_klines_analyzed || 0} nến klines)`;
      } else {
        badgeText.innerText = "🟢 Dữ Liệu Xuyên Suốt (Bù Klines Tự Động)";
      }
    }
  } catch (e) {
    console.debug("Error fetching gap fill status:", e);
  }
}


function predictInFlight() {
  return runInteractiveMLPrediction();
}

function setCampaignPage(page) {
  campaignCurrentPage = page;
  renderCampaignsView();
  const el = document.getElementById("campaigns-container");
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function setCampaignPageSize(size) {
  campaignPageSize = Number(size);
  campaignCurrentPage = 1;
  renderCampaignsView();
}

function setDatasetPage(page) {
  datasetCurrentPage = page;
  renderDatasetTable(cachedDatasetEvents);
}

function setDatasetPageSize(size) {
  datasetPageSize = Number(size);
  datasetCurrentPage = 1;
  renderDatasetTable(cachedDatasetEvents);
}

function setLedgerPage(page) {
  ledgerCurrentPage = page;
  renderBenchmarkLedgerTable(cachedLedgerRecords);
}

function setLedgerPageSize(size) {
  ledgerPageSize = Number(size);
  ledgerCurrentPage = 1;
  renderBenchmarkLedgerTable(cachedLedgerRecords);
}

/**
 * Reusable Modern Neon Pagination Generator
 */
function buildPaginationHtml(totalItems, currentPage, pageSize, setPageFnName, setSizeFnName, sizeOptions = [10, 20, 50, 100, 0]) {
  if (totalItems === 0) return "";
  const totalPages = pageSize > 0 ? Math.ceil(totalItems / pageSize) : 1;
  const startIndex = pageSize > 0 ? (currentPage - 1) * pageSize + 1 : 1;
  const endIndex = pageSize > 0 ? Math.min(currentPage * pageSize, totalItems) : totalItems;

  let pageButtonsHtml = "";
  if (totalPages > 1) {
    // First & Prev buttons
    pageButtonsHtml += `
      <button class="page-btn" ${currentPage <= 1 ? "disabled" : ""} onclick="${setPageFnName}(1)" title="Trang đầu">⏮</button>
      <button class="page-btn" ${currentPage <= 1 ? "disabled" : ""} onclick="${setPageFnName}(${currentPage - 1})" title="Trang trước">◀ Trước</button>
    `;

    // Smart sliding window for page numbers (max 7 numbers)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (currentPage <= 3) {
      endPage = Math.min(5, totalPages);
    }
    if (currentPage >= totalPages - 2) {
      startPage = Math.max(1, totalPages - 4);
    }

    if (startPage > 1) {
      pageButtonsHtml += `<button class="page-btn" onclick="${setPageFnName}(1)">1</button>`;
      if (startPage > 2) {
        pageButtonsHtml += `<span style="color: var(--text-dim); padding: 0 4px; font-family: var(--font-mono);">…</span>`;
      }
    }

    for (let p = startPage; p <= endPage; p++) {
      pageButtonsHtml += `
        <button class="page-btn ${p === currentPage ? "active" : ""}" onclick="${setPageFnName}(${p})">${p}</button>
      `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pageButtonsHtml += `<span style="color: var(--text-dim); padding: 0 4px; font-family: var(--font-mono);">…</span>`;
      }
      pageButtonsHtml += `<button class="page-btn" onclick="${setPageFnName}(${totalPages})">${totalPages}</button>`;
    }

    // Next & Last buttons
    pageButtonsHtml += `
      <button class="page-btn" ${currentPage >= totalPages ? "disabled" : ""} onclick="${setPageFnName}(${currentPage + 1})" title="Trang tiếp">Tiếp ▶</button>
      <button class="page-btn" ${currentPage >= totalPages ? "disabled" : ""} onclick="${setPageFnName}(${totalPages})" title="Trang cuối">⏭</button>
    `;
  }

  const sizeOptionsHtml = sizeOptions.map(s => `
    <option value="${s}" ${pageSize === s ? "selected" : ""}>${s === 0 ? "Tất cả" : s}</option>
  `).join("");

  return `
    <div class="pagination-wrapper">
      <div class="pagination-info">
        Hiển thị <strong>${startIndex} - ${endIndex}</strong> trong <strong>${totalItems}</strong> &bull; Trang <strong>${currentPage} / ${totalPages}</strong>
      </div>
      
      ${totalPages > 1 ? `<div class="pagination-nav">${pageButtonsHtml}</div>` : ""}

      <div class="page-size-wrapper">
        <span>Hiển thị:</span>
        <select class="page-size-select" onchange="${setSizeFnName}(Number(this.value))">
          ${sizeOptionsHtml}
        </select>
        <span>dòng/trang</span>
      </div>
    </div>
  `;
}

function setCampaignViewMode(mode) {
  currentCampaignViewMode = mode;
  const listBtn = document.getElementById("campaign-view-list");
  const gridBtn = document.getElementById("campaign-view-grid");
  if (listBtn && gridBtn) {
    if (mode === "LIST") {
      listBtn.classList.add("active");
      gridBtn.classList.remove("active");
    } else {
      gridBtn.classList.add("active");
      listBtn.classList.remove("active");
    }
  }
  renderCampaignsView();
}

function setCampaignSearch(query) {
  currentCampaignSearchQuery = (query || "").trim().toUpperCase();
  campaignCurrentPage = 1; // Reset to page 1 on search
  renderCampaignsView();
}

function setCampaignFilter(filter) {
  currentCampaignFilter = filter;
  campaignCurrentPage = 1; // Reset to page 1 on filter switch
  ["active", "dumped", "all"].forEach(t => {
    const btn = document.getElementById(`campaign-filter-${t}`);
    if (btn) {
      if (t === filter.toLowerCase()) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    }
  });
  renderCampaignsView();
}

function setCampaignSort(sortBy) {
  currentCampaignSort = sortBy;
  campaignCurrentPage = 1; // Reset to page 1 on sort switch
  const sel = document.getElementById("campaign-sort-select");
  if (sel && sel.value !== sortBy) {
    for (let opt of sel.options) {
      if (opt.value === sortBy) {
        sel.value = sortBy;
        break;
      }
    }
  }
  renderCampaignsView();
}

function toggleCampaignDetails(rowId) {
  const detailsRow = document.getElementById(`details-${rowId}`);
  const icon = document.getElementById(`icon-${rowId}`);
  if (!detailsRow) return;
  if (detailsRow.style.display === "none" || detailsRow.style.display === "") {
    detailsRow.style.display = "table-row";
    if (icon) icon.innerText = "▲";
  } else {
    detailsRow.style.display = "none";
    if (icon) icon.innerText = "▼";
  }
}


async function fetchCampaignsData() {
  try {
    const res = await fetch("/api/ml/active_pump_campaigns");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    cachedCampaignsData = data;
    
    // Update KPI counters
    const activeCount = data.active_count || (data.active_campaigns ? data.active_campaigns.length : 0);
    const activeEl = document.getElementById("stat-active-count");
    if (activeEl) activeEl.innerText = activeCount;

    const scatterActiveEl = document.getElementById("scatter-active-count");
    if (scatterActiveEl) scatterActiveEl.innerText = activeCount;

    const all = data.all_campaigns || [];
    const dumpedCount = all.filter(c => !c.is_active || c.stage === "DUMP_CONFIRMED").length;
    const dumpedEl = document.getElementById("stat-dumped-count");
    if (dumpedEl) dumpedEl.innerText = dumpedCount;

    populateMLSymbolSelect(all);
    renderCampaignsView();

    if (cachedResearchData && cachedResearchData.events) {
      renderScatterCanvas(cachedResearchData.events);
    }
  } catch (e) {


    console.debug("Error fetching campaigns data:", e);
  }
}

function populateMLSymbolSelect(campaigns) {
  const sel = document.getElementById("ml-pred-symbol-select");
  if (!sel) return;
  const currentVal = sel.value;
  
  const active = (campaigns || []).filter(c => c.is_active && c.stage !== "DUMP_CONFIRMED" && c.stage !== "DELISTED");
  active.sort((a, b) => (b.current_n || 0) - (a.current_n || 0));
  if (active.length === 0) return;
  
  let html = "";
  active.forEach(c => {
    const stageTxt = c.stage === "ACTIVE_EXPANSION" ? "Đang đẩy" : c.stage === "HIGH_CONSOLIDATION" ? "Neo đỉnh" : "Tích lũy";
    const nDisplay = c.max_n ? `${c.max_n}x` : `${c.current_n || 1.0}x`;
    html += `<option value="${c.symbol}">${c.symbol} (${nDisplay} - ${stageTxt})</option>`;
  });
  html += `<option value="CUSTOM">➕ Nhập Mã Khác...</option>`;
  sel.innerHTML = html;
  
  if (currentVal && Array.from(sel.options).some(o => o.value === currentVal)) {
    sel.value = currentVal;
  } else if (Array.from(sel.options).some(o => o.value === "MAGMAUSDT")) {
    sel.value = "MAGMAUSDT";
  }
}


function renderCampaignsGrid() {
  renderCampaignsView();
}

function renderCampaignsView() {
  if (!cachedCampaignsData) return;

  const all = cachedCampaignsData.all_campaigns || [];
  let displayCampaigns = [];

  if (currentCampaignFilter === "ACTIVE") {
    displayCampaigns = all.filter(c => c.is_active && c.stage !== "DUMP_CONFIRMED");
  } else if (currentCampaignFilter === "DUMPED") {
    displayCampaigns = all.filter(c => !c.is_active || c.stage === "DUMP_CONFIRMED");
  } else {
    displayCampaigns = all;
  }

  // Apply Quick Search Filter if present
  if (currentCampaignSearchQuery) {
    displayCampaigns = displayCampaigns.filter(c => 
      (c.symbol || "").toUpperCase().includes(currentCampaignSearchQuery) ||
      (c.notes || "").toUpperCase().includes(currentCampaignSearchQuery) ||
      (c.origin_date || "").includes(currentCampaignSearchQuery)
    );
  }

  // Precompute metrics & sorting keys
  displayCampaigns.forEach(c => {
    const mlPred = c.ml_prediction || {};
    const nLow = mlPred.n_low || c.expected_n_low || 5.0;
    const nHigh = mlPred.n_high || c.expected_n_high || 20.0;
    const nExp = mlPred.n_expected || c.expected_n_ml || ((nLow + nHigh) / 2) || 10.0;

    const effectiveN = c.is_active ? (c.current_n || 1.0) : (c.max_n || c.current_n || 1.0);
    const progressPct = mlPred.progress_pct !== undefined ? mlPred.progress_pct : Math.round((effectiveN / Math.max(nExp, 0.1)) * 1000) / 10;
    
    c._progressPct = progressPct;
    c._maxN = c.max_n || c.current_n || 1.0;
    c._currentN = c.current_n || 1.0;
    c._drawdown = c.drawdown_from_peak_pct || 0.0;
    c._nExp = nExp;
    c._nLow = nLow;
    c._nHigh = nHigh;
  });

  // Sort by selected criteria
  if (currentCampaignSort === "PROGRESS_DESC") {
    displayCampaigns.sort((a, b) => b._progressPct - a._progressPct);
  } else if (currentCampaignSort === "PROGRESS_ASC") {
    displayCampaigns.sort((a, b) => a._progressPct - b._progressPct);
  } else if (currentCampaignSort === "MAX_N_DESC") {
    displayCampaigns.sort((a, b) => b._maxN - a._maxN);
  } else if (currentCampaignSort === "CURRENT_N_DESC") {
    displayCampaigns.sort((a, b) => b._currentN - a._currentN);
  } else if (currentCampaignSort === "DRAWDOWN_DESC" || currentCampaignSort === "DRAWDOWN") {
    displayCampaigns.sort((a, b) => b._drawdown - a._drawdown);
  } else if (currentCampaignSort === "SYMBOL") {
    displayCampaigns.sort((a, b) => a.symbol.localeCompare(b.symbol));
  } else if (currentCampaignSort === "DATE_DESC") {
    displayCampaigns.sort((a, b) => (b.origin_date || '').localeCompare(a.origin_date || ''));
  }

  const container = document.getElementById("campaigns-container") || document.getElementById("campaigns-grid");
  if (!container) return;

  if (displayCampaigns.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-dim); padding: 36px; background: rgba(0,0,0,0.25); border-radius: 8px; border: 1px dashed rgba(0,240,255,0.2);">
        ${currentCampaignSearchQuery ? `Không tìm thấy coin nào khớp với từ khóa "<strong>${currentCampaignSearchQuery}</strong>".` : (currentCampaignFilter === 'ACTIVE' ? 'Hiện tại chưa có thêm siêu sóng nào khác đang trong pha đẩy/neo đỉnh.' : 'Chưa có chiến dịch nào trong mục này.')}
      </div>
    `;
    return;
  }

  // ── PAGINATION CALCULATION ──────────────────────────────────────────
  const totalCampaigns = displayCampaigns.length;
  const totalPages = campaignPageSize > 0 ? Math.ceil(totalCampaigns / campaignPageSize) : 1;
  if (campaignCurrentPage > totalPages) campaignCurrentPage = Math.max(1, totalPages);
  const startIndex = campaignPageSize > 0 ? (campaignCurrentPage - 1) * campaignPageSize : 0;
  const endIndex = campaignPageSize > 0 ? Math.min(startIndex + campaignPageSize, totalCampaigns) : totalCampaigns;
  const paginatedCampaigns = campaignPageSize > 0 ? displayCampaigns.slice(startIndex, endIndex) : displayCampaigns;
  const paginationHtml = buildPaginationHtml(totalCampaigns, campaignCurrentPage, campaignPageSize, 'setCampaignPage', 'setCampaignPageSize');

  // ── RENDER DENSE LIST VIEW (DEFAULT) ─────────────────────────────────
  if (currentCampaignViewMode === "LIST") {
    container.innerHTML = `
      <div style="overflow-x: auto; border-radius: 8px 8px 0 0; border: 1px solid rgba(0, 240, 255, 0.25); border-bottom: none; background: rgba(11, 15, 23, 0.9); box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
        <table class="styled-table" style="width: 100%; border-collapse: collapse; min-width: 1100px; font-size: 0.84rem;">
          <thead>
            <tr style="background: linear-gradient(90deg, rgba(0, 240, 255, 0.12) 0%, rgba(18, 24, 36, 0.8) 100%); border-bottom: 2px solid rgba(0, 240, 255, 0.35);">
              <th style="padding: 10px 12px; color: var(--accent-cyan); font-weight: 700; width: 45px; text-align: center;">#</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; cursor: pointer;" onclick="setCampaignSort('SYMBOL')" title="Bấm để sắp xếp">MÃ COIN / KHỞI PHÁT ⬍</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: center;">TRẠNG THÁI</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: right;">ĐÁY GỐC (BASE)</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: right; cursor: pointer;" onclick="setCampaignSort('MAX_N_DESC')" title="Bấm để sắp xếp">ĐỈNH CAO (PEAK) ⬍</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: right; cursor: pointer;" onclick="setCampaignSort('CURRENT_N_DESC')" title="Bấm để sắp xếp">GIÁ HIỆN TẠI ⬍</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: right; cursor: pointer;" onclick="setCampaignSort('DRAWDOWN_DESC')" title="Bấm để sắp xếp">SỤT TỪ ĐỈNH ⬍</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: center;">DẢI ĐỈNH ML (90% CI)</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; min-width: 215px; cursor: pointer;" onclick="setCampaignSort('PROGRESS_DESC')" title="Bấm để sắp xếp">TIẾN ĐỘ &amp; GIÁ ĐÍCH 100% ⬍</th>
              <th style="padding: 10px 14px; color: var(--accent-cyan); font-weight: 700; text-align: center;">CẮT DUMP</th>
              <th style="padding: 10px 12px; color: var(--accent-cyan); font-weight: 700; text-align: center; width: 110px;">THAO TÁC</th>
            </tr>
          </thead>
          <tbody>
            ${paginatedCampaigns.map((c, idx) => {
              const bottomFmt = c.origin_bottom_price < 0.001 ? c.origin_bottom_price.toFixed(8) : c.origin_bottom_price < 1 ? c.origin_bottom_price.toFixed(5) : c.origin_bottom_price.toFixed(2);
              const peakFmt = c.highest_peak_price < 0.001 ? c.highest_peak_price.toFixed(8) : c.highest_peak_price < 1 ? c.highest_peak_price.toFixed(5) : c.highest_peak_price.toFixed(2);
              const currFmt = c.current_price < 0.001 ? c.current_price.toFixed(8) : c.current_price < 1 ? c.current_price.toFixed(5) : c.current_price.toFixed(2);
              const dumpFmt = c.dump_threshold_price < 0.001 ? c.dump_threshold_price.toFixed(8) : c.dump_threshold_price < 1 ? c.dump_threshold_price.toFixed(5) : c.dump_threshold_price.toFixed(2);

              let stageColor = "var(--accent-cyan)";
              let stageBg = "rgba(0, 240, 255, 0.08)";
              if (c.stage === "ACTIVE_EXPANSION") {
                stageColor = "var(--accent-yellow)";
                stageBg = "rgba(255, 184, 0, 0.12)";
              } else if (c.stage === "HIGH_CONSOLIDATION") {
                stageColor = "var(--accent-green)";
                stageBg = "rgba(0, 230, 118, 0.12)";
              } else if (c.stage === "EXHAUSTION_WARNING") {
                stageColor = "var(--accent-orange)";
                stageBg = "rgba(255, 102, 0, 0.12)";
              } else if (c.stage === "DUMP_CONFIRMED") {
                stageColor = "var(--accent-red)";
                stageBg = "rgba(255, 51, 102, 0.12)";
              } else if (c.stage === "DELISTED") {
                stageColor = "var(--text-muted)";
                stageBg = "rgba(255, 255, 255, 0.05)";
              }

              const mlPred = c.ml_prediction || {};
              const nLow = mlPred.n_low || c.expected_n_low || 5.0;
              const nHigh = mlPred.n_high || c.expected_n_high || 20.0;
              const nExp = mlPred.n_expected || c.expected_n_ml || ((nLow + nHigh) / 2);

              const priceLow = mlPred.target_price_low || (c.origin_bottom_price * nLow);
              const priceHigh = mlPred.target_price_high || (c.origin_bottom_price * nHigh);
              const priceExp = mlPred.target_peak_price || (c.origin_bottom_price * nExp);

              const priceLowFmt = priceLow < 0.0001 ? priceLow.toFixed(8) : priceLow < 0.01 ? priceLow.toFixed(6) : priceLow < 1 ? priceLow.toFixed(4) : priceLow.toFixed(2);
              const priceHighFmt = priceHigh < 0.0001 ? priceHigh.toFixed(8) : priceHigh < 0.01 ? priceHigh.toFixed(6) : priceHigh < 1 ? priceHigh.toFixed(4) : priceHigh.toFixed(2);
              const priceExpFmt = priceExp < 0.0001 ? priceExp.toFixed(8) : priceExp < 0.01 ? priceExp.toFixed(6) : priceExp < 1 ? priceExp.toFixed(4) : priceExp.toFixed(2);
              const actualProgressPct = Math.round(((c.is_active ? c.current_n : c.max_n) / nExp) * 100);
              const isExceeded = actualProgressPct > 100;
              const upsidePct = mlPred.remaining_upside_pct !== undefined ? mlPred.remaining_upside_pct : Math.max(0, Math.round(((priceExp - c.current_price) / c.current_price) * 100));

              const rowNumber = startIndex + idx + 1;
              const rowId = `camp-row-${rowNumber}`;
              const isEven = idx % 2 === 0;

              return `
                <tr style="background: ${isEven ? 'rgba(255,255,255,0.015)' : 'transparent'}; border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.15s ease; cursor: pointer;"
                    onclick="window.selectScatterSymbol('${c.symbol}')"
                    title="Click để định vị tâm ngắm ML trên biểu đồ phân tán"
                    onmouseover="this.style.background='rgba(0, 240, 255, 0.07)'"
                    onmouseout="this.style.background='${isEven ? 'rgba(255,255,255,0.015)' : 'transparent'}'">
                  <!-- Index -->
                  <td style="padding: 11px 12px; text-align: center; color: var(--text-dim); font-family: var(--font-mono); font-size: 0.78rem;">
                    ${rowNumber}
                  </td>


                  <!-- Symbol & Launch Date -->
                  <td style="padding: 11px 14px;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                      <a href="/?symbol=${c.symbol}" style="font-weight: 800; font-size: 0.96rem; color: #fff; text-decoration: none; font-family: var(--font-mono);" title="Mở biểu đồ TradingView Live">
                        ${c.symbol}
                      </a>
                      ${c.is_active ? '<span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #00e676; box-shadow: 0 0 6px #00e676;"></span>' : ''}
                      ${c.pattern_type === 'VOLUME_IGNITION' ? '<span style="font-size: 0.65rem; padding: 1px 5px; border-radius: 3px; background: rgba(255,102,0,0.2); color: #ff6600; border: 1px solid rgba(255,102,0,0.4); font-weight: 700;">🔥 IGNITION</span>' : ''}
                      ${c.pattern_type === 'STEALTH_CLIMBER' ? '<span style="font-size: 0.65rem; padding: 1px 5px; border-radius: 3px; background: rgba(0,230,118,0.2); color: #00e676; border: 1px solid rgba(0,230,118,0.4); font-weight: 700;">🐢 STEALTH</span>' : ''}
                    </div>
                    <div style="font-size: 0.72rem; color: var(--text-dim);">
                      ${c.origin_date} • ${c.pump_age_days || 1} ngày
                    </div>
                  </td>


                  <!-- Stage Badge -->
                  <td style="padding: 11px 14px; text-align: center;">
                    <span style="display: inline-block; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; background: ${stageBg}; color: ${stageColor}; font-weight: 700; border: 1px solid ${stageColor}; white-space: nowrap;">
                      ${c.stage_label_vi || c.stage}
                    </span>
                  </td>

                  <!-- Base Price -->
                  <td style="padding: 11px 14px; text-align: right; font-family: var(--font-mono);">
                    <strong style="color: var(--accent-cyan); font-size: 0.88rem;">$${bottomFmt}</strong>
                  </td>

                  <!-- Peak Price & Max Multiplier -->
                  <td style="padding: 11px 14px; text-align: right; font-family: var(--font-mono);">
                    <strong style="color: var(--accent-yellow); font-size: 0.88rem;">$${peakFmt}</strong>
                    <div style="font-size: 0.74rem; color: var(--accent-yellow); font-weight: 700;">${c.max_n}x</div>
                  </td>

                  <!-- Current Price & Multiplier -->
                  <td style="padding: 11px 14px; text-align: right; font-family: var(--font-mono);">
                    <strong style="color: #fff; font-size: 0.88rem;">$${currFmt}</strong>
                    <div style="font-size: 0.74rem; color: var(--accent-cyan);">${c.current_n}x</div>
                  </td>

                  <!-- Drawdown -->
                  <td style="padding: 11px 14px; text-align: right; font-family: var(--font-mono);">
                    <strong style="color: ${c.drawdown_from_peak_pct >= 35 ? 'var(--accent-red)' : 'var(--accent-green)'}; font-size: 0.88rem;">
                      -${c.drawdown_from_peak_pct}%
                    </strong>
                  </td>

                  <!-- ML Expected Range (90% CI) -->
                  <td style="padding: 11px 14px; text-align: center; font-family: var(--font-mono);">
                    <div style="color: var(--accent-yellow); font-weight: 700; font-size: 0.88rem;">
                      ${nLow.toFixed(1)}x &rarr; ${nHigh.toFixed(1)}x
                    </div>
                    <div style="font-size: 0.72rem; color: ${isExceeded ? '#ff007a' : '#fff'}; font-weight: 600;">
                      ${isExceeded ? 'Đích Gốc:' : 'Đích 100%:'} <strong style="color: ${isExceeded ? '#ffb800' : 'var(--accent-cyan)'}; font-size: 0.78rem;">$${priceExpFmt}</strong> <span style="color: var(--text-dim);">(${nExp.toFixed(1)}x)</span>
                    </div>
                    <div style="font-size: 0.68rem; color: var(--text-dim);">
                      Dải: $${priceLowFmt} &rarr; $${priceHighFmt}
                    </div>
                  </td>

                  <!-- ML Progress Bar & 100% Target Price -->
                  <td style="padding: 11px 14px; min-width: 220px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.73rem; margin-bottom: 3px; font-family: var(--font-mono);">
                      <span style="color: ${isExceeded ? '#ff007a' : '#fff'}; font-weight: 700;">
                        ${actualProgressPct}% ${isExceeded ? `<span style="font-size: 0.68rem; color: #ff007a;">(VƯỢT ĐÍCH ${nExp.toFixed(1)}x)</span>` : `<span style="color: var(--text-dim); font-weight: normal;">(${c.is_active ? c.current_n : c.max_n}x / ${nExp.toFixed(1)}x)</span>`}
                      </span>
                      <span style="color: ${isExceeded ? '#ff007a' : (c.is_active ? (upsidePct > 0 ? 'var(--accent-green)' : 'var(--accent-red)') : (actualProgressPct >= 100 ? 'var(--accent-green)' : 'var(--accent-yellow)'))}; font-weight: 700;">
                        ${isExceeded ? `+${actualProgressPct - 100}% Vượt Đích` : (c.is_active ? (upsidePct > 0 ? `+${upsidePct}%` : 'Chạm đỉnh') : (actualProgressPct >= 100 ? 'Đạt Target' : 'Hoàn tất'))}
                      </span>
                    </div>
                    <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; margin-bottom: 4px;">
                      <div style="width: ${Math.min(100, actualProgressPct)}%; height: 100%; background: ${isExceeded ? 'linear-gradient(90deg, #00e676 0%, #00f0ff 40%, #ff007a 100%)' : (actualProgressPct >= 100 ? 'linear-gradient(90deg, #00e676 0%, #00f0ff 100%)' : 'linear-gradient(90deg, #00e676 0%, #00f0ff 70%, #ffb800 100%)')}; border-radius: 3px;"></div>
                    </div>
                    ${isExceeded ? `
                      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.70rem; font-family: var(--font-mono); background: rgba(255, 0, 122, 0.12); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255, 0, 122, 0.35);">
                        <span style="color: #ffb800;">🎯 Đích Gốc (${nExp.toFixed(1)}x): <strong>$${priceExpFmt}</strong></span>
                        <strong style="color: #ff007a; font-size: 0.72rem;">ĐÃ VƯỢT (${c.is_active ? c.current_n : c.max_n}x)</strong>
                      </div>
                    ` : `
                      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem; font-family: var(--font-mono); background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255, 184, 0, 0.2);">
                        <span style="color: var(--text-dim);">🎯 Giá Khi Đầy 100%:</span>
                        <strong style="color: var(--accent-yellow); font-size: 0.82rem;">$${priceExpFmt}</strong>
                      </div>
                    `}
                  </td>

                  <!-- Dump Stop Price -->
                  <td style="padding: 11px 14px; text-align: center; font-family: var(--font-mono); font-size: 0.82rem;">
                    <strong style="color: var(--accent-red);">$${dumpFmt}</strong>
                  </td>

                  <!-- Actions -->
                  <td style="padding: 11px 12px; text-align: center;">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 4px;">
                      <a href="/?symbol=${c.symbol}" class="btn-inspect" style="padding: 4px 8px; font-size: 0.72rem;" title="Mở biểu đồ TradingView">
                        Soi Nến
                      </a>
                      <button onclick="toggleCampaignDetails('${rowId}')" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: var(--accent-cyan); padding: 4px 6px; border-radius: 4px; cursor: pointer; font-size: 0.68rem;" title="Xem chi tiết phân tích">
                        <span id="icon-${rowId}">▼</span>
                      </button>
                    </div>
                  </td>
                </tr>

                <!-- Collapsible Detailed Notes Row -->
                <tr id="details-${rowId}" style="display: none; background: rgba(0, 240, 255, 0.03); border-bottom: 1px solid rgba(0, 240, 255, 0.2);">
                  <td colspan="11" style="padding: 10px 18px; font-size: 0.78rem; color: var(--text-dim); line-height: 1.5;">
                    <div style="display: flex; gap: 16px; flex-wrap: wrap; align-items: center;">
                      <div style="flex: 1; min-width: 280px;">
                        <strong style="color: var(--accent-cyan);">Phân Tích Sóng &amp; Động Lực:</strong> ${c.notes || 'Không có ghi chú thêm.'}
                      </div>
                      <div style="font-family: var(--font-mono); font-size: 0.75rem; background: rgba(0,0,0,0.35); padding: 6px 14px; border-radius: 4px; border: 1px solid rgba(0, 240, 255, 0.25);">
                        🎯 Giá Đầy 100% (Med ${nExp.toFixed(1)}x): <strong style="color: var(--accent-yellow); font-size: 0.88rem;">$${priceExpFmt}</strong> &bull; Dải 90% CI: <strong style="color: #fff;">$${priceLowFmt} &rarr; $${priceHighFmt}</strong>
                      </div>
                    </div>
                  </td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
      </div>
      ${paginationHtml}
    `;
    return;
  }

  // ── RENDER CARD GRID VIEW (ALTERNATIVE) ──────────────────────────────
  container.innerHTML = `
    <div id="campaigns-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 16px;">
      ${paginatedCampaigns.map(c => {
        const bottomFmt = c.origin_bottom_price < 0.001 ? c.origin_bottom_price.toFixed(8) : c.origin_bottom_price < 1 ? c.origin_bottom_price.toFixed(4) : c.origin_bottom_price.toFixed(2);
        const peakFmt = c.highest_peak_price < 0.001 ? c.highest_peak_price.toFixed(8) : c.highest_peak_price < 1 ? c.highest_peak_price.toFixed(4) : c.highest_peak_price.toFixed(2);
        const currFmt = c.current_price < 0.001 ? c.current_price.toFixed(8) : c.current_price < 1 ? c.current_price.toFixed(4) : c.current_price.toFixed(2);
        const dumpFmt = c.dump_threshold_price < 0.001 ? c.dump_threshold_price.toFixed(8) : c.dump_threshold_price < 1 ? c.dump_threshold_price.toFixed(4) : c.dump_threshold_price.toFixed(2);

        let stageColor = "var(--accent-cyan)";
        let borderGlow = "border: 1px solid rgba(0, 240, 255, 0.3);";
        if (c.stage === "ACTIVE_EXPANSION") {
          stageColor = "var(--accent-yellow)";
          borderGlow = "border: 1px solid rgba(255, 184, 0, 0.4); box-shadow: 0 0 15px rgba(255, 184, 0, 0.1);";
        } else if (c.stage === "HIGH_CONSOLIDATION") {
          stageColor = "var(--accent-green)";
          borderGlow = "border: 1px solid rgba(0, 230, 118, 0.35);";
        } else if (c.stage === "EXHAUSTION_WARNING") {
          stageColor = "var(--accent-orange)";
          borderGlow = "border: 1px solid rgba(255, 102, 0, 0.4);";
        } else if (c.stage === "DUMP_CONFIRMED") {
          stageColor = "var(--accent-red)";
          borderGlow = "border: 1px solid rgba(255, 51, 102, 0.4); background: rgba(255, 51, 102, 0.02);";
        } else if (c.stage === "DELISTED") {
          stageColor = "var(--text-muted)";
          borderGlow = "border: 1px solid rgba(255, 255, 255, 0.1);";
        }

        const mlPred = c.ml_prediction || {};
        const nLow = mlPred.n_low || c.expected_n_low || 5.0;
        const nHigh = mlPred.n_high || c.expected_n_high || 20.0;
        const nExp = mlPred.n_expected || c.expected_n_ml || ((nLow + nHigh) / 2);

        const priceLow = mlPred.target_price_low || (c.origin_bottom_price * nLow);
        const priceHigh = mlPred.target_price_high || (c.origin_bottom_price * nHigh);
        const priceExp = mlPred.target_peak_price || (c.origin_bottom_price * nExp);

        const priceLowFmt = priceLow < 0.0001 ? priceLow.toFixed(8) : priceLow < 0.01 ? priceLow.toFixed(6) : priceLow < 1 ? priceLow.toFixed(4) : priceLow.toFixed(2);
        const priceHighFmt = priceHigh < 0.0001 ? priceHigh.toFixed(8) : priceHigh < 0.01 ? priceHigh.toFixed(6) : priceHigh < 1 ? priceHigh.toFixed(4) : priceHigh.toFixed(2);
        const priceExpFmt = priceExp < 0.0001 ? priceExp.toFixed(8) : priceExp < 0.01 ? priceExp.toFixed(6) : priceExp < 1 ? priceExp.toFixed(4) : priceExp.toFixed(2);

        const actualProgressPct = Math.round(((c.is_active ? c.current_n : c.max_n) / nExp) * 100);
        const isExceeded = actualProgressPct > 100;
        const upsidePct = mlPred.remaining_upside_pct !== undefined ? mlPred.remaining_upside_pct : Math.max(0, Math.round(((priceExp - c.current_price) / c.current_price) * 100));

        return `
          <div style="background: rgba(11, 15, 23, 0.85); border-radius: 8px; padding: 16px; ${borderGlow} display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <!-- Header -->
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                <div>
                  <a href="/?symbol=${c.symbol}" style="font-size: 1.2rem; font-weight: 800; color: #fff; text-decoration: none;" title="Soi Nến ${c.symbol}">
                    ${c.symbol}
                  </a>
                  <div style="font-size: 0.74rem; color: var(--text-dim);">Khởi phát: ${c.origin_date} (${c.pump_age_days || 1} ngày trước)</div>
                </div>
                <span style="font-size: 0.74rem; padding: 4px 9px; border-radius: 4px; background: rgba(255, 255, 255, 0.05); color: ${stageColor}; font-weight: 700; border: 1px solid ${stageColor};">
                  ${c.stage_label_vi || c.stage}
                </span>
              </div>

              <!-- Multipliers Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: rgba(0, 0, 0, 0.28); padding: 12px; border-radius: 6px; margin-bottom: 10px; font-family: var(--font-mono); font-size: 0.82rem;">
                <div>
                  <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">ĐÁY GỐC (BASE):</span>
                  <strong style="color: var(--accent-cyan); font-size: 0.9rem;">$${bottomFmt}</strong>
                </div>
                <div>
                  <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">ĐỈNH CAO (PEAK):</span>
                  <strong style="color: var(--accent-yellow); font-size: 0.9rem;">$${peakFmt} <span style="font-size: 0.74rem;">(${c.max_n}x)</span></strong>
                </div>
                <div>
                  <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">GIÁ HIỆN TẠI:</span>
                  <strong style="color: #fff; font-size: 0.9rem;">$${currFmt} <span style="font-size: 0.74rem; color: var(--accent-cyan);">(${c.current_n}x)</span></strong>
                </div>
                <div>
                  <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">SỤT TỪ ĐỈNH:</span>
                  <strong style="color: ${c.drawdown_from_peak_pct >= 35 ? 'var(--accent-red)' : 'var(--accent-green)'}; font-size: 0.9rem;">-${c.drawdown_from_peak_pct}%</strong>
                </div>
              </div>

              <!-- ML Multiplier Targets Box -->
              <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 4px;">
                  <span style="color: var(--accent-cyan); font-weight: 700;">DỰ BÁO ML (90% CI):</span>
                  <strong style="color: var(--accent-yellow); font-family: var(--font-mono);">${nLow.toFixed(1)}x &rarr; ${nHigh.toFixed(1)}x</strong>
                </div>
                <div style="font-size: 0.74rem; color: var(--text-dim); margin-bottom: 6px;">
                  Mục Tiêu: <strong style="color: #fff;">$${priceLowFmt} &rarr; $${priceHighFmt}</strong>
                </div>

                <!-- Progress Bar -->
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; margin-bottom: 2px;">
                  <span style="color: ${isExceeded ? '#ff007a' : 'var(--text-dim)'}; font-weight: ${isExceeded ? '700' : 'normal'};">
                    ${actualProgressPct}% ${isExceeded ? `(VƯỢT ĐÍCH ${nExp.toFixed(1)}x)` : 'Tiến độ'}
                  </span>
                  <span style="color: ${isExceeded ? '#ff007a' : (c.is_active ? (upsidePct > 0 ? 'var(--accent-green)' : 'var(--accent-red)') : (actualProgressPct >= 100 ? 'var(--accent-green)' : 'var(--accent-yellow)'))}; font-weight: 700;">
                    ${isExceeded ? `+${actualProgressPct - 100}% Vượt Đích` : (c.is_active ? (upsidePct > 0 ? `+${upsidePct}% Dư Địa` : 'Chạm Target') : (actualProgressPct >= 100 ? 'Đạt Target' : 'Hoàn tất'))}
                  </span>
                </div>
                <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; margin-bottom: 6px;">
                  <div style="width: ${Math.min(100, actualProgressPct)}%; height: 100%; background: ${isExceeded ? 'linear-gradient(90deg, #00e676 0%, #00f0ff 40%, #ff007a 100%)' : (actualProgressPct >= 100 ? 'linear-gradient(90deg, #00e676 0%, #00f0ff 100%)' : 'linear-gradient(90deg, #00e676 0%, #00f0ff 70%, #ffb800 100%)')}; border-radius: 3px;"></div>
                </div>

                <!-- Explicit 100% Target Price Row in Cards -->
                ${isExceeded ? `
                  <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: rgba(255, 0, 122, 0.12); border-radius: 4px; border: 1px solid rgba(255, 0, 122, 0.35);">
                    <span style="color: #ffb800; font-size: 0.72rem;">🎯 Đích Gốc (${nExp.toFixed(1)}x): <strong>$${priceExpFmt}</strong></span>
                    <strong style="color: #ff007a; font-family: var(--font-mono); font-size: 0.84rem;">ĐÃ VƯỢT (${c.is_active ? c.current_n : c.max_n}x)</strong>
                  </div>
                ` : `
                  <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: rgba(0,0,0,0.3); border-radius: 4px; border: 1px solid rgba(255, 184, 0, 0.25);">
                    <span style="color: var(--text-dim); font-size: 0.72rem;">🎯 Giá Khi Đầy 100% (Med):</span>
                    <strong style="color: var(--accent-yellow); font-family: var(--font-mono); font-size: 0.88rem;">$${priceExpFmt}</strong>
                  </div>
                `}
              </div>

              <div style="font-size: 0.76rem; color: var(--text-dim); line-height: 1.4; margin-bottom: 10px;">
                ${c.notes || ''}
              </div>
            </div>

            <!-- Bottom Warning / Trailing -->
            <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid rgba(255, 255, 255, 0.06); padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
              <span>Ngưỡng Cắt Dump: <strong style="color: var(--accent-red);">$${dumpFmt}</strong></span>
              <a href="/?symbol=${c.symbol}" class="btn-inspect" style="padding: 4px 10px; font-size: 0.74rem;" title="Mở biểu đồ TradingView">
                Soi Nến
              </a>
            </div>
          </div>
        `;
      }).join("")}
    </div>
    ${paginationHtml}
  `;
}

function onMLSelectCampaign(symbol) {
  const customBox = document.getElementById("ml-custom-input-box");
  if (symbol === "CUSTOM") {
    if (customBox) customBox.style.display = "block";
    return;
  }
  if (customBox) customBox.style.display = "none";
  runInteractiveMLPrediction();
}


async function runInteractiveMLPrediction() {
  try {
    const sel = document.getElementById("ml-pred-symbol-select");
    let sym = sel ? sel.value : "BTRUSDT";
    if (sym === "CUSTOM") {
      const customIn = document.getElementById("ml-pred-custom-sym");
      sym = (customIn && customIn.value.trim()) ? customIn.value.trim().toUpperCase() : "BTRUSDT";
    }
    if (!sym.endsWith("USDT") && !sym.endsWith("BUSD") && !sym.endsWith("USDC")) {
      sym += "USDT";
    }

    const res = await fetch(`/api/ml/predict_pump_multiplier?symbol=${encodeURIComponent(sym)}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success" || !data.prediction) return;

    const p = data.prediction;
    const live = data.live_metrics || {};

    // 1. Update Live Binance Metric Stat Displays (Read-Only)
    const baseEl = document.getElementById("ml-live-base-price");
    if (baseEl) {
      const bFmt = p.base_price < 0.001 ? p.base_price.toFixed(8) : p.base_price < 1 ? p.base_price.toFixed(5) : p.base_price.toFixed(2);
      baseEl.innerText = `$${bFmt}`;
    }

    const currEl = document.getElementById("ml-live-curr-price");
    if (currEl) {
      const cFmt = p.current_price < 0.001 ? p.current_price.toFixed(8) : p.current_price < 1 ? p.current_price.toFixed(5) : p.current_price.toFixed(2);
      currEl.innerText = `$${cFmt}`;
    }

    const volEl = document.getElementById("ml-live-vol-spike");
    if (volEl) {
      volEl.innerText = `${p.vol_spike_ratio ? p.vol_spike_ratio.toFixed(1) : '10.0'}x`;
    }

    const fundEl = document.getElementById("ml-live-funding");
    if (fundEl) {
      const fPct = p.funding_rate_pct !== undefined ? p.funding_rate_pct : (p.funding_rate * 100.0);
      fundEl.innerText = `${fPct >= 0 ? '+' : ''}${fPct.toFixed(2)}%`;
      fundEl.style.color = fPct <= -0.5 ? "var(--accent-red)" : fPct < 0 ? "var(--accent-yellow)" : "var(--accent-cyan)";
    }

    // 2. Update Result Display Card
    const symEl = document.getElementById("ml-pred-res-sym");
    if (symEl) symEl.innerText = p.symbol;

    const tierEl = document.getElementById("ml-pred-res-tier");
    if (tierEl) tierEl.innerText = `Phân Khúc Giá: ${p.price_tier_label} (${p.price_tier_code})`;

    const stageEl = document.getElementById("ml-pred-res-stage");
    if (stageEl) {
      stageEl.innerText = p.stage_recommendation;
      if (p.risk_level === "LOW_RISK") {
        stageEl.style.borderColor = "var(--accent-green)";
        stageEl.style.color = "var(--accent-green)";
        stageEl.style.background = "rgba(0, 230, 118, 0.15)";
      } else if (p.risk_level === "MEDIUM_RISK") {
        stageEl.style.borderColor = "var(--accent-yellow)";
        stageEl.style.color = "var(--accent-yellow)";
        stageEl.style.background = "rgba(255, 184, 0, 0.15)";
      } else if (p.risk_level === "HIGH_RISK") {
        stageEl.style.borderColor = "var(--accent-orange)";
        stageEl.style.color = "var(--accent-orange)";
        stageEl.style.background = "rgba(255, 102, 0, 0.15)";
      } else {
        stageEl.style.borderColor = "var(--accent-red)";
        stageEl.style.color = "var(--accent-red)";
        stageEl.style.background = "rgba(255, 51, 102, 0.15)";
      }
    }

    const currNEl = document.getElementById("ml-pred-res-curr-n");
    if (currNEl) currNEl.innerText = `${p.current_n.toFixed(2)}x`;

    const subCurrEl = document.getElementById("ml-pred-res-curr-price-sub");
    if (subCurrEl) {
      const cFmt = p.current_price < 0.001 ? p.current_price.toFixed(8) : p.current_price < 1 ? p.current_price.toFixed(5) : p.current_price.toFixed(2);
      subCurrEl.innerText = `$${cFmt}`;
    }

    const expNEl = document.getElementById("ml-pred-res-exp-n");
    if (expNEl) expNEl.innerText = `${p.n_expected.toFixed(2)}x`;

    const nRangeEl = document.getElementById("ml-pred-res-n-range");
    if (nRangeEl) nRangeEl.innerText = `Dải 90% CI: ${p.n_low.toFixed(1)}x - ${p.n_high.toFixed(1)}x`;

    const targetPriceEl = document.getElementById("ml-pred-res-target-price");
    if (targetPriceEl) {
      const tpFmt = p.target_peak_price < 0.001 ? p.target_peak_price.toFixed(8) : p.target_peak_price < 1 ? p.target_peak_price.toFixed(5) : p.target_peak_price.toFixed(2);
      targetPriceEl.innerText = `$${tpFmt}`;
    }

    const priceRangeEl = document.getElementById("ml-pred-res-price-range");
    if (priceRangeEl) {
      const lowFmt = p.target_price_low < 0.001 ? p.target_price_low.toFixed(8) : p.target_price_low.toFixed(4);
      const highFmt = p.target_price_high < 0.001 ? p.target_price_high.toFixed(8) : p.target_price_high.toFixed(4);
      priceRangeEl.innerText = `$${lowFmt} - $${highFmt}`;
    }

    const upsideEl = document.getElementById("ml-pred-res-upside");
    if (upsideEl) {
      upsideEl.innerText = p.remaining_upside_pct > 0 ? `+${p.remaining_upside_pct}%` : "0.0% (Đạt Đỉnh)";
      upsideEl.style.color = p.remaining_upside_pct > 30 ? "var(--accent-green)" : p.remaining_upside_pct > 0 ? "var(--accent-yellow)" : "var(--accent-red)";
    }

    const progText = document.getElementById("ml-pred-res-progress-text");
    if (progText) {
      if (p.progress_pct > 100) {
        progText.innerHTML = `<span style="color: #ff007a; font-weight: 800;">${p.progress_pct}% (VƯỢT ĐÍCH ${p.n_expected.toFixed(1)}x)</span>`;
      } else {
        progText.innerText = `${p.progress_pct}%`;
      }
    }

    const remText = document.getElementById("ml-pred-res-rem-text");
    if (remText) {
      if (p.progress_pct > 100) {
        remText.innerHTML = `<span style="color: #ff007a; font-weight: 700;">Đã vượt xa mục tiêu ban đầu +${(p.progress_pct - 100).toFixed(1)}%</span>`;
      } else {
        const remPct = Math.max(0, 100 - p.progress_pct);
        remText.innerText = remPct > 0 ? `Còn ${remPct.toFixed(1)}% để chạm mục tiêu ML` : `Đã chạm ngưỡng kỳ vọng`;
      }
    }

    const progBar = document.getElementById("ml-pred-res-progress-bar");
    if (progBar) {
      progBar.style.width = `${Math.min(100, p.progress_pct)}%`;
      if (p.progress_pct > 100) {
        progBar.style.background = 'linear-gradient(90deg, #00e676 0%, #00f0ff 40%, #ff007a 100%)';
        progBar.style.boxShadow = '0 0 12px rgba(255, 0, 122, 0.6)';
      } else {
        progBar.style.background = 'linear-gradient(90deg, #00e676 0%, #00f0ff 70%, #ffb800 100%)';
        progBar.style.boxShadow = 'none';
      }
    }

    const playbookEl = document.getElementById("ml-pred-res-playbook");
    if (playbookEl) {
      const tpFmt = p.target_peak_price < 0.001 ? p.target_peak_price.toFixed(8) : p.target_peak_price < 1 ? p.target_peak_price.toFixed(5) : p.target_peak_price.toFixed(2);
      if (p.progress_pct < 45.0) {
        playbookEl.innerText = `Sóng đang trong pha tăng tốc sớm (tiến độ ${p.progress_pct}%). Dư địa tăng còn lớn (+${p.remaining_upside_pct}%). Khuyến nghị canh các nhịp điều chỉnh pullback để gia tăng vị thế, mục tiêu chốt lời $${tpFmt}.`;
      } else if (p.progress_pct < 80.0) {
        playbookEl.innerText = `Sóng đang trong pha trưởng thành (tiến độ ${p.progress_pct}%). Khuyến nghị giữ vị thế, dời Trailing Stop lên để bảo toàn lợi nhuận và chuẩn bị chốt lời từng phần khi tiệm cận $${tpFmt}.`;
      } else {
        playbookEl.innerText = `Sóng đã tiến sát hoặc nằm trong dải đỉnh kỳ vọng ML (${p.progress_pct}%). Rủi ro đảo chiều/phân phối tăng cao. Khuyến nghị chốt lời phần lớn vị thế và tuyệt đối không mua đuổi vùng giá này.`;
      }
    }

    const featEl = document.getElementById("ml-pred-res-features");
    if (featEl) {
      const fPct = p.funding_rate_pct !== undefined ? p.funding_rate_pct : (p.funding_rate * 100.0);
      featEl.innerHTML = `
        <li>Phân khúc giá ${p.price_tier_code}: Nền tảng kỳ vọng n ≈ ${p.n_low.toFixed(1)}x - ${p.n_high.toFixed(1)}x</li>
        <li>Vol Spike ${p.vol_spike_ratio ? p.vol_spike_ratio.toFixed(1) : '10.0'}x: Mở rộng thanh khoản theo luật lũy thừa Bayesian</li>
        <li>Funding ${fPct >= 0 ? '+' : ''}${fPct.toFixed(2)}%: ${fPct <= -0.5 ? 'Áp lực Short Squeeze kích thích gia tốc bơm mạnh' : 'Funding trung tính'}</li>
      `;
    }

  } catch (err) {
    console.error("Error running ML prediction:", err);
  }
}

async function fetchResearchData() {
  try {
    const res = await fetch("/api/ml/pump_multiplier_research");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    cachedResearchData = data;
    renderScatterCanvas(data.events || []);
    renderTiersGrid(data.tiers || []);
    renderDatasetTable(data.events || []);
  } catch (e) {
    console.debug("Error fetching ML research data:", e);
  }
}

let currentScatterFilter = "ALL";

function setScatterFilter(filter) {
  currentScatterFilter = filter;
  const btnIds = {
    "ALL": "scatter-filter-all",
    "ACTIVE": "scatter-filter-active",
    "OUTLIER": "scatter-filter-outlier",
    "MID": "scatter-filter-mid",
    "BASE": "scatter-filter-base"
  };
  Object.keys(btnIds).forEach(k => {
    const el = document.getElementById(btnIds[k]);
    if (el) {
      if (k === filter) el.classList.add("active");
      else el.classList.remove("active");
    }
  });
  if (cachedResearchData && cachedResearchData.events) {
    renderScatterCanvas(cachedResearchData.events);
  }
}

let scatterPoints = [];
let isScatterHoverAttached = false;

function renderScatterCanvas(events) {
  const canvas = document.getElementById("ml-scatter-canvas");
  if (!canvas) return;

  // 1. Dynamic dataset counter updates
  const scatterCountEl = document.getElementById("scatter-events-count");
  if (scatterCountEl) scatterCountEl.innerText = events.length;
  const scatterCountAllEl = document.getElementById("scatter-count-all");
  if (scatterCountAllEl) scatterCountAllEl.innerText = events.length;
  const datasetCountEl = document.getElementById("dataset-events-count");
  if (datasetCountEl) datasetCountEl.innerText = events.length;

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 2;
  canvas.width = (rect.width || 1100) * dpr;
  canvas.height = (rect.height || 520) * dpr;

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width || 1100;
  const H = rect.height || 520;

  // Deep space background
  ctx.fillStyle = "#0a0f1d";
  ctx.fillRect(0, 0, W, H);

  const padLeft = 85;
  const padRight = 45;
  const padTop = 45;
  const padBottom = 52;

  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBottom;

  // Log Price Range: 1e-5 ($0.00001) to 1e3 ($1000) for ample margin around micro-caps
  const minLogP = Math.log(0.00001);
  const maxLogP = Math.log(1000.0);

  // Log N Range: 1.0 (1x) to 150.0 (150x) for headroom above 94x outliers
  const minLogN = Math.log(1.0);
  const maxLogN = Math.log(150.0);

  function toScreenX(price) {
    const lp = Math.log(Math.max(price, 0.000005));
    return padLeft + ((lp - minLogP) / (maxLogP - minLogP)) * plotW;
  }

  function toScreenY(n) {
    const ln = Math.log(Math.max(n, 1.0));
    return padTop + plotH - ((ln - minLogN) / (maxLogN - minLogN)) * plotH;
  }

  // ── 2. BACKGROUND PRICE TIER BANDS & LABELS ──────────────────────────
  const tierBands = [
    { code: "T0", label: "Nano", min: 0.00001, max: 0.0001 },
    { code: "T1", label: "Micro", min: 0.0001, max: 0.001 },
    { code: "T2", label: "Sub-Cent", min: 0.001, max: 0.01 },
    { code: "T3", label: "Penny", min: 0.01, max: 0.10 },
    { code: "T4", label: "Low", min: 0.10, max: 1.0 },
    { code: "T5", label: "Mid", min: 1.0, max: 5.0 },
    { code: "T6", label: "High", min: 5.0, max: 20.0 },
    { code: "T7", label: "Mega", min: 20.0, max: 100.0 },
    { code: "T8", label: "Ultra", min: 100.0, max: 1000.0 }
  ];

  tierBands.forEach((tb, i) => {
    const x1 = toScreenX(tb.min);
    const x2 = toScreenX(tb.max);
    
    // Subtle alternating band shade
    if (i % 2 === 0) {
      ctx.fillStyle = "rgba(0, 240, 255, 0.015)";
      ctx.fillRect(x1, padTop, x2 - x1, plotH);
    }

    // Tier header tag at the top
    ctx.font = "bold 9px 'JetBrains Mono', monospace";
    ctx.fillStyle = "rgba(0, 240, 255, 0.4)";
    ctx.textAlign = "center";
    ctx.fillText(`${tb.code} ${tb.label}`, (x1 + x2) / 2, padTop - 12);
    ctx.textAlign = "left";
  });

  // ── 3. SUBTLE GRID LINES & LABELS ─────────────────────────────────────
  // Horizontal grid lines
  const yTicks = [2, 5, 10, 20, 50, 100];
  yTicks.forEach(nVal => {
    const y = toScreenY(nVal);
    ctx.beginPath();
    ctx.setLineDash([2, 4]);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
    ctx.lineWidth = 1;
    ctx.moveTo(padLeft, y);
    ctx.lineTo(padLeft + plotW, y);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // Vertical grid lines
  const xTicks = [
    { p: 0.00001, lbl: "$0.00001" },
    { p: 0.0001,  lbl: "$0.0001" },
    { p: 0.001,   lbl: "$0.001" },
    { p: 0.01,    lbl: "$0.01" },
    { p: 0.1,     lbl: "$0.10" },
    { p: 1.0,     lbl: "$1.0" },
    { p: 10.0,    lbl: "$10" },
    { p: 100.0,   lbl: "$100" },
  ];
  xTicks.forEach(t => {
    const x = toScreenX(t.p);
    ctx.beginPath();
    ctx.setLineDash([2, 4]);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
    ctx.lineWidth = 1;
    ctx.moveTo(x, padTop);
    ctx.lineTo(x, padTop + plotH);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // ── 3.5. SOLID 0xy COORDINATE AXES (TRỤC OXY NỔI BẬT & RÕ RÀNG) ─────────
  // 1. Solid Trục Tung (Oy / Y-Axis)
  ctx.strokeStyle = "rgba(0, 240, 255, 0.75)";
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(padLeft, padTop - 12);
  ctx.lineTo(padLeft, padTop + plotH);
  ctx.stroke();

  // Y-Axis Arrow Head
  ctx.beginPath();
  ctx.moveTo(padLeft - 4, padTop - 6);
  ctx.lineTo(padLeft, padTop - 15);
  ctx.lineTo(padLeft + 4, padTop - 6);
  ctx.fillStyle = "#00f0ff";
  ctx.fill();

  // Y-Axis Title
  ctx.font = "bold 10px 'JetBrains Mono', Inter, sans-serif";
  ctx.fillStyle = "#00f0ff";
  ctx.textAlign = "left";
  ctx.fillText("↑ Bội Số n (Log)", padLeft - 75, padTop - 18);

  // Y-Axis Ticks & Values
  yTicks.forEach(nVal => {
    const y = toScreenY(nVal);
    // Tick mark
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 240, 255, 0.8)";
    ctx.lineWidth = 1.5;
    ctx.moveTo(padLeft - 6, y);
    ctx.lineTo(padLeft, y);
    ctx.stroke();

    // Value text
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.fillStyle = nVal >= 30 ? "#ff0055" : nVal >= 10 ? "#ffb800" : "#94a3b8";
    ctx.textAlign = "right";
    ctx.fillText(`${nVal}x`, padLeft - 10, y + 4);
    ctx.textAlign = "left";
  });

  // 2. Solid Trục Hoành (Ox / X-Axis)
  ctx.strokeStyle = "rgba(0, 240, 255, 0.75)";
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(padLeft, padTop + plotH);
  ctx.lineTo(padLeft + plotW + 16, padTop + plotH);
  ctx.stroke();

  // X-Axis Arrow Head
  ctx.beginPath();
  ctx.moveTo(padLeft + plotW + 8, padTop + plotH - 4);
  ctx.lineTo(padLeft + plotW + 18, padTop + plotH);
  ctx.lineTo(padLeft + plotW + 8, padTop + plotH + 4);
  ctx.fillStyle = "#00f0ff";
  ctx.fill();

  // X-Axis Title
  ctx.font = "bold 10px 'JetBrains Mono', Inter, sans-serif";
  ctx.fillStyle = "#00f0ff";
  ctx.textAlign = "right";
  ctx.fillText("Giá Đáy Khởi Phát P_base ($ USD, Log Scale) →", padLeft + plotW, padTop + plotH + 40);

  // X-Axis Ticks & Values
  xTicks.forEach(t => {
    const x = toScreenX(t.p);
    // Tick mark
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 240, 255, 0.8)";
    ctx.lineWidth = 1.5;
    ctx.moveTo(x, padTop + plotH);
    ctx.lineTo(x, padTop + plotH + 6);
    ctx.stroke();

    // Value text
    ctx.font = "bold 10.5px 'JetBrains Mono', monospace";
    ctx.fillStyle = "#94a3b8";
    ctx.textAlign = "center";
    ctx.fillText(t.lbl, x, padTop + plotH + 20);
    ctx.textAlign = "left";
  });

  // Origin point dot
  ctx.beginPath();
  ctx.arc(padLeft, padTop + plotH, 3.0, 0, 2 * Math.PI);
  ctx.fillStyle = "#00f0ff";
  ctx.fill();


  // ── 4. GENERALIZED HILL SATURATION DECAY & DYNAMIC HETEROSCEDASTIC FUNNEL ────
  const hp = (cachedResearchData && cachedResearchData.hill_model_parameters) || {
    n_floor: 1.85,
    n_ceiling: 68.0,
    p0: 0.012,
    gamma: 0.38,
    sigma_max: 0.45,
    sigma_min: 0.16,
    p_sigma0: 0.015,
    gamma_sigma: 0.40
  };

  function evalHillMedian(p) {
    const pSafe = Math.max(p, 1e-12);
    const ratio = Math.pow(pSafe / hp.p0, hp.gamma);
    return hp.n_floor + (hp.n_ceiling - hp.n_floor) / (1.0 + ratio);
  }

  function evalHillSigma(p) {
    const pSafe = Math.max(p, 1e-12);
    const ratio = Math.pow(pSafe / hp.p_sigma0, hp.gamma_sigma);
    return hp.sigma_min + (hp.sigma_max - hp.sigma_min) / (1.0 + ratio);
  }

  function evalHillBounds(p) {
    const med = evalHillMedian(p);
    const sig = evalHillSigma(p);
    const high = med * Math.exp(1.645 * sig);
    const low = Math.max(1.15, med * Math.exp(-1.645 * sig));
    return { high, low, med };
  }

  const ciSteps = 140;
  const highPoints = [];
  const lowPoints = [];
  const medPoints = [];

  for (let s = 0; s <= ciSteps; s++) {
    const pVal = Math.exp(minLogP + (s / ciSteps) * (maxLogP - minLogP));
    const b = evalHillBounds(pVal);
    medPoints.push({ x: toScreenX(pVal), y: toScreenY(b.med) });
    highPoints.push({ x: toScreenX(pVal), y: toScreenY(b.high) });
    lowPoints.push({ x: toScreenX(pVal), y: toScreenY(b.low) });
  }

  // Fill Shaded Heteroscedastic Funnel Polygon
  ctx.beginPath();
  highPoints.forEach((pt, idx) => {
    if (idx === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  for (let idx = lowPoints.length - 1; idx >= 0; idx--) {
    ctx.lineTo(lowPoints[idx].x, lowPoints[idx].y);
  }
  ctx.closePath();
  const ciGrad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
  ciGrad.addColorStop(0, "rgba(0, 240, 255, 0.14)");
  ciGrad.addColorStop(1, "rgba(0, 240, 255, 0.02)");
  ctx.fillStyle = ciGrad;
  ctx.fill();

  // Upper & Lower dashed boundary lines
  ctx.strokeStyle = "rgba(0, 240, 255, 0.40)";
  ctx.lineWidth = 1.2;
  ctx.setLineDash([4, 4]);

  ctx.beginPath();
  highPoints.forEach((pt, idx) => {
    if (idx === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();

  ctx.beginPath();
  lowPoints.forEach((pt, idx) => {
    if (idx === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();
  ctx.setLineDash([]);

  // ── 5. MAIN SMOOTH HILL SATURATION MEDIAN CURVE ─────────────────────
  ctx.strokeStyle = "rgba(0, 240, 255, 0.95)";
  ctx.lineWidth = 3.0;
  ctx.shadowColor = "rgba(0, 240, 255, 0.6)";
  ctx.shadowBlur = 12;
  ctx.beginPath();
  medPoints.forEach((pt, idx) => {
    if (idx === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();
  ctx.shadowBlur = 0;

  // ── 6. DATA POINTS WITH Z-ORDERING ──────────────────────────────────
  scatterPoints = [];

  // Get exact active campaigns list from Section 1
  const activeCoinsList = (cachedCampaignsData && cachedCampaignsData.all_campaigns) 
    ? cachedCampaignsData.all_campaigns.filter(c => c.is_active && c.stage !== "DUMP_CONFIRMED" && c.stage !== "DELISTED")
    : [];
  const activeSymbols = new Set(activeCoinsList.map(c => c.symbol));

  // Filter historical events according to currentScatterFilter
  let filteredEvents = events;
  if (currentScatterFilter === "OUTLIER") {
    filteredEvents = events.filter(e => e.n_actual >= 30);
  } else if (currentScatterFilter === "MID") {
    filteredEvents = events.filter(e => e.n_actual >= 10 && e.n_actual < 30);
  } else if (currentScatterFilter === "BASE") {
    filteredEvents = events.filter(e => e.n_actual < 10);
  } else if (currentScatterFilter === "ACTIVE") {
    filteredEvents = []; // When ACTIVE filter selected, show only active coins in step 7
  }

  // Split into layers for clean Z-Ordering
  const basePoints = [];
  const midPoints = [];
  const outlierPoints = [];

  filteredEvents.forEach(e => {
    const x = toScreenX(e.pre_pump_price);
    const y = toScreenY(e.n_actual);
    const pt = { x, y, event: e, isActive: false, radius: e.n_actual >= 30 ? 7.5 : e.n_actual >= 10 ? 5.5 : 4.0 };
    scatterPoints.push(pt);

    if (e.n_actual >= 30) outlierPoints.push(pt);
    else if (e.n_actual >= 10) midPoints.push(pt);
    else basePoints.push(pt);
  });

  // Layer 1: Historical Base Points (n < 10x)
  basePoints.forEach(pt => {
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 3.8, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(0, 229, 255, 0.6)";
    ctx.fill();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
    ctx.lineWidth = 0.8;
    ctx.stroke();
  });

  // Layer 2: Historical Mid Points (10x <= n < 30x)
  midPoints.forEach(pt => {
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 5.5, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(255, 184, 0, 0.85)";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.2;
    ctx.stroke();
  });

  // Layer 3: Historical Super Outliers (n >= 30x)
  outlierPoints.forEach(pt => {
    ctx.shadowColor = "#ff0055";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 7.5, 0, 2 * Math.PI);
    ctx.fillStyle = "#ff0055";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.8;
    ctx.stroke();
    ctx.shadowBlur = 0;
  });

  // ── 7. RENDER ACTIVE RUNNING COINS (SMART COLLISION-FREE LABELING) ─────
  const activeLandmarkOffsets = {
    "AKEUSDT":     { dx: 12,  dy: -10, align: "left" },
    "BTRUSDT":     { dx: 12,  dy: -8,  align: "left" },
    "龙虾USDT":    { dx: 12,  dy: -14, align: "left" },
    "PROMUSDT":    { dx: 12,  dy: -10, align: "left" },
    "MAGMAUSDT":   { dx: 12,  dy: -10, align: "left" },
    "4USDT":       { dx: 12,  dy: -12, align: "left" },
    "BULLAUSDT":   { dx: -12, dy: -8,  align: "right" },
    "ZECUSDT":     { dx: -12, dy: -8,  align: "right" },
    "PUMPUSDT":    { dx: -12, dy: -8,  align: "right" },
    "HEMIUSDT":    { dx: 12,  dy: 14,  align: "left" },
    "MORPHOUSDT":  { dx: 12,  dy: -8,  align: "left" },
    "MUBARAKUSDT": { dx: -12, dy: 14,  align: "right" },
    "ENAUSDT":     { dx: 12,  dy: 12,  align: "left" },
    "TRUMPUSDT":   { dx: 12,  dy: -10, align: "left" },
    "NEARUSDT":    { dx: -12, dy: 14,  align: "right" },
    "SNXXUSDT":    { dx: 12,  dy: -8,  align: "left" },
    "AAVEUSDT":    { dx: 12,  dy: 12,  align: "left" },
    "HUMAUSDT":    { dx: 12,  dy: -10, align: "left" },
    "COTIUSDT":    { dx: -12, dy: -12, align: "right" },
    "GIGGLEUSDT":  { dx: 12,  dy: -10, align: "left" },
    "CETUSUSDT":   { dx: -12, dy: 12,  align: "right" },
    "TAOUSDT":     { dx: 12,  dy: -12, align: "left" },
    "ACTUSDT":     { dx: 12,  dy: -8,  align: "left" },
    "VIRTUALUSDT": { dx: 12,  dy: 10,  align: "left" },
  };

  // Default interactive symbol if not set
  if (!window.selectedScatterSymbol && activeCoinsList.length > 0) {
    window.selectedScatterSymbol = activeCoinsList[0].symbol;
  }

  // Determine which coins get prominent Badge Tags
  const sortedActive = [...activeCoinsList].sort((a, b) => (b.max_n || b.current_n || 1.0) - (a.max_n || a.current_n || 1.0));
  const topFeaturedSymbols = new Set(sortedActive.slice(0, 6).map(c => c.symbol.toUpperCase()));
  if (window.selectedScatterSymbol) {
    topFeaturedSymbols.add(window.selectedScatterSymbol.toUpperCase());
  }

  // Render each active campaign
  activeCoinsList.forEach((c, cIdx) => {
    const sym = c.symbol;
    const basePrice = c.origin_bottom_price;
    const maxN = c.max_n || c.current_n || 2.0;
    const isSelected = window.selectedScatterSymbol && window.selectedScatterSymbol.toUpperCase() === sym.toUpperCase();
    const isTopFeatured = topFeaturedSymbols.has(sym.toUpperCase());
    const shouldShowBadge = (window.currentLabelMode === "ALL") || isTopFeatured || isSelected;

    let offset = activeLandmarkOffsets[sym] || { dx: 10, dy: -8, align: "left" };
    // In ALL mode, alternate vertical offset to reduce collisions
    if (window.currentLabelMode === "ALL" && !activeLandmarkOffsets[sym]) {
      const altDy = (cIdx % 2 === 0) ? -12 : 12;
      offset = { dx: 10, dy: altDy, align: "left" };
    }

    const x = toScreenX(basePrice);
    const y = toScreenY(maxN);

    // Push to scatterPoints for interactive hover and click
    scatterPoints.push({
      x, y,
      isActive: true,
      campaign: c,
      radius: isSelected ? 12 : 9
    });

    // 1. Draw Active Point Dot
    ctx.beginPath();
    ctx.arc(x, y, isSelected ? 8.0 : 6.0, 0, 2 * Math.PI);
    ctx.fillStyle = maxN >= 30 ? "#ff0055" : maxN >= 10 ? "#ffb800" : "#00f0ff";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = isSelected ? 2.5 : 1.8;
    ctx.stroke();

    // 2. Draw Active Green Pulsing Halo
    ctx.beginPath();
    ctx.arc(x, y, isSelected ? 14.0 : 10.5, 0, 2 * Math.PI);
    ctx.strokeStyle = isSelected ? "#ffd700" : "#00e676";
    ctx.lineWidth = isSelected ? 2.5 : 1.8;
    ctx.stroke();

    // 3. Draw Badge Tag (Only for Top / Selected / In ALL mode)
    if (shouldShowBadge) {
      const cleanSym = sym.endsWith("USDT") ? sym.slice(0, -4) : sym;
      const labelText = `${cleanSym} (${maxN.toFixed(1)}x) ${maxN >= 10 ? '🔥' : '⚡'}`;

      ctx.font = isSelected ? "bold 12px 'JetBrains Mono', Inter, sans-serif" : "bold 10.5px 'JetBrains Mono', Inter, sans-serif";
      const textMetrics = ctx.measureText(labelText);
      const textW = textMetrics.width;
      const textH = isSelected ? 18 : 15;

      const lx = offset.align === "right" ? x + offset.dx - textW - 6 : x + offset.dx;
      const ly = y + offset.dy - 10;

      // Glowing Pill badge for Active Coin
      ctx.shadowColor = isSelected ? "rgba(255, 215, 0, 0.6)" : "rgba(0, 230, 118, 0.5)";
      ctx.shadowBlur = isSelected ? 12 : 8;
      ctx.fillStyle = isSelected ? "rgba(18, 25, 45, 0.98)" : "rgba(10, 20, 30, 0.92)";
      ctx.strokeStyle = isSelected ? "#ffd700" : "#00e676";
      ctx.lineWidth = isSelected ? 2.0 : 1.4;
      ctx.beginPath();
      ctx.roundRect(lx - 4, ly - 2, textW + 8, textH + 2, 4);
      ctx.fill();
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Text
      ctx.fillStyle = isSelected ? "#ffd700" : "#ffffff";
      ctx.fillText(labelText, lx, ly + (isSelected ? 12 : 10));
    }
  });


  // ── 7.5. INTERACTIVE MULTIVARIATE RETICLE & LIFT VECTOR ──────────────────
  if (window.selectedScatterSymbol) {
    const selSym = window.selectedScatterSymbol.toUpperCase();
    const selCamp = activeCoinsList.find(c => c.symbol.toUpperCase() === selSym || c.symbol.toUpperCase() === `${selSym}USDT`);
    
    if (selCamp) {
      const bPrice = selCamp.origin_bottom_price;
      const xPos = toScreenX(bPrice);
      const nBase1D = evalHillMedian(bPrice);
      const yBase1D = toScreenY(nBase1D);
      
      const mlPred = selCamp.ml_prediction || {};
      const decomp = selCamp.multivariate_decomp || mlPred.multivariate_decomp || {};
      const nTarget = mlPred.n_expected || decomp.n_multivariate_target || selCamp.expected_n_ml || (nBase1D * 1.35);
      const yTarget = toScreenY(nTarget);
      const targetPrice = bPrice * nTarget;

      // 1. Draw Dashed Drift Vector (Connecting 1D curve baseline to Multivariate ML Target)
      ctx.beginPath();
      ctx.setLineDash([5, 4]);
      ctx.moveTo(xPos, yBase1D);
      ctx.lineTo(xPos, yTarget);
      ctx.strokeStyle = "#ffd700";
      ctx.lineWidth = 2.4;
      ctx.shadowColor = "#ffd700";
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.shadowBlur = 0;

      // 2. Draw Vector Arrow Head at Target
      ctx.beginPath();
      ctx.moveTo(xPos - 5, yTarget + 8);
      ctx.lineTo(xPos, yTarget);
      ctx.lineTo(xPos + 5, yTarget + 8);
      ctx.fillStyle = "#ffd700";
      ctx.fill();

      // 3. Draw Target Reticle at (xPos, yTarget)
      ctx.beginPath();
      ctx.arc(xPos, yTarget, 14, 0, 2 * Math.PI);
      ctx.strokeStyle = "rgba(255, 215, 0, 0.85)";
      ctx.lineWidth = 1.8;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(xPos, yTarget, 5, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffd700";
      ctx.fill();

      // Crosshairs
      ctx.beginPath();
      ctx.moveTo(xPos - 20, yTarget); ctx.lineTo(xPos - 8, yTarget);
      ctx.moveTo(xPos + 8, yTarget);  ctx.lineTo(xPos + 20, yTarget);
      ctx.moveTo(xPos, yTarget - 20); ctx.lineTo(xPos, yTarget - 8);
      ctx.moveTo(xPos, yTarget + 8);  ctx.lineTo(xPos, yTarget + 20);
      ctx.strokeStyle = "#ffd700";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 4. Draw Rich Target Callout Pill
      const cleanTargetSym = selCamp.symbol.endsWith("USDT") ? selCamp.symbol.slice(0, -4) : selCamp.symbol;
      const targetTxt = `🎯 ${cleanTargetSym} ML Target: ${nTarget.toFixed(1)}x ($${targetPrice < 0.01 ? targetPrice.toFixed(6) : targetPrice.toFixed(4)})`;
      const fBoost = decomp.funding_boost_pct ? `⚡ Funding +${decomp.funding_boost_pct}%` : "";
      const vBoost = decomp.volume_boost_pct ? `🌊 Vol +${decomp.volume_boost_pct}%` : "";
      const subTxt = [fBoost, vBoost].filter(Boolean).join(" &bull; ");

      ctx.font = "bold 11px 'JetBrains Mono', Inter, sans-serif";
      const tMetrics = ctx.measureText(targetTxt);
      const cardW = Math.max(tMetrics.width + 16, 220);
      const cardH = subTxt ? 36 : 22;
      const cardX = Math.min(W - padRight - cardW - 10, xPos + 18);
      const cardY = Math.max(padTop + 10, yTarget - cardH / 2);

      // Glassmorphic Card Background
      ctx.shadowColor = "rgba(255, 215, 0, 0.4)";
      ctx.shadowBlur = 12;
      ctx.fillStyle = "rgba(15, 23, 42, 0.96)";
      ctx.strokeStyle = "#ffd700";
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.roundRect(cardX, cardY, cardW, cardH, 6);
      ctx.fill();
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Header Text
      ctx.fillStyle = "#ffd700";
      ctx.fillText(targetTxt, cardX + 8, cardY + 15);

      // Subtext breakdown if present
      if (subTxt) {
        ctx.font = "10px Inter, sans-serif";
        ctx.fillStyle = "#94a3b8";
        ctx.fillText(subTxt.replace("&bull;", "•"), cardX + 8, cardY + 29);
      }
    }
  }

  // ── 8. RICH INTERACTIVE TOOLTIP & CLICK SELECTION ─────────────────────
  if (!isScatterHoverAttached) {
    isScatterHoverAttached = true;
    const tooltip = document.getElementById("ml-scatter-tooltip");

    canvas.addEventListener("click", (evt) => {
      const cRect = canvas.getBoundingClientRect();
      const clickX = evt.clientX - cRect.left;
      const clickY = evt.clientY - cRect.top;

      let clicked = null;
      for (const pt of scatterPoints) {
        const dist = Math.hypot(pt.x - clickX, pt.y - clickY);
        if (dist <= pt.radius + 12) {
          clicked = pt;
          break;
        }
      }
      if (clicked) {
        const targetSym = clicked.campaign ? clicked.campaign.symbol : (clicked.event ? clicked.event.symbol : null);
        if (targetSym) {
          window.selectScatterSymbol(targetSym);
        }
      }
    });

    canvas.addEventListener("mousemove", (evt) => {
      const cRect = canvas.getBoundingClientRect();
      const mouseX = evt.clientX - cRect.left;
      const mouseY = evt.clientY - cRect.top;

      let found = null;
      for (const pt of scatterPoints) {
        const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
        if (dist <= pt.radius + 8) {
          found = pt;
          break;
        }
      }

      if (found && tooltip) {
        if (found.campaign) {
          const c = found.campaign;
          const baseFmt = c.origin_bottom_price < 0.001 ? c.origin_bottom_price.toFixed(8) : c.origin_bottom_price < 1 ? c.origin_bottom_price.toFixed(5) : c.origin_bottom_price.toFixed(2);
          const peakFmt = c.highest_peak_price < 0.001 ? c.highest_peak_price.toFixed(8) : c.highest_peak_price < 1 ? c.highest_peak_price.toFixed(5) : c.highest_peak_price.toFixed(2);
          const currFmt = c.current_price < 0.001 ? c.current_price.toFixed(8) : c.current_price < 1 ? c.current_price.toFixed(5) : c.current_price.toFixed(2);
          const decomp = c.multivariate_decomp || {};
          const mlTargetN = c.ml_prediction ? c.ml_prediction.n_expected : (decomp.n_multivariate_target || c.expected_n_ml || 5.0);

          tooltip.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-weight: 800; font-size: 1.05rem; color: #fff;">${c.symbol}</span>
              <span style="font-size: 0.68rem; padding: 2px 6px; border-radius: 4px; font-weight: 700; background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid #00e676;">
                🟢 ${c.stage_label_vi || c.stage}
              </span>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px; display: flex; justify-content: space-between;">
              <span style="color: var(--text-dim);">Đáy Gốc (Base):</span>
              <strong style="color: var(--accent-cyan);">$${baseFmt}</strong>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px; display: flex; justify-content: space-between;">
              <span style="color: var(--text-dim);">Đỉnh Cao (Peak):</span>
              <strong style="color: var(--accent-yellow);">$${peakFmt} (${c.max_n}x)</strong>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px; display: flex; justify-content: space-between;">
              <span style="color: var(--text-dim);">Giá Hiện Tại:</span>
              <strong style="color: #fff;">$${currFmt} (${c.current_n}x)</strong>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #ffd700; margin-bottom: 4px; display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,215,0,0.25); padding-top: 4px;">
              <span>🎯 Mục Tiêu ML Đa Biến:</span>
              <strong>${mlTargetN.toFixed(1)}x ($${(c.origin_bottom_price * mlTargetN).toFixed(4)})</strong>
            </div>
            <div style="font-size: 0.70rem; color: var(--text-dim); line-height: 1.4; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 5px;">
              Khởi phát: ${c.origin_date} (${c.pump_age_days || 1} ngày) &bull; Sụt đỉnh: -${c.drawdown_from_peak_pct}%
            </div>
            <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.68rem; color: var(--accent-yellow);">💡 Click để khóa tâm ngắm</span>
              <a href="/?symbol=${c.symbol}" style="font-size: 0.70rem; color: var(--accent-cyan); text-decoration: none; font-weight: 700;">Soi Nến Live ↗</a>
            </div>
          `;
        } else if (found.event) {
          const ev = found.event;
          const baseFmt = ev.pre_pump_price < 0.001 ? ev.pre_pump_price.toFixed(8) : ev.pre_pump_price < 1 ? ev.pre_pump_price.toFixed(5) : ev.pre_pump_price.toFixed(2);
          const peakFmt = ev.peak_price < 0.001 ? ev.peak_price.toFixed(8) : ev.peak_price < 1 ? ev.peak_price.toFixed(5) : ev.peak_price.toFixed(2);

          tooltip.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-weight: 800; font-size: 1.02rem; color: #fff;">${ev.symbol}</span>
              <span style="font-size: 0.68rem; padding: 2px 6px; border-radius: 4px; font-weight: 700; background: rgba(255,255,255,0.08); color: var(--text-dim); border: 1px solid rgba(255,255,255,0.15);">
                ⚪ LỊCH SỬ ĐÃ HOÀN TẤT
              </span>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px; display: flex; justify-content: space-between;">
              <span style="color: var(--text-dim);">Đáy Gốc (Base):</span>
              <strong style="color: var(--accent-cyan);">$${baseFmt}</strong>
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px; display: flex; justify-content: space-between;">
              <span style="color: var(--text-dim);">Đỉnh Cao Nhất:</span>
              <strong style="color: var(--accent-yellow);">$${peakFmt} (${ev.n_actual.toFixed(2)}x)</strong>
            </div>
            <div style="font-size: 0.70rem; color: var(--text-dim); line-height: 1.4; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 5px;">
              Tầng: ${ev.tier_code || 'Tiers'} &bull; Vol Spike: ${ev.vol_spike_ratio ? ev.vol_spike_ratio.toFixed(1) + 'x' : '—'} &bull; Ngày: ${ev.event_date}
            </div>
          `;
        }
        tooltip.style.left = `${Math.min(cRect.width - 240, Math.max(10, mouseX + 15))}px`;
        tooltip.style.top = `${Math.max(10, mouseY - 85)}px`;
        tooltip.style.display = "block";
      } else if (tooltip) {
        tooltip.style.display = "none";
      }
    });

    canvas.addEventListener("mouseleave", () => {
      if (tooltip) tooltip.style.display = "none";
    });
  }
}

// Global selector for interactive scatter focus and label mode
window.selectedScatterSymbol = "4USDT";
window.currentLabelMode = "FOCUS";

window.selectScatterSymbol = function(sym) {
  window.selectedScatterSymbol = sym;
  if (cachedResearchData && cachedResearchData.events) {
    renderScatterCanvas(cachedResearchData.events);
  }
};

window.setLabelMode = function(mode) {
  window.currentLabelMode = mode;
  const focusBtn = document.getElementById("label-mode-focus");
  const allBtn = document.getElementById("label-mode-all");
  if (focusBtn) {
    if (mode === "FOCUS") focusBtn.classList.add("active");
    else focusBtn.classList.remove("active");
  }
  if (allBtn) {
    if (mode === "ALL") allBtn.classList.add("active");
    else allBtn.classList.remove("active");
  }
  if (cachedResearchData && cachedResearchData.events) {
    renderScatterCanvas(cachedResearchData.events);
  }
};





function renderTiersGrid(tiers) {
  const container = document.getElementById("tiers-grid");
  if (!container) return;

  container.innerHTML = tiers.map(t => {
    const minP = t.price_min !== undefined ? t.price_min : (t.min_price || 0);
    const maxP = t.price_max !== undefined ? t.price_max : (t.max_price || 1000000);
    const minFmt = minP === 0 ? '$0.00' : (minP < 0.001 ? `$${minP.toFixed(6)}` : `$${minP}`);
    const maxFmt = maxP >= 100000 ? '&infin;' : (maxP < 0.001 ? `$${maxP.toFixed(6)}` : `$${maxP}`);

    return `
      <div style="background: rgba(18, 24, 36, 0.75); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 6px; padding: 10px; font-size: 0.78rem;">
        <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 4px;">${t.label}</div>
        <div style="font-family: var(--font-mono); color: var(--text-dim); font-size: 0.72rem; margin-bottom: 6px;">${minFmt} &rarr; ${maxFmt}</div>
        <div style="display: flex; justify-content: space-between; font-family: var(--font-mono);">
          <span style="color: var(--text-muted);">Biên độ n:</span>
          <strong style="color: var(--accent-yellow);">${t.n_expected_low}x &rarr; ${t.n_expected_high}x (Med: ${t.n_median}x)</strong>
        </div>
      </div>
    `;
  }).join("");
}


function renderDatasetTable(events) {
  const tbody = document.getElementById("dataset-tbody");
  const paginationContainer = document.getElementById("dataset-pagination-container");
  if (!tbody) return;

  cachedDatasetEvents = events || [];
  const totalEvents = cachedDatasetEvents.length;

  if (totalEvents === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 20px;">Chưa có sự kiện nào.</td></tr>`;
    if (paginationContainer) paginationContainer.innerHTML = "";
    return;
  }

  const totalPages = datasetPageSize > 0 ? Math.ceil(totalEvents / datasetPageSize) : 1;
  if (datasetCurrentPage > totalPages) datasetCurrentPage = Math.max(1, totalPages);
  const startIndex = datasetPageSize > 0 ? (datasetCurrentPage - 1) * datasetPageSize : 0;
  const endIndex = datasetPageSize > 0 ? Math.min(startIndex + datasetPageSize, totalEvents) : totalEvents;
  const paginatedEvents = datasetPageSize > 0 ? cachedDatasetEvents.slice(startIndex, endIndex) : cachedDatasetEvents;

  tbody.innerHTML = paginatedEvents.map(e => `
    <tr>
      <td style="font-weight: 700;">
        <a href="/?symbol=${e.symbol}" style="color: var(--accent-cyan); text-decoration: none;">${e.symbol}</a>
      </td>
      <td style="font-family: var(--font-mono); color: var(--text-dim);">${e.event_date}</td>
      <td style="font-family: var(--font-mono);">$${e.pre_pump_price < 0.001 ? e.pre_pump_price.toFixed(8) : e.pre_pump_price < 1 ? e.pre_pump_price.toFixed(4) : e.pre_pump_price.toFixed(2)}</td>
      <td style="font-family: var(--font-mono);">$${e.peak_price < 0.001 ? e.peak_price.toFixed(8) : e.peak_price < 1 ? e.peak_price.toFixed(4) : e.peak_price.toFixed(2)}</td>
      <td style="font-family: var(--font-mono); font-weight: 800; color: ${e.n_actual >= 30 ? 'var(--accent-red)' : e.n_actual >= 10 ? 'var(--accent-yellow)' : 'var(--accent-green)'};">
        ${e.n_actual.toFixed(2)}x
      </td>
      <td><span class="badge badge-info" style="font-size: 0.72rem;">${e.tier_code}</span></td>
      <td style="font-family: var(--font-mono);">${e.vol_spike_ratio ? e.vol_spike_ratio.toFixed(1) + 'x' : '—'}</td>
      <td style="font-family: var(--font-mono); color: var(--text-dim);">${e.pump_duration_h ? e.pump_duration_h.toFixed(0) + 'h' : '—'}</td>
      <td style="font-size: 0.75rem; color: var(--text-muted); max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${e.notes || ''}">
        ${e.notes || '—'}
      </td>
    </tr>
  `).join("");

  if (paginationContainer) {
    paginationContainer.innerHTML = buildPaginationHtml(totalEvents, datasetCurrentPage, datasetPageSize, 'setDatasetPage', 'setDatasetPageSize', [15, 25, 50, 100, 0]);
  }
}

async function fetchBenchmarkLedger() {
  try {
    const res = await fetch("/api/ml/benchmark_ledger");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success" || !data.report) return;

    const rep = data.report;

    const hitEl = document.getElementById("ledger-hit-rate");
    if (hitEl) hitEl.innerText = `${rep.hit_rate_pct}%`;

    const apeEl = document.getElementById("ledger-avg-ape");
    if (apeEl) apeEl.innerText = `${rep.avg_ape_pct}%`;

    const totalEl = document.getElementById("ledger-total-events");
    if (totalEl) totalEl.innerText = `${rep.total_events} Sự Kiện`;

    const statusEl = document.getElementById("ledger-daemon-status");
    if (statusEl) statusEl.innerText = rep.daemon_status || "Tự Động 24/7";

    const lastRetrainEl = document.getElementById("ledger-last-retrain");
    if (lastRetrainEl) lastRetrainEl.innerText = `Đã cập nhật: ${rep.last_retrain || 'Realtime'}`;

    renderBenchmarkLedgerTable(rep.records || []);
  } catch (err) {
    console.debug("Error fetching benchmark ledger:", err);
  }
}

function renderBenchmarkLedgerTable(records) {
  const tbody = document.getElementById("ledger-tbody");
  const paginationContainer = document.getElementById("ledger-pagination-container");
  if (!tbody) return;

  cachedLedgerRecords = records || [];
  const totalRecords = cachedLedgerRecords.length;

  if (totalRecords === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim); padding: 25px;">Chưa có sự kiện dump nào được ghi nhận vào sổ cái đối chiếu.</td></tr>`;
    if (paginationContainer) paginationContainer.innerHTML = "";
    return;
  }

  const totalPages = ledgerPageSize > 0 ? Math.ceil(totalRecords / ledgerPageSize) : 1;
  if (ledgerCurrentPage > totalPages) ledgerCurrentPage = Math.max(1, totalPages);
  const startIndex = ledgerPageSize > 0 ? (ledgerCurrentPage - 1) * ledgerPageSize : 0;
  const endIndex = ledgerPageSize > 0 ? Math.min(startIndex + ledgerPageSize, totalRecords) : totalRecords;
  const paginatedRecords = ledgerPageSize > 0 ? cachedLedgerRecords.slice(startIndex, endIndex) : cachedLedgerRecords;

  tbody.innerHTML = paginatedRecords.map(r => {
    const baseFmt = r.base_price < 0.001 ? r.base_price.toFixed(8) : r.base_price < 1 ? r.base_price.toFixed(5) : r.base_price.toFixed(2);
    const peakFmt = r.peak_price_actual < 0.001 ? r.peak_price_actual.toFixed(8) : r.peak_price_actual < 1 ? r.peak_price_actual.toFixed(5) : r.peak_price_actual.toFixed(2);
    const targetFmt = r.target_price_predicted < 0.001 ? r.target_price_predicted.toFixed(8) : r.target_price_predicted < 1 ? r.target_price_predicted.toFixed(5) : r.target_price_predicted.toFixed(2);

    let badgeColor = "var(--accent-green)";
    let badgeBg = "rgba(0, 230, 118, 0.15)";
    if (r.outcome_status.includes("VƯỢT")) {
      badgeColor = "var(--accent-cyan)";
      badgeBg = "rgba(0, 240, 255, 0.15)";
    } else if (r.outcome_status.includes("HỤT")) {
      badgeColor = "var(--accent-red)";
      badgeBg = "rgba(255, 51, 102, 0.15)";
    }

    return `
      <tr>
        <td style="font-weight: 800;">
          <a href="/?symbol=${r.symbol}" style="color: var(--accent-cyan); text-decoration: none;">${r.symbol}</a>
        </td>
        <td style="font-family: var(--font-mono); color: var(--text-dim);">${r.event_date}</td>
        <td style="font-family: var(--font-mono);">$${baseFmt}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: #fff;">$${peakFmt}</td>
        <td style="font-family: var(--font-mono); font-weight: 800; color: ${r.n_actual >= 30 ? 'var(--accent-red)' : r.n_actual >= 10 ? 'var(--accent-yellow)' : 'var(--accent-green)'};">
          ${r.n_actual.toFixed(2)}x
        </td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--accent-yellow);">
          ${r.n_predicted.toFixed(2)}x
        </td>
        <td style="font-family: var(--font-mono); color: var(--text-dim);">
          ${r.n_low.toFixed(1)}x - ${r.n_high.toFixed(1)}x
        </td>
        <td style="font-family: var(--font-mono); color: var(--text-muted);">$${targetFmt}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: ${r.ape_pct <= 15 ? 'var(--accent-green)' : r.ape_pct <= 25 ? 'var(--accent-yellow)' : 'var(--accent-red)'};">
          ${r.ape_pct.toFixed(1)}%
        </td>
        <td>
          <span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeColor};">
            ${r.outcome_status}
          </span>
        </td>
        <td style="font-size: 0.74rem; color: var(--text-muted); max-width: 240px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${r.notes || ''}">
          ${r.notes || '—'}
        </td>
      </tr>
    `;
  }).join("");

  if (paginationContainer) {
    paginationContainer.innerHTML = buildPaginationHtml(totalRecords, ledgerCurrentPage, ledgerPageSize, 'setLedgerPage', 'setLedgerPageSize', [10, 20, 50, 100, 0]);
  }
}


async function triggerManualRetrain() {
  try {
    const res = await fetch("/api/ml/retrain_models", { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === "success") {
      fetchBenchmarkLedger();
      fetchResearchData();
      alert("Đã tái huấn luyện mô hình ML Tri-Ensemble v4 và đồng bộ sổ cái đối chiếu thực nghiệm thành công!");
    }
  } catch (e) {
    console.error("Error triggering manual retrain:", e);
  }
}
