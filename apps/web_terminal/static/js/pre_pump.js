/**
 * DeepAlpha Pre-Pump Leading Radar Page Logic (4-Pillar Quantitative Engine)
 * Captures Ignition, Coiling, and Short Squeeze Anomalies (10x - 40x Pumps)
 */

let allPrePumpCandidates = [];
let currentPrePumpPhase = "ALL";
let isAudioAlertEnabled = true;

document.addEventListener("DOMContentLoaded", () => {
  fetchPrePumpRadar();
  setInterval(fetchPrePumpRadar, 3000);
});

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
        <td colspan="11" style="text-align: center; color: var(--text-dim); padding: 35px;">
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
