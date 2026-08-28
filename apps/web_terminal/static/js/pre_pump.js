/**
 * DeepAlpha Pre-Pump Leading Radar Page Logic (4-Pillar Quantitative Engine)
 * Captures Ignition, Coiling, and Short Squeeze Anomalies (10x - 40x Pumps)
 */

let allPrePumpCandidates = [];
let currentPrePumpPhase = "ALL";
let isAudioAlertEnabled = true;

document.addEventListener("DOMContentLoaded", () => {
  fetchPrePumpRadar();
  fetchActivePumpCampaigns();
  setInterval(fetchPrePumpRadar, 3000);
  setInterval(fetchActivePumpCampaigns, 5000);
});

let currentCampaignFilter = "ACTIVE";
let cachedCampaignsData = null;

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

async function fetchActivePumpCampaigns() {
  try {
    const res = await fetch("/api/ml/active_pump_campaigns");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    cachedCampaignsData = data;
    renderCampaignsGrid();
  } catch (e) {
    console.debug("Error fetching active pump campaigns:", e);
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

  const grid = document.getElementById("active-campaigns-grid");
  if (!grid) return;

  if (displayCampaigns.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 20px;">
        ${currentCampaignFilter === 'ACTIVE' ? 'Hiện tại không có siêu sóng nào đang trong pha đẩy/neo đỉnh.' : 'Chưa có chiến dịch nào.'}
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
      borderGlow = "border: 1px solid rgba(255, 51, 102, 0.4); background: rgba(255, 51, 102, 0.03);";
    }

    return `
      <div style="background: rgba(11, 15, 23, 0.85); border-radius: 8px; padding: 14px; ${borderGlow} display: flex; flex-direction: column; justify-content: space-between;">
        <div>
          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
              <a href="/?symbol=${c.symbol}" style="font-size: 1.1rem; font-weight: 800; color: #fff; text-decoration: none;" title="Soi Nến ${c.symbol}">
                ${c.symbol}
              </a>
              <div style="font-size: 0.72rem; color: var(--text-dim);">Khởi phát: ${c.origin_date} (${c.pump_age_days || 1} ngày trước)</div>
            </div>
            <span style="font-size: 0.74rem; padding: 3px 8px; border-radius: 4px; background: rgba(255, 255, 255, 0.05); color: ${stageColor}; font-weight: 700; border: 1px solid ${stageColor};">
              ${c.stage_label_vi || c.stage}
            </span>
          </div>

          <!-- Multipliers Grid -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: rgba(0, 0, 0, 0.25); padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: var(--font-mono); font-size: 0.8rem;">
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">ĐÁY GỐC (BASE):</span>
              <strong style="color: var(--accent-cyan);">$${bottomFmt}</strong>
            </div>
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">ĐỈNH CAO NHẤT (PEAK):</span>
              <strong style="color: var(--accent-yellow);">$${peakFmt} (${c.max_n}x)</strong>
            </div>
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">GIÁ HIỆN TẠI:</span>
              <strong style="color: #fff;">$${currFmt} (${c.current_n}x)</strong>
            </div>
            <div>
              <span style="font-size: 0.68rem; color: var(--text-dim); display: block;">SỤT TỪ ĐỈNH:</span>
              <strong style="color: ${c.drawdown_from_peak_pct >= 35 ? 'var(--accent-red)' : 'var(--accent-green)'};">-${c.drawdown_from_peak_pct}%</strong>
            </div>
          </div>
        </div>

        <!-- Bottom Warning / Trailing -->
        <div style="font-size: 0.72rem; color: var(--text-muted); border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 8px; display: flex; justify-content: space-between; align-items: center;">
          <span>Ngưỡng Cắt Dump: <strong style="color: var(--accent-red);">$${dumpFmt}</strong></span>
          <a href="/?symbol=${c.symbol}" class="btn-inspect" style="padding: 3px 8px; font-size: 0.72rem;" title="Mở biểu đồ">
            Soi Nến ↗
          </a>
        </div>
      </div>
    `;
  }).join("");
}



async function fetchPrePumpRadar() {
  try {
    const res = await fetch("/api/pre_pump_radar");
    if (!res.ok) return;
    const data = await res.json();
    allPrePumpCandidates = data.candidates || [];

    // Assign true global rank before filtering
    allPrePumpCandidates.forEach((c, idx) => {
      c.globalRank = idx + 1;
    });

    updatePrePumpStats(data.timestamp);
    renderPrePumpTable();
  } catch (e) {
    console.debug("Error fetching pre-pump radar:", e);
  }
}

function updatePrePumpStats(timestamp) {
  if (!allPrePumpCandidates || allPrePumpCandidates.length === 0) return;

  // 1. Ignition Triggered Count (Strict: only bullish ignition)
  const ignCount = allPrePumpCandidates.filter(c => c.phase === "IGNITION_TRIGGERED" || (c.is_bullish_ignition && c.vol_spike_1h >= 2.2)).length;
  const ignEl = document.getElementById("stat-ignition-count");
  if (ignEl) ignEl.innerText = ignCount;

  // 2. Coiling Count (Compression <= 3.5%)
  const coilCount = allPrePumpCandidates.filter(c => c.phase === "PRE_IGNITION_COILING" || (c.range_1h_avg && c.range_1h_avg <= 3.5)).length;
  const coilEl = document.getElementById("stat-coiling-count");
  if (coilEl) coilEl.innerText = coilCount;

  // 3. Negative Funding Count
  const negFundCount = allPrePumpCandidates.filter(c => c.funding_rate <= -0.0005).length;
  const negFundEl = document.getElementById("stat-neg-funding-count");
  if (negFundEl) negFundEl.innerText = negFundCount;

  // 4. High Score Count (>= 65)
  const highScoreCount = allPrePumpCandidates.filter(c => c.pre_pump_score >= 60).length;
  const highScoreEl = document.getElementById("stat-high-score-count");
  if (highScoreEl) highScoreEl.innerText = highScoreCount;
}

function filterPrePumpPhase(phase) {
  currentPrePumpPhase = phase;
  document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }
  renderPrePumpTable();
}

function formatFundingCountdown(nextFundingTime) {
  if (!nextFundingTime) return "--:--:--";
  const now = Date.now();
  const diff = nextFundingTime - now;
  if (diff <= 0) return "00:00:00";

  const hrs = Math.floor(diff / (1000 * 60 * 60));
  const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const secs = Math.floor((diff % (1000 * 60)) / 1000);

  return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function renderPrePumpTable() {
  const tbody = document.getElementById("pre-pump-body");
  const titleEl = document.getElementById("pre-pump-table-title");
  const subtitleEl = document.getElementById("pre-pump-table-subtitle");
  if (!tbody) return;

  let list = allPrePumpCandidates;
  if (currentPrePumpPhase === "IGNITION") {
    list = allPrePumpCandidates.filter(c => c.phase === "IGNITION_TRIGGERED" || (c.is_bullish_ignition && c.vol_spike_1h >= 2.2));
  } else if (currentPrePumpPhase === "COILING") {
    list = allPrePumpCandidates.filter(c => c.phase === "PRE_IGNITION_COILING" || (c.range_1h_avg && c.range_1h_avg <= 3.5));
  } else if (currentPrePumpPhase === "NEG_FUNDING") {
    list = allPrePumpCandidates.filter(c => c.funding_rate <= -0.0005);
  } else if (currentPrePumpPhase === "EXPANSION") {
    list = allPrePumpCandidates.filter(c => c.phase === "SQUEEZE_EXPANSION" || (c.funding_rate <= -0.005 && c.pct_24h >= 8.0));
  }

  if (titleEl && subtitleEl) {
    if (currentPrePumpPhase !== "ALL") {
      const phaseLabels = {
        "IGNITION": "Vừa Mồi Lửa (Ignition)",
        "COILING": "Đang Nén Đáy (Coiling)",
        "NEG_FUNDING": "Funding Âm Sâu (Short Trap)",
        "EXPANSION": "Short Squeeze Đang Bay"
      };
      const pLbl = phaseLabels[currentPrePumpPhase] || currentPrePumpPhase;
      titleEl.innerText = `DANH SÁCH LỌC PHA THỊ TRƯỜNG: ${pLbl.toUpperCase()} (${list.length} CẶP)`;
      subtitleEl.innerText = `Lọc theo cấu trúc vi mô • Giữ nguyên thứ hạng thực tế trong toàn hệ thống`;
    } else {
      titleEl.innerText = `BẢNG QUÉT VI MÔ 4 TRỤ CỘT & PHÂN LOẠI PHA PUMP`;
      subtitleEl.innerText = `Tự động quét nến 1H lịch sử và Order Flow trên toàn bộ Binance Futures (Cập nhật mỗi 3s)`;
    }
  }

  if (!list || list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="12" style="text-align: center; color: var(--text-dim); padding: 35px;">
          Chưa phát hiện cặp coin nào thuộc bộ lọc "${currentPrePumpPhase}". Đang quét vi mô 1H liên tục...
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = list.map((c) => {
    const rank = c.globalRank;
    const rankBadge = rank === 1 ? "🥇 #1" : rank === 2 ? "🥈 #2" : rank === 3 ? "🥉 #3" : `#${rank}`;
    const rankStyle = rank <= 3 ? "color: var(--accent-red); font-weight: 800;" : "color: var(--text-muted);";
    const pScore = Math.min(100, Math.max(0, c.pre_pump_score || 0));
    const barColor = pScore >= 75 ? "var(--accent-red)" : pScore >= 60 ? "var(--accent-yellow)" : "var(--accent-cyan)";

    const pct = c.pct_24h || 0;
    const pctClass = pct >= 0 ? "badge-green" : "badge-red";
    const pctSign = pct >= 0 ? "+" : "";

    const priceFmt = c.price < 0.001 ? c.price.toFixed(6) : c.price < 1 ? c.price.toFixed(4) : c.price.toFixed(2);
    const frClass = c.funding_rate < 0 ? "funding-negative" : "funding-positive";
    const countdown = formatFundingCountdown(c.next_funding_time);

    const range1h = c.range_1h_avg || 5.0;
    const rangeStyle = range1h <= 3.5 ? "coiling-tight" : "color: var(--text-muted);";

    const volSpike = c.vol_spike_1h || 1.0;
    let volStyle = "color: var(--text-main);";
    let volSubBadge = "";

    if (c.is_bullish_ignition && volSpike >= 2.2) {
      volStyle = "vol-spike-high";
      volSubBadge = ' <span style="font-size:0.7rem; color:var(--accent-yellow);">(Mồi)</span>';
    } else if (!c.is_bullish_ignition && volSpike >= 2.0 && ((c.candle_1h_pct || 0) < -0.3 || (c.taker_buy_1h || 50) < 48.0)) {
      volStyle = "color: var(--accent-red);";
      volSubBadge = ' <span style="font-size:0.7rem; color:var(--accent-red);">(Xả)</span>';
    } else if (volSpike >= 2.0) {
      volStyle = "color: var(--accent-yellow);";
    }

    const takerBuy = c.taker_buy_1h || 50.0;
    const buyStyle = takerBuy >= 53.0 ? "taker-buy-bull" : takerBuy <= 45.0 ? "color: var(--accent-red);" : "color: var(--text-muted);";

    const tp = c.trade_plan || {};
    const slFmt = tp.sl ? `$${tp.sl < 1 ? tp.sl.toFixed(4) : tp.sl.toFixed(2)}` : "--";
    const tp1Fmt = tp.tp1 ? `$${tp.tp1 < 1 ? tp.tp1.toFixed(4) : tp.tp1.toFixed(2)}` : "--";

    // ML Pump Multiplier Prediction
    const pm = c.pump_multiplier || {};
    let multiplierHtml = '';
    if (pm.n_expected) {
      const nExp = pm.n_expected;
      const nLow = pm.n_low || (nExp * 0.6);
      const nHigh = pm.n_high || (nExp * 1.8);
      const tierLbl = pm.tier_code || '';
      const reason = pm.wave_reason || 'Đang trong sóng bơm';
      const conf = pm.confidence ? ` (Độ tin cậy: ${(pm.confidence * 100).toFixed(0)}%)` : '';
      
      let badgeStyle = "background: rgba(0, 240, 255, 0.15); color: var(--accent-cyan); border: 1px solid var(--accent-cyan);";
      let icon = "🎯";
      if (nExp >= 20) {
        badgeStyle = "background: rgba(255, 59, 105, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); box-shadow: 0 0 10px rgba(255, 59, 105, 0.4); font-weight: 800;";
        icon = "🔥";
      } else if (nExp >= 10) {
        badgeStyle = "background: rgba(255, 184, 0, 0.2); color: var(--accent-yellow); border: 1px solid var(--accent-yellow); font-weight: 700;";
        icon = "⚡";
      }

      multiplierHtml = `
        <div style="cursor: help;" title="Ước tính ML: ~${nExp.toFixed(1)}x&#10;Trạng thái: ${reason}&#10;Vùng biến động: [${nLow.toFixed(1)}x - ${nHigh.toFixed(1)}x]&#10;Phân tầng: ${tierLbl}${conf}">
          <span style="display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; font-family: var(--font-mono); ${badgeStyle}">
            ${icon} ~${nExp.toFixed(1)}x
          </span>
          <div style="font-size: 0.68rem; color: var(--accent-cyan); margin-top: 2px; font-weight: 600;">
            ${reason}
          </div>
        </div>
      `;
    } else {
      multiplierHtml = `
        <div style="color: var(--text-dim); font-size: 0.72rem; font-family: var(--font-mono);" title="Tính năng tự kích hoạt khi biến động 24h > 50% hoặc sóng 3D/7D > 75%">
          <span style="opacity: 0.6;">-- (Chờ nổ sóng)</span>
        </div>
      `;
    }

    return `
      <tr>
        <td style="${rankStyle} font-family: var(--font-mono);">${rankBadge}</td>
        <td>
          <div style="font-weight: 700; color: #fff; font-size: 0.95rem;">${c.symbol}</div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">USDT-M Perpetual</div>
        </td>
        <td>
          <div style="font-family: var(--font-mono); font-weight: 600;">$${priceFmt}</div>
          <span class="${pctClass}" style="font-size: 0.72rem;">${pctSign}${pct.toFixed(2)}%</span>
        </td>
        <td>
          <span class="phase-badge ${c.phase_class || 'phase-normal'}">
            ${c.phase_tag || 'BÌNH THƯỜNG'}
          </span>
        </td>
        <td>
          <div class="${frClass}" style="font-size: 0.88rem;">
            ${(c.funding_pct || 0) >= 0 ? '+' : ''}${(c.funding_pct || 0).toFixed(4)}%
          </div>
          <div style="font-family: var(--font-mono); color: var(--text-dim); font-size: 0.72rem;">
            ${countdown}
          </div>
        </td>
        <td class="${rangeStyle}" style="font-size: 0.9rem;">
          ${range1h.toFixed(2)}%
          ${range1h <= 3.5 ? ' <span style="font-size:0.7rem; color:var(--accent-cyan);">(Nén)</span>' : ''}
        </td>
        <td class="${volStyle}" style="font-size: 0.9rem;">
          ${volSpike.toFixed(1)}x${volSubBadge}
        </td>

        <td class="${buyStyle}" style="font-size: 0.9rem;">
          ${takerBuy.toFixed(1)}%
        </td>
        <td>
          <div class="pump-score-wrap">
            <span class="pump-score-num" style="color: ${barColor}; font-size: 0.88rem;">${pScore.toFixed(0)}</span>
            <div class="pump-score-track">
              <div class="pump-score-bar" style="width: ${pScore}%; background: ${barColor};"></div>
            </div>
          </div>
        </td>
        <td>
          ${multiplierHtml}
        </td>
        <td>
          <div class="trade-plan-box">
            <span>SL: <strong style="color:var(--accent-red);">${slFmt}</strong></span>
            <span>TP1 (+20%): <strong style="color:var(--accent-green);">${tp1Fmt}</strong></span>
          </div>
        </td>
        <td>
          <a href="/?symbol=${c.symbol}" class="btn-inspect" title="Mở Terminal để soi nến và phân tích 7 lớp">
            <span>Soi Nến</span>
          </a>
        </td>
      </tr>
    `;
  }).join("");
}

/* ─── Backtest Modal & Audio Alert Controls ─── */
function openBacktestModal() {
  const modal = document.getElementById("backtest-modal");
  if (modal) modal.style.display = "flex";
}

function closeBacktestModal() {
  const modal = document.getElementById("backtest-modal");
  if (modal) modal.style.display = "none";
}

async function runHistoricalBacktest() {
  const symbol = document.getElementById("bt-symbol").value.trim().toUpperCase() || "BTCUSDT";
  const days = parseInt(document.getElementById("bt-days").value, 10) || 7;

  const btn = document.getElementById("btn-run-backtest");
  const loading = document.getElementById("bt-loading");
  const resContainer = document.getElementById("bt-results-container");

  if (btn) btn.disabled = true;
  if (loading) loading.style.display = "block";
  if (resContainer) resContainer.style.display = "none";

  try {
    const resp = await fetch("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, days, initial_balance: 1000.0 })
    });
    const data = await resp.json();

    if (data.error) {
      alert("Lỗi chạy backtest: " + data.error);
      return;
    }

    document.getElementById("bt-net-profit").innerText = `$${(data.net_profit || 0).toFixed(2)}`;
    document.getElementById("bt-return-pct").innerText = `(${(data.return_pct || 0) >= 0 ? '+' : ''}${(data.return_pct || 0).toFixed(2)}%)`;
    document.getElementById("bt-win-rate").innerText = `${(data.win_rate || 0).toFixed(1)}%`;
    document.getElementById("bt-trade-counts").innerText = `${data.win_trades || 0} thắng / ${data.loss_trades || 0} thua`;
    document.getElementById("bt-profit-factor").innerText = (data.profit_factor || 0).toFixed(2);
    document.getElementById("bt-max-dd").innerText = `${(data.max_drawdown || 0).toFixed(2)}%`;

    const tradesBody = document.getElementById("bt-trades-body");
    if (tradesBody && data.trade_log) {
      tradesBody.innerHTML = data.trade_log.slice(0, 30).map(t => `
        <tr>
          <td>${t.entry_time || '--'}</td>
          <td>${t.exit_time || '--'}</td>
          <td style="font-family: var(--font-mono);">$${(t.entry_price || 0).toFixed(4)}</td>
          <td style="font-family: var(--font-mono);">$${(t.exit_price || 0).toFixed(4)}</td>
          <td style="font-family: var(--font-mono); color: ${(t.pnl || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'};">
            ${(t.pnl || 0) >= 0 ? '+' : ''}$${(t.pnl || 0).toFixed(2)}
          </td>
          <td><span class="${(t.pnl_pct || 0) >= 0 ? 'badge-green' : 'badge-red'}">${(t.pnl_pct || 0) >= 0 ? '+' : ''}${(t.pnl_pct || 0).toFixed(2)}%</span></td>
          <td style="font-size: 0.75rem; color: var(--text-muted);">${t.exit_reason || '--'}</td>
        </tr>
      `).join("");
    }

    if (resContainer) resContainer.style.display = "block";
  } catch (err) {
    alert("Không thể kết nối đến server: " + err);
  } finally {
    if (btn) btn.disabled = false;
    if (loading) loading.style.display = "none";
  }
}

function toggleAudioAlert() {
  isAudioAlertEnabled = !isAudioAlertEnabled;
  const txt = document.getElementById("audio-status-text");
  const ico = document.getElementById("audio-icon");
  if (txt) txt.innerText = isAudioAlertEnabled ? "Chuông: BẬT" : "Chuông: TẮT";
  if (ico) ico.innerText = "";
}

/* ─── ML Multiplier Research Modal & Interactive Scatter Plot ─── */
let mlResearchData = null;

function openMultiplierResearchModal() {
  const modal = document.getElementById("multiplier-research-modal");
  if (modal) {
    modal.style.display = "flex";
    fetchAndRenderMultiplierResearch();
  }
}

function closeMultiplierResearchModal() {
  const modal = document.getElementById("multiplier-research-modal");
  if (modal) modal.style.display = "none";
}

async function fetchAndRenderMultiplierResearch() {
  try {
    const res = await fetch("/api/ml/pump_multiplier_research");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;
    mlResearchData = data;

    const events = data.events || [];
    const model = data.model_summary || {};

    // Update Stats
    const evCountEl = document.getElementById("ml-stat-events");
    if (evCountEl) evCountEl.innerText = events.length;

    const meanNEl = document.getElementById("ml-stat-mean-n");
    if (meanNEl && events.length > 0) {
      const sumN = events.reduce((acc, e) => acc + (e.n_actual || 0), 0);
      meanNEl.innerText = `${(sumN / events.length).toFixed(1)}x`;
    }

    const maeEl = document.getElementById("ml-stat-mae");
    if (maeEl && model.loo_mae_ridge !== undefined) {
      const avgMae = ((model.loo_mae_ridge + model.loo_mae_rf) / 2).toFixed(3);
      maeEl.innerText = avgMae;
    }

    // Render Table
    const tbody = document.getElementById("ml-events-body");
    if (tbody) {
      tbody.innerHTML = events.map(e => {
        const bottomFmt = e.pre_pump_price < 0.001 ? e.pre_pump_price.toFixed(8) : e.pre_pump_price < 1 ? e.pre_pump_price.toFixed(4) : e.pre_pump_price.toFixed(2);
        const peakFmt = e.peak_price < 0.001 ? e.peak_price.toFixed(8) : e.peak_price < 1 ? e.peak_price.toFixed(4) : e.peak_price.toFixed(2);
        
        let nBadgeClass = "badge-cyan";
        if (e.n_actual >= 20) nBadgeClass = "badge-red";
        else if (e.n_actual >= 10) nBadgeClass = "badge-yellow";

        return `
          <tr>
            <td style="font-weight: 700; color: #fff;">${e.symbol}</td>
            <td><span class="phase-badge phase-normal" style="font-size: 0.72rem;">${e.tier_code}</span></td>
            <td style="font-family: var(--font-mono); color: var(--accent-cyan);">$${bottomFmt}</td>
            <td style="font-family: var(--font-mono); color: var(--accent-green);">$${peakFmt}</td>
            <td><span class="${nBadgeClass}" style="font-weight: 800; font-family: var(--font-mono); font-size: 0.85rem;">${(e.n_actual || 0).toFixed(2)}x</span></td>
            <td style="font-family: var(--font-mono); color: var(--text-muted);">${(e.vol_spike_ratio || 0).toFixed(1)}x</td>
            <td style="font-size: 0.76rem; color: var(--text-dim);">${e.event_date || '--'}</td>
          </tr>
        `;
      }).join("");
    }

    // Render Canvas Scatter Plot
    drawMultiplierScatterPlot(events);

  } catch (err) {
    console.error("Error fetching ML research data:", err);
  }
}

function drawMultiplierScatterPlot(events) {
  const canvas = document.getElementById("ml-scatter-canvas");
  if (!canvas || !events || events.length === 0) return;

  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;

  // Margins
  const mLeft = 65;
  const mRight = 35;
  const mTop = 30;
  const mBottom = 45;

  const pW = w - mLeft - mRight;
  const pH = h - mTop - mBottom;

  // Background
  ctx.fillStyle = "#0B0F17";
  ctx.fillRect(0, 0, w, h);

  // Compute log ranges
  const logPrices = events.map(e => Math.log10(Math.max(e.pre_pump_price, 1e-7)));
  const logNs = events.map(e => Math.log10(Math.max(e.n_actual, 1.0)));

  const minLogP = Math.floor(Math.min(...logPrices));
  const maxLogP = Math.ceil(Math.max(...logNs, Math.max(...logPrices)));
  const minLogN = 0; // log10(1) = 0
  const maxLogN = Math.ceil(Math.max(...logNs) * 1.1);

  const xRange = maxLogP - minLogP;
  const yRange = maxLogN - minLogN;

  function toX(lp) {
    return mLeft + ((lp - minLogP) / xRange) * pW;
  }

  function toY(ln) {
    return mTop + pH - ((ln - minLogN) / yRange) * pH;
  }

  // Draw Gridlines & Axis Labels
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.07)";
  ctx.fillStyle = "rgba(160, 175, 200, 0.6)";
  ctx.font = "10px Inter, monospace";
  ctx.textAlign = "center";

  // X Axis Ticks (Price Powers of 10)
  for (let lp = minLogP; lp <= maxLogP; lp++) {
    const x = toX(lp);
    ctx.beginPath();
    ctx.moveTo(x, mTop);
    ctx.lineTo(x, mTop + pH);
    ctx.stroke();

    let valStr = `$10^${lp}`;
    if (lp === -5) valStr = "$0.00001";
    else if (lp === -4) valStr = "$0.0001";
    else if (lp === -3) valStr = "$0.001";
    else if (lp === -2) valStr = "$0.01";
    else if (lp === -1) valStr = "$0.1";
    else if (lp === 0) valStr = "$1";
    else if (lp === 1) valStr = "$10";
    else if (lp === 2) valStr = "$100";

    ctx.fillText(valStr, x, mTop + pH + 16);
  }

  // Y Axis Ticks (Multiplier n Powers of 10)
  ctx.textAlign = "right";
  for (let ln = minLogN; ln <= maxLogN; ln++) {
    const y = toY(ln);
    ctx.beginPath();
    ctx.moveTo(mLeft, y);
    ctx.lineTo(mLeft + pW, y);
    ctx.stroke();

    let nStr = `${Math.pow(10, ln)}x`;
    ctx.fillText(nStr, mLeft - 8, y + 3);
  }

  // Axes Title
  ctx.fillStyle = "rgba(0, 240, 255, 0.7)";
  ctx.font = "11px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("← Giá Đáy Trước Pump (Log10 Price) →", mLeft + pW / 2, h - 8);

  ctx.save();
  ctx.translate(14, mTop + pH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("← Bội Số Pump n (Log10 Multiplier) →", 0, 0);
  ctx.restore();

  // Draw Trendline (Empirical fit)
  ctx.beginPath();
  ctx.strokeStyle = "rgba(0, 240, 255, 0.35)";
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 4]);

  const x1 = minLogP;
  const y1 = toY(1.8 - 0.15 * (minLogP - (-5)));
  const x2 = maxLogP;
  const y2 = toY(0.45);

  ctx.moveTo(toX(x1), y1);
  ctx.lineTo(toX(x2), y2);
  ctx.stroke();
  ctx.setLineDash([]); // Reset line dash

  // Draw Data Points
  events.forEach(e => {
    const lp = Math.log10(Math.max(e.pre_pump_price, 1e-7));
    const ln = Math.log10(Math.max(e.n_actual, 1.0));

    const cx = toX(lp);
    const cy = toY(ln);

    let color = "#00F0FF";
    let r = 5;
    if (e.n_actual >= 20) {
      color = "#FF3366";
      r = 7.5;
    } else if (e.n_actual >= 10) {
      color = "#FFB800";
      r = 6;
    }

    // Outer Glow
    ctx.beginPath();
    ctx.arc(cx, cy, r + 3, 0, Math.PI * 2);
    ctx.fillStyle = color.replace(")", ", 0.25)").replace("rgb", "rgba").replace("#FF3366", "rgba(255,51,102,0.25)").replace("#FFB800", "rgba(255,184,0,0.25)").replace("#00F0FF", "rgba(0,240,255,0.25)");
    ctx.fill();

    // Core Dot
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // Coin Label (for notable cases)
    if (e.n_actual >= 20 || e.symbol === "DEXEUSDT" || e.symbol === "AKEUSDT" || e.symbol === "TUTUSDT" || e.symbol === "BANKUSDT" || e.symbol === "BEATUSDT" || e.symbol === "VELVETUSDT") {
      ctx.font = "bold 9.5px Inter, sans-serif";
      ctx.fillStyle = "#FFFFFF";
      ctx.textAlign = "center";
      ctx.fillText(`${e.symbol.replace("USDT", "")} (${e.n_actual.toFixed(0)}x)`, cx, cy - r - 4);
    }
  });
}

