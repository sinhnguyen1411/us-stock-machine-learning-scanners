/**
 * DeepAlpha — ML Super-Pump Lifecycle & CRISP-DM Research Engine (lifecycle.js)
 * Standalone dedicated controller for Multi-Month Campaigns, 2-Way CRISP-DM Scatter Chart, and 126 USD-M Event DB.
 */

let currentCampaignFilter = "ACTIVE";
let currentCampaignSort = "PROGRESS_DESC";
let cachedCampaignsData = null;
let cachedResearchData = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchCampaignsData();
  fetchResearchData();
  fetchBenchmarkLedger();
  setInterval(fetchCampaignsData, 5000);
  setInterval(fetchBenchmarkLedger, 10000);
});

function setCampaignFilter(filter) {
  currentCampaignFilter = filter;
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
  renderCampaignsGrid();
}

function setCampaignSort(sortBy) {
  currentCampaignSort = sortBy;
  renderCampaignsGrid();
}

async function fetchCampaignsData() {
  try {
    const res = await fetch("/api/ml/active_pump_campaigns");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    cachedCampaignsData = data;
    
    // Update KPI counters
    const activeEl = document.getElementById("stat-active-count");
    if (activeEl) activeEl.innerText = data.active_count || 0;

    const all = data.all_campaigns || [];
    const dumpedCount = all.filter(c => !c.is_active || c.stage === "DUMP_CONFIRMED").length;
    const dumpedEl = document.getElementById("stat-dumped-count");
    if (dumpedEl) dumpedEl.innerText = dumpedCount;

    renderCampaignsGrid();
  } catch (e) {
    console.debug("Error fetching campaigns data:", e);
  }
}

function renderCampaignsGrid() {
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
    c._nExp = nExp;
    c._nLow = nLow;
    c._nHigh = nHigh;
  });

  // Sort by selected criteria (Default: % Tiến độ đạt mục tiêu ML giảm dần)
  if (currentCampaignSort === "PROGRESS_DESC") {
    displayCampaigns.sort((a, b) => b._progressPct - a._progressPct);
  } else if (currentCampaignSort === "PROGRESS_ASC") {
    displayCampaigns.sort((a, b) => a._progressPct - b._progressPct);
  } else if (currentCampaignSort === "MAX_N_DESC") {
    displayCampaigns.sort((a, b) => b._maxN - a._maxN);
  } else if (currentCampaignSort === "DATE_DESC") {
    displayCampaigns.sort((a, b) => (b.origin_date || '').localeCompare(a.origin_date || ''));
  }

  const grid = document.getElementById("campaigns-grid");
  if (!grid) return;

  if (displayCampaigns.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 30px; background: rgba(0,0,0,0.2); border-radius: 8px;">
        ${currentCampaignFilter === 'ACTIVE' ? 'Hiện tại chưa có thêm siêu sóng nào khác đang trong pha đẩy/neo đỉnh.' : 'Chưa có chiến dịch nào trong mục này.'}
      </div>
    `;
    return;
  }

  grid.innerHTML = displayCampaigns.map(c => {
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
    }

    const mlPred = c.ml_prediction || {};
    const nLow = mlPred.n_low || c.expected_n_low || 5.0;
    const nHigh = mlPred.n_high || c.expected_n_high || 20.0;
    const nExp = mlPred.n_expected || c.expected_n_ml || ((nLow + nHigh) / 2);

    const priceLow = mlPred.target_price_low || (c.origin_bottom_price * nLow);
    const priceHigh = mlPred.target_price_high || (c.origin_bottom_price * nHigh);
    const priceExp = mlPred.target_peak_price || (c.origin_bottom_price * nExp);

    const priceLowFmt = priceLow < 0.001 ? priceLow.toFixed(8) : priceLow < 1 ? priceLow.toFixed(5) : priceLow.toFixed(2);
    const priceHighFmt = priceHigh < 0.001 ? priceHigh.toFixed(8) : priceHigh < 1 ? priceHigh.toFixed(5) : priceHigh.toFixed(2);
    const priceExpFmt = priceExp < 0.001 ? priceExp.toFixed(8) : priceExp < 1 ? priceExp.toFixed(5) : priceExp.toFixed(2);

    const progressPct = mlPred.progress_pct || Math.min(100, Math.round((c.current_n / nExp) * 100));
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
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">ĐỈNH CAO NHẤT (PEAK):</span>
              <strong style="color: var(--accent-yellow); font-size: 0.9rem;">$${peakFmt} (${c.max_n}x)</strong>
            </div>
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">GIÁ HIỆN TẠI:</span>
              <strong style="color: #fff; font-size: 0.9rem;">$${currFmt} (${c.current_n}x)</strong>
            </div>
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">SỤT TỪ ĐỈNH:</span>
              <strong style="color: ${c.drawdown_from_peak_pct >= 35 ? 'var(--accent-red)' : 'var(--accent-green)'}; font-size: 0.9rem;">-${c.drawdown_from_peak_pct}%</strong>
            </div>
          </div>

          <!-- ML Training Target Range & Progress Row -->
          <div style="background: rgba(0, 240, 255, 0.04); border: 1px dashed ${c.is_active ? 'rgba(0, 240, 255, 0.35)' : 'rgba(255, 255, 255, 0.15)'}; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.78rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <div>
                <span style="color: var(--text-dim); display: block; font-size: 0.68rem;">DẢI ĐỈNH KỲ VỌNG ML (90% CI):</span>
                <strong style="color: var(--accent-yellow); font-family: var(--font-mono); font-size: 0.92rem;">${nLow.toFixed(1)}x &rarr; ${nHigh.toFixed(1)}x</strong>
                <span style="color: var(--accent-cyan); font-size: 0.72rem; font-family: var(--font-mono); margin-left: 4px;">(Med: ${nExp.toFixed(1)}x)</span>
              </div>
              <div style="text-align: right;">
                <span style="color: var(--text-dim); display: block; font-size: 0.68rem;">VÙNG GIÁ MỤC TIÊU:</span>
                <strong style="color: #fff; font-family: var(--font-mono); font-size: 0.82rem;">$${priceLowFmt} &rarr; $${priceHighFmt}</strong>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; font-size: 0.73rem; margin-bottom: 4px;">
              <span style="color: var(--text-muted);">
                ${c.is_active ? 'Tiến Độ Đạt Mục Tiêu ML:' : 'Đỉnh Thực Tế Đạt:'} 
                <strong style="color: var(--accent-cyan); font-family: var(--font-mono); font-size: 0.85rem;">${progressPct}%</strong>
                <span style="color: var(--text-dim); font-size: 0.7rem;">(${c.is_active ? c.current_n : c.max_n}x / ${nExp.toFixed(1)}x)</span>
              </span>
              <span style="color: ${c.is_active ? (upsidePct > 0 ? 'var(--accent-green)' : 'var(--accent-red)') : (progressPct >= 100 ? 'var(--accent-green)' : 'var(--accent-yellow)')}; font-weight: 700; font-family: var(--font-mono);">
                ${c.is_active ? (upsidePct > 0 ? '+' + upsidePct + '% Dư Địa Đến Đỉnh' : 'Đã Chạm Vùng Đỉnh ML') : (progressPct >= 100 ? 'ĐẠT VƯỢT MỤC TIÊU' : 'HOÀN TẤT CHU KỲ')}
              </span>
            </div>
            <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
              <div style="width: ${Math.min(100, progressPct)}%; height: 100%; background: ${progressPct >= 100 ? 'linear-gradient(90deg, #00e676 0%, #00f0ff 100%)' : 'linear-gradient(90deg, #00e676 0%, #00f0ff 70%, #ffb800 100%)'}; border-radius: 3px;"></div>
            </div>
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
  }).join("");
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
    if (progText) progText.innerText = `${p.progress_pct}%`;

    const remText = document.getElementById("ml-pred-res-rem-text");
    if (remText) {
      const remPct = Math.max(0, 100 - p.progress_pct);
      remText.innerText = remPct > 0 ? `Còn ${remPct.toFixed(1)}% để chạm mục tiêu ML` : `Đã chạm ngưỡng kỳ vọng`;
    }

    const progBar = document.getElementById("ml-pred-res-progress-bar");
    if (progBar) progBar.style.width = `${p.progress_pct}%`;

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

let scatterPoints = [];
let isScatterHoverAttached = false;

function renderScatterCanvas(events) {
  const canvas = document.getElementById("ml-scatter-canvas");
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 2;
  canvas.width = (rect.width || 1100) * dpr;
  canvas.height = (rect.height || 480) * dpr;

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width || 1100;
  const H = rect.height || 480;

  // High contrast background
  ctx.fillStyle = "#0a0f1d";
  ctx.fillRect(0, 0, W, H);

  const padLeft = 80;
  const padRight = 40;
  const padTop = 35;
  const padBottom = 45;

  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBottom;

  // Log Price Range: 1e-4 ($0.0001) to 1e3 ($1000)
  const minLogP = Math.log(0.0001);
  const maxLogP = Math.log(1000.0);

  // Log N Range: 1.0 (1x) to 120.0 (120x)
  const minLogN = Math.log(1.0);
  const maxLogN = Math.log(120.0);

  function toScreenX(price) {
    const lp = Math.log(Math.max(price, 0.00008));
    return padLeft + ((lp - minLogP) / (maxLogP - minLogP)) * plotW;
  }

  function toScreenY(n) {
    const ln = Math.log(Math.max(n, 1.0));
    return padTop + plotH - ((ln - minLogN) / (maxLogN - minLogN)) * plotH;
  }

  // Draw Grid Lines & Axis Labels
  ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
  ctx.lineWidth = 1;
  ctx.font = "bold 12px 'JetBrains Mono', monospace";

  // Y-axis grid: 2x, 5x, 10x, 20x, 50x, 100x
  const yTicks = [2, 5, 10, 20, 50, 100];
  yTicks.forEach(nVal => {
    const y = toScreenY(nVal);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();

    ctx.fillStyle = nVal >= 30 ? "#ff0055" : nVal >= 10 ? "#ffb800" : "#94a3b8";
    ctx.fillText(`${nVal}x`, 22, y + 4);
  });

  // X-axis grid: $0.0001, $0.001, $0.01, $0.1, $1, $10, $100
  const xTicks = [
    { p: 0.0001, lbl: "$0.0001" },
    { p: 0.001,  lbl: "$0.001" },
    { p: 0.01,   lbl: "$0.01" },
    { p: 0.1,    lbl: "$0.10" },
    { p: 1.0,    lbl: "$1.0" },
    { p: 10.0,   lbl: "$10" },
    { p: 100.0,  lbl: "$100" },
  ];
  xTicks.forEach(t => {
    const x = toScreenX(t.p);
    ctx.beginPath();
    ctx.moveTo(x, padTop);
    ctx.lineTo(x, padTop + plotH);
    ctx.stroke();

    ctx.fillStyle = "#cbd5e1";
    ctx.fillText(t.lbl, x - 22, H - 15);
  });

  // Draw Regression Power Law Curve
  ctx.strokeStyle = "rgba(0, 240, 255, 0.9)";
  ctx.lineWidth = 3;
  ctx.shadowColor = "rgba(0, 240, 255, 0.4)";
  ctx.shadowBlur = 8;
  ctx.beginPath();
  let firstPt = true;
  for (let step = 0; step <= 100; step++) {
    const pVal = Math.exp(minLogP + (step / 100) * (maxLogP - minLogP));
    const nCurve = Math.min(100.0, Math.max(1.8, 6.2 * Math.pow(pVal, -0.22)));
    const x = toScreenX(pVal);
    const y = toScreenY(nCurve);
    if (firstPt) {
      ctx.moveTo(x, y);
      firstPt = false;
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Store screen coordinates for hover interaction
  scatterPoints = [];

  // Draw Data Points
  events.forEach(e => {
    const x = toScreenX(e.pre_pump_price);
    const y = toScreenY(e.n_actual);

    scatterPoints.push({
      x, y,
      event: e,
      radius: e.n_actual >= 30 ? 7 : 5,
    });

    // Glowing Dot
    ctx.beginPath();
    ctx.arc(x, y, e.n_actual >= 30 ? 7 : e.n_actual >= 10 ? 5.5 : 4.5, 0, 2 * Math.PI);
    ctx.fillStyle = e.n_actual >= 30 ? "#ff0055" : e.n_actual >= 10 ? "#ffb800" : "#00f0ff";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // Smart Non-Overlapping Badges for Landmark Coins
  const landmarkPositions = {
    "AKEUSDT":    { dx: 10,  dy: -10, align: "left" },
    "BEATUSDT":   { dx: 10,  dy: -10, align: "left" },
    "VELVETUSDT": { dx: 12,  dy: -8,  align: "left" },
    "TUTUSDT":    { dx: -12, dy: -8,  align: "right" },
    "DEXEUSDT":   { dx: 12,  dy: -6,  align: "left" },
    "BANKUSDT":   { dx: -12, dy: 14,  align: "right" },
    "SYNUSDT":    { dx: 12,  dy: 14,  align: "left" },
    "BTRUSDT":    { dx: 12,  dy: -8,  align: "left" },
    "BULLAUSDT":  { dx: 10,  dy: -8,  align: "left" },
    "PUMPUSDT":   { dx: 10,  dy: 12,  align: "left" },
    "HEMIUSDT":   { dx: 10,  dy: -8,  align: "left" },
    "SNXXUSDT":   { dx: 10,  dy: -8,  align: "left" },
  };

  events.forEach(e => {
    const pos = landmarkPositions[e.symbol];
    if (pos) {
      const x = toScreenX(e.pre_pump_price);
      const y = toScreenY(e.n_actual);

      const labelText = `${e.symbol.replace("USDT", "")} (${e.n_actual.toFixed(0)}x)`;
      ctx.font = "bold 11px Inter, sans-serif";
      const textMetrics = ctx.measureText(labelText);
      const textW = textMetrics.width;
      const textH = 14;

      const lx = pos.align === "right" ? x + pos.dx - textW - 4 : x + pos.dx;
      const ly = y + pos.dy - 10;

      // Draw pill badge
      ctx.fillStyle = "rgba(10, 15, 29, 0.9)";
      ctx.strokeStyle = e.n_actual >= 30 ? "#ff0055" : e.n_actual >= 10 ? "#ffb800" : "#00f0ff";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.roundRect(lx - 4, ly - 2, textW + 8, textH + 4, 4);
      ctx.fill();
      ctx.stroke();

      // Draw text
      ctx.fillStyle = "#ffffff";
      ctx.fillText(labelText, lx, ly + 10);
    }
  });

  // Attach hover interaction once
  if (!isScatterHoverAttached) {
    isScatterHoverAttached = true;
    const tooltip = document.getElementById("ml-scatter-tooltip");

    canvas.addEventListener("mousemove", (evt) => {
      const cRect = canvas.getBoundingClientRect();
      const mouseX = evt.clientX - cRect.left;
      const mouseY = evt.clientY - cRect.top;

      let found = null;
      for (const pt of scatterPoints) {
        const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
        if (dist <= pt.radius + 6) {
          found = pt;
          break;
        }
      }

      if (found && tooltip) {
        const ev = found.event;
        const baseFmt = ev.pre_pump_price < 0.001 ? ev.pre_pump_price.toFixed(8) : ev.pre_pump_price < 1 ? ev.pre_pump_price.toFixed(5) : ev.pre_pump_price.toFixed(2);
        const peakFmt = ev.peak_price < 0.001 ? ev.peak_price.toFixed(8) : ev.peak_price < 1 ? ev.peak_price.toFixed(5) : ev.peak_price.toFixed(2);

        tooltip.innerHTML = `
          <div style="font-weight: 800; font-size: 0.92rem; color: var(--accent-cyan); margin-bottom: 4px;">${ev.symbol}</div>
          <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px;">
            Giá Đáy Gốc: <strong style="color: var(--accent-cyan);">$${baseFmt}</strong>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #fff; margin-bottom: 3px;">
            Đỉnh Cao Nhất: <strong style="color: var(--accent-yellow);">$${peakFmt} (${ev.n_actual.toFixed(2)}x)</strong>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 4px;">
            Phân Khúc: ${ev.tier_code} • Ngày Đáy: ${ev.event_date}
          </div>
        `;
        tooltip.style.left = `${Math.min(cRect.width - 220, Math.max(10, mouseX + 15))}px`;
        tooltip.style.top = `${Math.max(10, mouseY - 70)}px`;
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

function renderTiersGrid(tiers) {
  const container = document.getElementById("tiers-grid");
  if (!container) return;

  container.innerHTML = tiers.map(t => `
    <div style="background: rgba(18, 24, 36, 0.7); border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; font-size: 0.78rem;">
      <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 4px;">${t.label}</div>
      <div style="font-family: var(--font-mono); color: var(--text-dim); font-size: 0.72rem; margin-bottom: 6px;">$${t.min_price} &rarr; $${t.max_price >= 1000000 ? '&infin;' : t.max_price}</div>
      <div style="display: flex; justify-content: space-between; font-family: var(--font-mono);">
        <span style="color: var(--text-muted);">Biên độ n:</span>
        <strong style="color: var(--accent-yellow);">${t.n_expected_low}x &rarr; ${t.n_expected_high}x (Med: ${t.n_median}x)</strong>
      </div>
    </div>
  `).join("");
}

function renderDatasetTable(events) {
  const tbody = document.getElementById("dataset-tbody");
  if (!tbody) return;

  if (events.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 20px;">Chưa có sự kiện nào.</td></tr>`;
    return;
  }

  tbody.innerHTML = events.map(e => `
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
  if (!tbody) return;

  if (records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim); padding: 25px;">Chưa có sự kiện dump nào được ghi nhận vào sổ cái đối chiếu.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
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
