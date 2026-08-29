/**
 * DeepAlpha — ML Super-Pump Lifecycle & CRISP-DM Research Engine (lifecycle.js)
 * Standalone dedicated controller for Multi-Month Campaigns, 2-Way CRISP-DM Scatter Chart, and 126 USD-M Event DB.
 */

let currentCampaignFilter = "ACTIVE";
let cachedCampaignsData = null;
let cachedResearchData = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchCampaignsData();
  fetchResearchData();
  setInterval(fetchCampaignsData, 5000);
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
          ${c.is_active ? `
          <div style="background: rgba(0, 240, 255, 0.04); border: 1px dashed rgba(0, 240, 255, 0.35); padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.78rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <div>
                <span style="color: var(--text-dim); display: block; font-size: 0.68rem;">DAI DINH KY VONG ML (90% CI):</span>
                <strong style="color: var(--accent-yellow); font-family: var(--font-mono); font-size: 0.92rem;">${nLow.toFixed(1)}x &rarr; ${nHigh.toFixed(1)}x</strong>
                <span style="color: var(--accent-cyan); font-size: 0.72rem; font-family: var(--font-mono); margin-left: 4px;">(Med: ${nExp.toFixed(1)}x)</span>
              </div>
              <div style="text-align: right;">
                <span style="color: var(--text-dim); display: block; font-size: 0.68rem;">VUNG GIA MUC TIEU:</span>
                <strong style="color: #fff; font-family: var(--font-mono); font-size: 0.82rem;">$${priceLowFmt} &rarr; $${priceHighFmt}</strong>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; font-size: 0.73rem; margin-bottom: 4px;">
              <span style="color: var(--text-muted);">Tien Do Dat Muc Tieu ML: <strong style="color: var(--accent-cyan); font-family: var(--font-mono);">${progressPct}%</strong></span>
              <span style="color: ${upsidePct > 0 ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 700; font-family: var(--font-mono);">
                ${upsidePct > 0 ? '+' + upsidePct + '% Du Dia Den Dinh' : 'Da Cham Vung Dinh ML'}
              </span>
            </div>
            <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
              <div style="width: ${progressPct}%; height: 100%; background: linear-gradient(90deg, #00e676 0%, #00f0ff 70%, #ffb800 100%); border-radius: 3px;"></div>
            </div>
          </div>
          ` : ''}

          <div style="font-size: 0.76rem; color: var(--text-dim); line-height: 1.4; margin-bottom: 10px;">
            ${c.notes || ''}
          </div>
        </div>

        <!-- Bottom Warning / Trailing -->
        <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid rgba(255, 255, 255, 0.06); padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span>Nguong Cat Dump: <strong style="color: var(--accent-red);">$${dumpFmt}</strong></span>
          <a href="/?symbol=${c.symbol}" class="btn-inspect" style="padding: 4px 10px; font-size: 0.74rem;" title="Mo bieu do TradingView">
            Soi Nen
          </a>
        </div>
      </div>
    `;
  }).join("");
}

const CAMPAIGN_PRESETS = {
  "BTRUSDT":   { base: 0.01587, curr: 0.15663, vol: 18.5, funding: -1.20 },
  "AKEUSDT":   { base: 0.0001729, curr: 0.0107, vol: 35.0, funding: -1.80 },
  "BULLAUSDT": { base: 0.003824, curr: 0.01664, vol: 12.0, funding: -0.80 },
  "PUMPUSDT":  { base: 0.001149, curr: 0.00456, vol: 15.0, funding: -1.50 },
  "HEMIUSDT":  { base: 0.004101, curr: 0.01152, vol: 8.5, funding: -0.50 },
  "SNXXUSDT":  { base: 6.20, curr: 12.77, vol: 6.0, funding: -0.30 },
};

function onMLSelectCampaign(symbol) {
  const customBox = document.getElementById("ml-custom-input-box");
  if (symbol === "CUSTOM") {
    if (customBox) customBox.style.display = "block";
    return;
  }
  if (customBox) customBox.style.display = "none";

  const p = CAMPAIGN_PRESETS[symbol];
  if (p) {
    const baseIn = document.getElementById("ml-pred-base-price");
    const currIn = document.getElementById("ml-pred-curr-price");
    const volIn = document.getElementById("ml-pred-vol-spike");
    const fundIn = document.getElementById("ml-pred-funding");

    if (baseIn) baseIn.value = p.base;
    if (currIn) currIn.value = p.curr;
    if (volIn) volIn.value = p.vol;
    if (fundIn) fundIn.value = p.funding;

    runInteractiveMLPrediction();
  }
}

async function runInteractiveMLPrediction() {
  try {
    const sel = document.getElementById("ml-pred-symbol-select");
    let sym = sel ? sel.value : "BTRUSDT";
    if (sym === "CUSTOM") {
      const customIn = document.getElementById("ml-pred-custom-sym");
      sym = (customIn && customIn.value.trim()) ? customIn.value.trim().toUpperCase() : "BTRUSDT";
    }

    const basePrice = parseFloat(document.getElementById("ml-pred-base-price")?.value || 0.01587);
    const currPrice = parseFloat(document.getElementById("ml-pred-curr-price")?.value || 0.15663);
    const volSpike = parseFloat(document.getElementById("ml-pred-vol-spike")?.value || 10.0);
    const fundingPct = parseFloat(document.getElementById("ml-pred-funding")?.value || 0.0);
    const fundingRate = fundingPct / 100.0;

    const res = await fetch("/api/ml/predict_pump_multiplier", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: sym,
        base_price: basePrice,
        current_price: currPrice,
        vol_spike_ratio: volSpike,
        funding_rate: fundingRate,
      })
    });

    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success" || !data.prediction) return;

    const p = data.prediction;

    // Update Result UI Card
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
      if (p.progress_pct < 45.0) {
        playbookEl.innerText = `Sóng đang trong pha tăng tốc sớm (tiến độ ${p.progress_pct}%). Dư địa tăng còn lớn (+${p.remaining_upside_pct}%). Khuyến nghị canh các nhịp điều chỉnh pullback để gia tăng vị thế, mục tiêu chốt lời $${p.target_peak_price}.`;
      } else if (p.progress_pct < 80.0) {
        playbookEl.innerText = `Sóng đang trong pha trưởng thành (tiến độ ${p.progress_pct}%). Khuyến nghị giữ vị thế, dời Trailing Stop lên để bảo toàn lợi nhuận và chuẩn bị chốt lời từng phần khi tiệm cận $${p.target_peak_price}.`;
      } else {
        playbookEl.innerText = `Sóng đã tiến sát hoặc vượt mục tiêu ML (${p.progress_pct}%). Rủi ro đảo chiều/phân phối rất cao. Khuyến nghị chốt lời phần lớn vị thế và tuyệt đối không mua đuổi vùng giá này.`;
      }
    }

    const featEl = document.getElementById("ml-pred-res-features");
    if (featEl) {
      featEl.innerHTML = `
        <li>Phân khúc giá ${p.price_tier_code}: Nền tảng kỳ vọng n ≈ ${p.n_low.toFixed(1)}x - ${p.n_high.toFixed(1)}x</li>
        <li>Vol Spike ${volSpike}x: Mở rộng thanh khoản theo luật lũy thừa Bayesian</li>
        <li>Funding ${fundingPct}%: ${fundingPct <= -0.5 ? 'Áp lực Short Squeeze kích thích gia tốc bơm mạnh' : 'Funding trung tính'}</li>
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

function renderScatterCanvas(events) {
  const canvas = document.getElementById("ml-scatter-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;

  ctx.clearRect(0, 0, W, H);

  // Background Grid
  ctx.fillStyle = "#0a0e17";
  ctx.fillRect(0, 0, W, H);

  const padLeft = 70;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 40;

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
  ctx.strokeStyle = "rgba(255, 255, 255, 0.07)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.font = "10px JetBrains Mono";

  // Y-axis grid: 2x, 5x, 10x, 20x, 50x, 100x
  const yTicks = [2, 5, 10, 20, 50, 100];
  yTicks.forEach(nVal => {
    const y = toScreenY(nVal);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();
    ctx.fillText(`${nVal}x`, 25, y + 4);
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
    ctx.fillText(t.lbl, x - 15, H - 15);
  });

  // Draw Regression Power Law Curve
  ctx.strokeStyle = "rgba(0, 240, 255, 0.7)";
  ctx.lineWidth = 2.5;
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

  // Draw Data Points
  events.forEach(e => {
    const x = toScreenX(e.pre_pump_price);
    const y = toScreenY(e.n_actual);

    // Glowing Dot
    ctx.beginPath();
    ctx.arc(x, y, e.n_actual >= 30 ? 6 : 4, 0, 2 * Math.PI);
    ctx.fillStyle = e.n_actual >= 40 ? "#ff0055" : e.n_actual >= 20 ? "#ffb800" : "#00f0ff";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Label landmark coins
    if (["AKEUSDT", "BEATUSDT", "TUTUSDT", "VELVETUSDT", "DEXEUSDT", "BANKUSDT", "SYNUSDT"].includes(e.symbol)) {
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px Inter, sans-serif";
      ctx.fillText(`${e.symbol.replace("USDT", "")} (${e.n_actual.toFixed(0)}x)`, x + 8, y - 6);
    }
  });
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
