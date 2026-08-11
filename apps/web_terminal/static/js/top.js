/**
 * DeepAlpha Top 10 Pump Ranking Page Logic
 */

let allTopCandidates = [];
let currentTierFilter = "ALL";
let isAudioAlertEnabled = true;
let audioContext = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchTopPumpCandidates();
  setInterval(fetchTopPumpCandidates, 3000);
});

async function fetchTopPumpCandidates() {
  try {
    const res = await fetch("/api/top_pump_candidates");
    if (!res.ok) return;
    const data = await res.json();
    allTopCandidates = data.candidates || [];

    updateTopStats(data.timestamp);
    renderTopPumpTable();
  } catch (e) {
    console.debug("Error fetching top pump candidates:", e);
  }
}

function updateTopStats(timestamp) {
  const timeEl = document.getElementById("stat-last-time");
  if (timeEl && timestamp) {
    timeEl.innerText = timestamp + " UTC";
  }

  if (!allTopCandidates || allTopCandidates.length === 0) return;

  // 1. Top 1 Symbol & Score
  const top1 = allTopCandidates[0];
  const topSymEl = document.getElementById("stat-top-symbol");
  const topScoreEl = document.getElementById("stat-top-score");
  if (topSymEl && top1) {
    topSymEl.innerText = top1.symbol;
  }
  if (topScoreEl && top1) {
    topScoreEl.innerText = `Điểm tiềm năng: ${top1.pump_score.toFixed(1)}/100 (${top1.stage_tag || "Gom hàng"})`;
  }

  // 2. Breakout count (Vol ratio >= 5.0x or stage = Early Breakout)
  const breakouts = allTopCandidates.filter(c => (c.vol_ratio >= 4.0 || c.stage_class === "stage-breakout")).length;
  const brkEl = document.getElementById("stat-breakout-count");
  if (brkEl) {
    brkEl.innerText = breakouts;
  }

  // 3. Avg Buy Ratio
  const totalBuy = allTopCandidates.reduce((acc, cur) => acc + (cur.buy_ratio || 50), 0);
  const avgBuy = (totalBuy / allTopCandidates.length).toFixed(1);
  const avgBuyEl = document.getElementById("stat-avg-buy");
  if (avgBuyEl) {
    avgBuyEl.innerText = `${avgBuy}%`;
  }
}

function filterByTier(tier) {
  currentTierFilter = tier;
  document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }
  renderTopPumpTable();
}

function renderTopPumpTable() {
  const tbody = document.getElementById("top-pump-body");
  if (!tbody) return;

  let list = allTopCandidates;
  if (currentTierFilter !== "ALL") {
    list = allTopCandidates.filter(c => {
      const tName = (c.tier && c.tier.tier_name) || "";
      return tName.toUpperCase().includes(currentTierFilter.replace("_", " "));
    });
  }

  if (!list || list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" style="text-align: center; color: var(--text-dim); padding: 30px;">
          Chưa có ứng cử viên phù hợp với bộ lọc "${currentTierFilter}". Đang quét ngầm...
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = list.map((c, idx) => {
    const rank = idx + 1;
    const rankBadge = rank === 1 ? "🥇 #1" : rank === 2 ? "🥈 #2" : rank === 3 ? "🥉 #3" : `#${rank}`;
    const rankStyle = rank <= 3 ? "color: var(--accent-yellow); font-weight: 800;" : "color: var(--text-muted);";

    const pScore = Math.min(100, Math.max(0, c.pump_score || 0));
    const barColor = pScore >= 80 ? "var(--accent-red)" : pScore >= 60 ? "var(--accent-yellow)" : "var(--accent-cyan)";

    const pct = c.pct_24h || 0;
    const pctClass = pct >= 0 ? "badge-green" : "badge-red";
    const pctSign = pct >= 0 ? "+" : "";

    const priceFmt = c.price < 0.001 ? c.price.toFixed(6) : c.price < 1 ? c.price.toFixed(4) : c.price.toFixed(2);
    const p5m = c.price_change_5m || 0;
    const p5mClass = p5m >= 0 ? "color: var(--accent-green);" : "color: var(--accent-red);";

    return `
      <tr>
        <td style="${rankStyle}">${rankBadge}</td>
        <td>
          <div style="font-weight: 700; color: #fff; font-size: 0.95rem;">${c.symbol}</div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">${(c.tier && c.tier.tier_name) || "USDT-M"}</div>
        </td>
        <td style="font-family: var(--font-mono); font-weight: 600;">$${priceFmt}</td>
        <td><span class="${pctClass}">${pctSign}${pct.toFixed(2)}%</span></td>
        <td>
          <div class="pump-score-wrap">
            <span class="pump-score-num" style="color: ${barColor};">${pScore.toFixed(0)}</span>
            <div class="pump-score-track">
              <div class="pump-score-bar" style="width: ${pScore}%; background: ${barColor};"></div>
            </div>
          </div>
        </td>
        <td><span class="stage-pill ${c.stage_class || 'stage-accum'}">${c.stage_tag || 'Tích Lũy'}</span></td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: ${c.vol_ratio >= 3 ? 'var(--accent-yellow)' : 'var(--text-main)'};">
          ${(c.vol_ratio || 0).toFixed(1)}x
        </td>
        <td style="font-family: var(--font-mono); color: ${c.buy_ratio >= 65 ? 'var(--accent-green)' : 'var(--text-main)'};">
          ${(c.buy_ratio || 50).toFixed(1)}%
        </td>
        <td style="font-family: var(--font-mono); ${p5mClass}">
          ${p5m >= 0 ? '+' : ''}${p5m.toFixed(2)}%
        </td>
        <td style="font-family: var(--font-mono); font-weight: 600;">
          ${(c.rsi || 50).toFixed(1)}
        </td>
        <td>
          <a href="/?symbol=${c.symbol}" class="btn-inspect" title="Mở biểu đồ nến và 7 tầng xác thực">
            <span>🔍 Soi Nến</span>
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
  if (ico) ico.innerText = isAudioAlertEnabled ? "🔊" : "🔇";
}
