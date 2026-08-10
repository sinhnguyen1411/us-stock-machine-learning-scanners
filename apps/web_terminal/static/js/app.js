/**
 * DeepAlpha Binance Futures Scanner — Frontend Logic
 * Fully synchronized with Author's 7-Layer Core Framework & Risk Management
 */

let currentSymbol = "TUTUSDT";
let currentTimeframe = "1m";
let chart = null;
let candleSeries = null;
let volumeSeries = null;
let activePriceLines = [];
let refreshInterval = null;
let radarInterval = null;
let audioAlertEnabled = true;
let audioCtx = null;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  try { initChart(); } catch (e) { console.error("initChart error:", e); }
  try { initRecentSymbols(); } catch (e) { console.error("initRecentSymbols error:", e); }
  try { loadTopMovers(); } catch (e) { console.error("loadTopMovers error:", e); }
  try { loadSymbol(currentSymbol); } catch (e) { console.error("loadSymbol error:", e); }
  try { loadPortfolio(); } catch (e) { console.error("loadPortfolio error:", e); }
  try { loadLiveRadar(); } catch (e) { console.error("loadLiveRadar error:", e); }
  try { loadTopPumpCandidates(); } catch (e) { console.error("loadTopPumpCandidates error:", e); }

  // Search input Enter key
  const searchInput = document.getElementById("symbol-search");
  if (searchInput) {
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const val = searchInput.value.trim().toUpperCase();
        if (val) loadSymbol(val);
      }
    });
  }

  const btnScan = document.getElementById("btn-scan-symbol");
  if (btnScan) {
    btnScan.addEventListener("click", () => {
      const val = searchInput ? searchInput.value.trim().toUpperCase() : "";
      if (val) loadSymbol(val);
    });
  }

  // Auto-refresh every 4 seconds
  refreshInterval = setInterval(() => {
    refreshCurrentData();
    loadPortfolio();
  }, 4000);

  // Live Radar & Top 10 refresh every 4 seconds
  radarInterval = setInterval(() => {
    loadLiveRadar();
    loadTopPumpCandidates();
  }, 4000);
});

// ─── Audio Alert Synthesizer (Web Audio API) ─────────────────────────
function toggleAudioAlert() {
  audioAlertEnabled = !audioAlertEnabled;
  const icon = document.getElementById("audio-icon");
  const txt = document.getElementById("audio-status-text");
  if (audioAlertEnabled) {
    if (icon) icon.innerText = "🔊";
    if (txt) txt.innerText = "Chuông: BẬT";
    playSignalSound("PUMP_LONG");
  } else {
    if (icon) icon.innerText = "🔇";
    if (txt) txt.innerText = "Chuông: TẮT";
  }
}

function playSignalSound(action) {
  if (!audioAlertEnabled) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!audioCtx) audioCtx = new AudioContext();
    if (audioCtx.state === "suspended") audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (action === "PUMP_LONG") {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880.0, audioCtx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } else if (action === "DUMP_SHORT") {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(740.0, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(370.0, audioCtx.currentTime + 0.25);
      gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    }
  } catch (e) {
    console.debug("Audio play error:", e);
  }
}

// ─── Recent Symbols Management (Max 20 Unique Items) ─────────────────
const RECENT_STORAGE_KEY = "deepalpha_recent_symbols";
const DEFAULT_RECENT = ["TUTUSDT", "AKEUSDT", "BMTUSDT", "CAPUSDT", "BTCUSDT", "ETHUSDT", "ESPUSDT", "COAIUSDT", "BOMEUSDT", "SOLUSDT"];

function getRecentSymbols() {
  try {
    const stored = localStorage.getItem(RECENT_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (e) {
    console.debug("Failed to read recent symbols:", e);
  }
  return [...DEFAULT_RECENT];
}

function saveRecentSymbols(symbols) {
  try {
    localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(symbols));
  } catch (e) {
    console.debug("Failed to save recent symbols:", e);
  }
}

function addRecentSymbol(sym) {
  if (!sym) return;
  sym = sym.trim().toUpperCase();
  if (!sym.endsWith("USDT")) sym += "USDT";

  let symbols = getRecentSymbols();
  symbols = symbols.filter(s => s !== sym);
  symbols.unshift(sym);
  symbols = symbols.slice(0, 20);

  saveRecentSymbols(symbols);
  renderRecentSymbols();
}

function renderRecentSymbols() {
  const container = document.getElementById("recent-symbols-list");
  const countEl = document.getElementById("recent-count");
  if (!container) return;

  const symbols = getRecentSymbols();
  if (countEl) countEl.innerText = symbols.length;

  if (symbols.length === 0) {
    container.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-dim);">Chưa có mã nào được tra cứu.</span>`;
    return;
  }

  container.innerHTML = symbols.map(sym => {
    const isActive = sym === currentSymbol;
    const isHot = ["TUTUSDT", "AKEUSDT", "BMTUSDT", "CAPUSDT"].includes(sym);
    return `
      <span 
        class="symbol-chip ${isHot ? 'hot' : ''} ${isActive ? 'active-chip' : ''}" 
        style="${isActive ? 'border-color: var(--accent-cyan); background: rgba(0, 242, 254, 0.15); color: var(--accent-cyan); font-weight: 700;' : ''}"
        onclick="loadSymbol('${sym}')"
        title="Bấm để xem ${sym}"
      >
        ${sym}
      </span>
    `;
  }).join("");
}

function clearRecentSymbols() {
  saveRecentSymbols([]);
  renderRecentSymbols();
}

function initRecentSymbols() {
  renderRecentSymbols();
}

// ─── Initialize TradingView Lightweight Charts ───────────────────────
function initChart() {
  const chartContainer = document.getElementById("chart-area");
  if (!chartContainer) return;
  chartContainer.innerHTML = "";

  if (typeof LightweightCharts === "undefined") {
    console.warn("LightweightCharts library is loading, retrying in 300ms...");
    setTimeout(initChart, 300);
    return;
  }

  try {
    chart = LightweightCharts.createChart(chartContainer, {
      layout: {
        background: { color: "#0d121c" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.04)" },
        horzLines: { color: "rgba(255, 255, 255, 0.04)" },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        autoScale: true,
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Candlestick Series
    candleSeries = chart.addCandlestickSeries({
      upColor: "#00e676",
      downColor: "#ff3366",
      borderVisible: false,
      wickUpColor: "#00e676",
      wickDownColor: "#ff3366",
    });

    // Price scale margins: leave 25% space at bottom for volume
    chart.priceScale('right').applyOptions({
      scaleMargins: {
        top: 0.08,
        bottom: 0.25,
      },
    });

    // Volume Histogram Series (occupies bottom 18%)
    volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.82,
        bottom: 0.0,
      },
    });

    window.addEventListener("resize", () => {
      if (chart && chartContainer) {
        chart.applyOptions({
          width: chartContainer.clientWidth,
          height: chartContainer.clientHeight,
        });
      }
    });
  } catch (e) {
    console.error("Failed to initialize TradingView Lightweight Charts:", e);
  }
}

// ─── Load Symbol Analysis ────────────────────────────────────────────
async function loadSymbol(sym) {
  if (!sym) return;
  sym = sym.trim().toUpperCase();
  if (!sym.endsWith("USDT")) sym += "USDT";
  currentSymbol = sym;

  const searchInput = document.getElementById("symbol-search");
  if (searchInput) searchInput.value = sym;

  const symTitle = document.getElementById("active-symbol");
  if (symTitle) symTitle.innerText = sym;

  renderRecentSymbols();

  try {
    const res = await fetch(`/api/analyze/${sym}?interval=${currentTimeframe}`);
    const data = await res.json();

    if (data.error) {
      alert(`Lỗi: ${data.error}`);
      return;
    }

    addRecentSymbol(sym);
    renderAnalysisData(data);
  } catch (err) {
    console.error("Failed to load symbol:", err);
  }
}

// Refresh current symbol data quietly
async function refreshCurrentData() {
  try {
    const res = await fetch(`/api/analyze/${currentSymbol}?interval=${currentTimeframe}`);
    const data = await res.json();
    if (!data.error) {
      renderAnalysisData(data);
    }
  } catch (err) {
    console.debug("Silent refresh error:", err);
  }
}

// ─── Render Data & Price Lines ───────────────────────────────────────
function renderAnalysisData(data) {
  if (!data) return;

  // 1. Header & Price & Coin Tier
  const priceEl = document.getElementById("active-price");
  if (priceEl) priceEl.innerText = `$${formatPrice(data.price)}`;

  const changeEl = document.getElementById("active-change");
  if (changeEl) {
    changeEl.innerText = `${data.pct_24h >= 0 ? "+" : ""}${data.pct_24h.toFixed(2)}%`;
    changeEl.className = `asset-change ${data.pct_24h >= 0 ? "badge-green" : "badge-red"}`;
  }

  if (data.tier) {
    const tierEl = document.getElementById("active-tier");
    if (tierEl) {
      tierEl.innerText = data.tier.name;
    }
  }

  // 2. Candlestick & Volume Chart
  if (data.candles && data.candles.length > 0 && candleSeries) {
    const candleData = data.candles.map(c => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    const volData = data.candles.map(c => ({
      time: c.time,
      value: c.volume,
      color: c.close >= c.open ? "rgba(0, 230, 118, 0.30)" : "rgba(255, 51, 102, 0.30)",
    }));

    // Dynamic price formatting precision
    let precision = 4;
    let minMove = 0.0001;
    const p = Math.abs(Number(data.price) || 0);
    if (p < 0.00001) {
      precision = 8;
      minMove = 0.00000001;
    } else if (p < 0.001) {
      precision = 6;
      minMove = 0.000001;
    } else if (p < 0.1) {
      precision = 5;
      minMove = 0.00001;
    } else if (p < 1.0) {
      precision = 4;
      minMove = 0.0001;
    } else if (p < 50.0) {
      precision = 3;
      minMove = 0.001;
    } else {
      precision = 2;
      minMove = 0.01;
    }

    try {
      candleSeries.applyOptions({
        priceFormat: {
          type: 'price',
          precision: precision,
          minMove: minMove,
        },
      });

      candleSeries.setData(candleData);
      if (volumeSeries) volumeSeries.setData(volData);

      // ── 3. Render Direct Price Lines (SL, TP1, TP2, TP3) on Chart ──
      const tp = data.trade_plan;
      if (tp) {
        activePriceLines.forEach(line => {
          try { candleSeries.removePriceLine(line); } catch (e) { }
        });
        activePriceLines = [];

        // Stop Loss line (Red dashed)
        if (tp.stop_loss) {
          const slLine = candleSeries.createPriceLine({
            price: tp.stop_loss,
            color: '#ff3366',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: 'SL (1.5x ATR)',
          });
          activePriceLines.push(slLine);
        }

        // TP1 line (+5% green)
        if (tp.tp1) {
          const tp1Line = candleSeries.createPriceLine({
            price: tp.tp1,
            color: '#00e676',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'TP1 (Chốt 40%)',
          });
          activePriceLines.push(tp1Line);
        }

        // TP2 line (+10% cyan)
        if (tp.tp2) {
          const tp2Line = candleSeries.createPriceLine({
            price: tp.tp2,
            color: '#00f2fe',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'TP2 (Trailing 3%)',
          });
          activePriceLines.push(tp2Line);
        }
      }
    } catch (e) {
      console.warn("Chart rendering warning:", e);
    }
  }

  // 4. Verdict Card
  const v = data.verdict;
  const verdictCard = document.getElementById("verdict-card");
  if (verdictCard && v) {
    verdictCard.className = `verdict-banner verdict-${v.action}`;

    let actionText = "⏳ TRẠNG THÁI TRUNG LẬP";
    let barColor = "var(--text-muted)";

    if (v.action === "PUMP_LONG") {
      actionText = "🚀 PHÁT HIỆN TÍN HIỆU PUMP LONG!";
      barColor = "var(--accent-green)";
      if (v.confidence >= 75) playSignalSound("PUMP_LONG");
    } else if (v.action === "DUMP_SHORT") {
      actionText = "🔻 PHÁT HIỆN TÍN HIỆU DUMP SHORT (BẮT ĐỈNH)!";
      barColor = "var(--accent-red)";
      if (v.confidence >= 75) playSignalSound("DUMP_SHORT");
    } else if (v.action === "OVERSOLD_REBOUND") {
      actionText = "⚡ QUÁ BÁN SÂU (TIỀM NĂNG HỒI KỸ THUẬT)";
      barColor = "var(--accent-yellow)";
    }

    const vText = document.getElementById("verdict-text");
    if (vText) vText.innerText = actionText;

    const vConf = document.getElementById("verdict-conf");
    if (vConf) vConf.innerText = `${v.confidence}% Độ Tin Cậy`;

    const confBar = document.getElementById("confidence-bar");
    if (confBar) {
      confBar.style.width = `${v.confidence}%`;
      confBar.style.background = barColor;
    }

    const reasonsEl = document.getElementById("verdict-reasons");
    if (reasonsEl && v.reasons) {
      reasonsEl.innerHTML = v.reasons.map(r => `<div>• ${r}</div>`).join("");
    }
  }

  // 5. Scorecard with Adaptive Tier Thresholds
  const sc = data.scorecard;
  if (sc) {
    const reqVol = data.tier ? data.tier.req_vol_spike : 5.0;
    const reqPrice = data.tier ? (data.tier.req_price_spike * 100.0) : 3.0;
    const reqBuy = data.tier ? (data.tier.req_buy_ratio * 100.0) : 65.0;

    const elVol = document.getElementById("m-vol-ratio");
    if (elVol) elVol.innerText = `${sc.vol_ratio}x`;

    const elBuy = document.getElementById("m-buy-ratio");
    if (elBuy) elBuy.innerText = `${sc.buy_ratio}%`;

    const elPrice = document.getElementById("m-price-change");
    if (elPrice) elPrice.innerText = `${sc.price_change_5m >= 0 ? '+' : ''}${sc.price_change_5m}%`;

    const elRsi = document.getElementById("m-rsi");
    if (elRsi) elRsi.innerText = sc.rsi;

    const elGreen = document.getElementById("m-green");
    if (elGreen) elGreen.innerText = `${sc.green_candles}/3 Nến`;

    const elOi = document.getElementById("m-oi");
    if (elOi) elOi.innerText = Number(sc.open_interest).toLocaleString();

    // Layer 1: Vol Spike (Adaptive)
    const bVol = document.getElementById("badge-vol");
    if (bVol) {
      if (sc.vol_ratio >= reqVol) {
        bVol.className = "layer-badge badge-pass";
        bVol.innerText = `✓ ĐẠT (≥${reqVol}x)`;
      } else {
        bVol.className = "layer-badge badge-fail";
        bVol.innerText = `✗ CHƯA ĐẠT (≥${reqVol}x)`;
      }
    }

    // Layer 2: Buy Ratio (Adaptive)
    const bBuy = document.getElementById("badge-buy");
    if (bBuy) {
      if (sc.buy_ratio >= reqBuy) {
        bBuy.className = "layer-badge badge-pass";
        bBuy.innerText = `✓ ĐẠT (≥${reqBuy.toFixed(0)}%)`;
      } else {
        bBuy.className = "layer-badge badge-fail";
        bBuy.innerText = `✗ CHƯA ĐẠT (≥${reqBuy.toFixed(0)}%)`;
      }
    }

    // Layer 3: Price Spike 5M (Adaptive)
    const bPrice = document.getElementById("badge-price");
    if (bPrice) {
      if (sc.price_change_5m >= reqPrice) {
        bPrice.className = "layer-badge badge-pass";
        bPrice.innerText = `✓ ĐẠT (≥+${reqPrice.toFixed(1)}%)`;
      } else {
        bPrice.className = "layer-badge badge-fail";
        bPrice.innerText = `✗ CHƯA ĐẠT (≥+${reqPrice.toFixed(1)}%)`;
      }
    }

    // Layer 4: RSI (60 - 85)
    const bRsi = document.getElementById("badge-rsi");
    if (bRsi) {
      if (sc.rsi >= 60 && sc.rsi <= 85) {
        bRsi.className = "layer-badge badge-pass";
        bRsi.innerText = "✓ ĐẠT (60-85)";
      } else {
        bRsi.className = "layer-badge badge-fail";
        bRsi.innerText = sc.rsi < 60 ? "Yếu (<60)" : "Quá Mua (>85)";
      }
    }

    // Layer 5: Green Candles (>= 3)
    const bGreen = document.getElementById("badge-green");
    if (bGreen) {
      if (sc.green_candles >= 3) {
        bGreen.className = "layer-badge badge-pass";
        bGreen.innerText = "✓ ĐẠT (3/3)";
      } else {
        bGreen.className = "layer-badge badge-fail";
        bGreen.innerText = `✗ ${sc.green_candles}/3 Nến`;
      }
    }

    // Layer 6: Open Interest & Funding Rate
    const bOi = document.getElementById("badge-oi");
    if (bOi) {
      bOi.className = "layer-badge badge-pass";
      bOi.innerText = `${sc.funding_rate > 0 ? '+' : ''}${sc.funding_rate.toFixed(3)}% Funding`;
    }
  }

  // 6. Target Levels
  const tpData = data.trade_plan;
  if (tpData) {
    const tEntry = document.getElementById("tgt-entry");
    if (tEntry) tEntry.innerText = `$${formatPrice(tpData.entry)}`;

    const tSl = document.getElementById("tgt-sl");
    if (tSl) tSl.innerText = `$${formatPrice(tpData.stop_loss)}`;

    const tTp1 = document.getElementById("tgt-tp1");
    if (tTp1) tTp1.innerText = `$${formatPrice(tpData.tp1)}`;

    const tTp2 = document.getElementById("tgt-tp2");
    if (tTp2) tTp2.innerText = `$${formatPrice(tpData.tp2)}`;
  }
}

// Change Timeframe (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 1d)
function changeTimeframe(tf) {
  currentTimeframe = tf;
  document.querySelectorAll(".tf-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("onclick").includes(`'${tf}'`));
  });
  loadSymbol(currentSymbol);
}

// ─── Top 10 High-Probability Pump Candidates Loader ──────────────────
async function loadTopPumpCandidates() {
  try {
    const res = await fetch("/api/top_pump_candidates");
    const data = await res.json();
    const body = document.getElementById("top-pump-body");
    if (!body) return;

    if (!data.candidates || data.candidates.length === 0) {
      body.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim); padding: 20px;">Đang quét toàn sàn Binance Futures... Dữ liệu Top 10 đang được khởi tạo!</td></tr>`;
      return;
    }

    body.innerHTML = data.candidates.map((c, idx) => {
      const rankNum = idx + 1;
      const rankClass = rankNum === 1 ? "rank-1" : (rankNum === 2 ? "rank-2" : (rankNum === 3 ? "rank-3" : "rank-other"));
      
      const score = c.pump_score;
      let scoreColor = "var(--accent-yellow)";
      if (score >= 75) scoreColor = "var(--accent-green)";
      else if (score >= 60) scoreColor = "var(--accent-cyan)";

      const isCurrent = c.symbol === currentSymbol;

      return `
        <tr style="cursor: pointer; ${isCurrent ? 'background: rgba(0, 242, 254, 0.06);' : ''}" onclick="loadSymbol('${c.symbol}')">
          <td><span class="rank-badge ${rankClass}">${rankNum}</span></td>
          <td>
            <div style="display: flex; flex-direction: column;">
              <strong style="color: var(--accent-cyan); font-size: 1.05rem;">${c.symbol}</strong>
              <span style="font-size: 0.7rem; color: var(--text-dim);">${c.tier?.name || ''}</span>
            </div>
          </td>
          <td>$${formatPrice(c.price)}</td>
          <td>
            <span class="${c.pct_24h >= 0 ? 'badge-green' : 'badge-red'}">
              ${c.pct_24h >= 0 ? '+' : ''}${c.pct_24h.toFixed(2)}%
            </span>
          </td>
          <td>
            <div class="pump-score-wrap">
              <span class="pump-score-num" style="color: ${scoreColor};">${score}</span>
              <div class="pump-score-track">
                <div class="pump-score-bar" style="width: ${score}%; background: ${scoreColor};"></div>
              </div>
            </div>
          </td>
          <td><span class="stage-tag ${c.stage_class}">${c.stage_tag}</span></td>
          <td><strong style="color: ${c.vol_ratio >= 3.0 ? 'var(--accent-green)' : 'var(--text-main)'};">${c.vol_ratio}x</strong></td>
          <td>${c.buy_ratio}%</td>
          <td><span class="${c.price_change_5m >= 0 ? 'badge-green' : 'badge-red'}" style="font-size: 0.75rem;">${c.price_change_5m >= 0 ? '+' : ''}${c.price_change_5m}%</span></td>
          <td>${c.rsi}</td>
          <td>
            <div style="display: flex; gap: 6px;">
              <button class="btn-close-pos" style="border-color: var(--accent-cyan); color: var(--accent-cyan); background: rgba(0, 242, 254, 0.1);" onclick="event.stopPropagation(); loadSymbol('${c.symbol}')">
                Soi Nến 🔍
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    console.debug("Top Pump Candidates fetch error:", e);
  }
}

// ─── Live Signals Radar Loader ───────────────────────────────────────
async function loadLiveRadar() {
  try {
    const res = await fetch("/api/live_signals");
    const data = await res.json();
    const body = document.getElementById("radar-signals-body");
    if (!body) return;

    if (!data.signals || data.signals.length === 0) {
      body.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim);">Đang quét 526 cặp Binance Futures... Chưa có tín hiệu đột biến nào vượt ngưỡng.</td></tr>`;
      return;
    }

    body.innerHTML = data.signals.map(s => {
      const isPump = s.action === "PUMP_LONG";
      const isDump = s.action === "DUMP_SHORT";
      const badgeClass = isPump ? "badge-green" : (isDump ? "badge-red" : "layer-badge");
      const actionTitle = isPump ? "🚀 PUMP LONG" : (isDump ? "🔻 DUMP SHORT" : "⚡ ĐỘT BIẾN");

      return `
        <tr style="cursor: pointer;" onclick="loadSymbol('${s.symbol}')">
          <td style="color: var(--text-dim);">${s.detected_at}</td>
          <td><strong style="color: var(--accent-cyan); font-size: 1rem;">${s.symbol}</strong></td>
          <td>$${formatPrice(s.price)}</td>
          <td><span class="${s.pct_24h >= 0 ? 'badge-green' : 'badge-red'}">${s.pct_24h >= 0 ? '+' : ''}${s.pct_24h.toFixed(2)}%</span></td>
          <td><span class="${badgeClass}" style="padding: 3px 8px; border-radius: 4px; font-weight: 700;">${actionTitle}</span></td>
          <td><strong style="color: ${s.vol_ratio >= 5.0 ? 'var(--accent-green)' : 'var(--text-main)'};">${s.vol_ratio}x</strong></td>
          <td>${s.buy_ratio}%</td>
          <td>${s.rsi}</td>
          <td><strong style="color: var(--accent-cyan);">${s.confidence}%</strong></td>
          <td>
            <button class="btn-close-pos" style="border-color: var(--accent-cyan); color: var(--accent-cyan); background: rgba(0, 242, 254, 0.1);" onclick="event.stopPropagation(); loadSymbol('${s.symbol}')">
              Soi Nến 🔍
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    console.debug("Radar fetch error:", e);
  }
}

// ─── Top Movers Bar ──────────────────────────────────────────────────
async function loadTopMovers() {
  try {
    const res = await fetch("/api/top_movers");
    const data = await res.json();

    const container = document.getElementById("top-movers-container");
    if (!container) return;
    container.innerHTML = "";

    const allMovers = [...data.top_gainers.slice(0, 4), ...data.top_losers.slice(0, 2)];

    allMovers.forEach(m => {
      const card = document.createElement("div");
      card.className = "mover-card";
      card.onclick = () => loadSymbol(m.symbol);

      const isGain = m.pct_change >= 0;
      card.innerHTML = `
        <div class="mover-header">
          <span class="mover-symbol">${m.symbol}</span>
          <span class="mover-pct ${isGain ? 'badge-green' : 'badge-red'}">
            ${isGain ? '+' : ''}${m.pct_change.toFixed(2)}%
          </span>
        </div>
        <div class="mover-price">$${formatPrice(m.price)}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load top movers:", err);
  }
}

// ─── Paper Trading Portfolio ─────────────────────────────────────────
async function loadPortfolio() {
  try {
    const res = await fetch("/api/portfolio");
    const data = await res.json();

    const eqEl = document.getElementById("header-equity");
    if (eqEl) eqEl.innerText = `$${data.equity.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;

    const tbody = document.getElementById("positions-table-body");
    if (!tbody) return;

    if (!data.active_positions || data.active_positions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim);">Chưa có vị thế nào đang mở. Bấm "MỞ LONG / SHORT" ở trên để vào lệnh thử nghiệm!</td></tr>`;
      return;
    }

    tbody.innerHTML = data.active_positions.map(p => {
      const isProfit = p.unrealized_pnl >= 0;
      return `
        <tr>
          <td><strong style="color: var(--accent-cyan);">${p.symbol}</strong></td>
          <td><span class="${p.side === 'LONG' ? 'badge-green' : 'badge-red'}" style="padding: 2px 6px; border-radius: 4px;">${p.side} (${p.leverage}x)</span></td>
          <td>$${formatPrice(p.entry)}</td>
          <td>$${formatPrice(p.current_price)}</td>
          <td>$${p.notional.toFixed(2)}</td>
          <td style="color: ${isProfit ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 700;">
            ${isProfit ? '+' : ''}$${p.unrealized_pnl.toFixed(2)}
          </td>
          <td style="color: ${isProfit ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 700;">
            ${isProfit ? '+' : ''}${p.pnl_pct.toFixed(2)}%
          </td>
          <td style="color: var(--text-muted); font-size: 0.8rem;">${p.opened_at} (Hạn 2h)</td>
          <td>
            <button class="btn-close-pos" onclick="closePosition('${p.symbol}')">Đóng Vị Thế</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load portfolio:", err);
  }
}

async function executePaperTrade(side) {
  try {
    const res = await fetch("/api/trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: currentSymbol,
        side: side,
        notional: 100.0,
        leverage: 5,
      }),
    });

    const data = await res.json();
    if (data.error) {
      alert(`Không thể mở vị thế: ${data.error}`);
    } else {
      alert(`✅ ${data.message}`);
      loadPortfolio();
    }
  } catch (err) {
    alert("Lỗi kết nối khi mở vị thế.");
  }
}

async function closePosition(symbol) {
  try {
    const res = await fetch("/api/close_trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: symbol }),
    });

    const data = await res.json();
    if (data.error) {
      alert(`Lỗi: ${data.error}`);
    } else {
      alert(`✅ ${data.message}`);
      loadPortfolio();
    }
  } catch (err) {
    alert("Lỗi kết nối khi đóng vị thế.");
  }
}

// ─── Backtest Engine Modal & Execution ───────────────────────────────
function openBacktestModal() {
  const modal = document.getElementById("backtest-modal");
  const symInput = document.getElementById("bt-symbol");
  if (symInput) symInput.value = currentSymbol;
  if (modal) modal.style.display = "flex";
}

function closeBacktestModal() {
  const modal = document.getElementById("backtest-modal");
  if (modal) modal.style.display = "none";
}

async function runHistoricalBacktest() {
  const symbol = document.getElementById("bt-symbol").value.trim().toUpperCase();
  const days = parseInt(document.getElementById("bt-days").value, 10) || 7;

  const loadingEl = document.getElementById("bt-loading");
  const resContainer = document.getElementById("bt-results-container");
  if (loadingEl) loadingEl.style.display = "block";
  if (resContainer) resContainer.style.display = "none";

  try {
    const res = await fetch("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: symbol,
        days: days,
        initial_balance: 1000.0,
      }),
    });

    const data = await res.json();
    if (loadingEl) loadingEl.style.display = "none";

    if (data.error) {
      alert(`Lỗi Backtest: ${data.error}`);
      return;
    }

    if (resContainer) resContainer.style.display = "block";
    const netEl = document.getElementById("bt-net-profit");
    const isWin = data.net_profit >= 0;
    if (netEl) {
      netEl.innerText = `${isWin ? '+' : ''}$${data.net_profit.toFixed(2)}`;
      netEl.style.color = isWin ? "var(--accent-green)" : "var(--accent-red)";
    }

    const retEl = document.getElementById("bt-return-pct");
    if (retEl) {
      retEl.innerText = `(${isWin ? '+' : ''}${data.return_pct.toFixed(2)}%)`;
      retEl.style.color = isWin ? "var(--accent-green)" : "var(--accent-red)";
    }

    const winRateEl = document.getElementById("bt-win-rate");
    if (winRateEl) winRateEl.innerText = `${data.win_rate}%`;

    const tradeCountsEl = document.getElementById("bt-trade-counts");
    if (tradeCountsEl) tradeCountsEl.innerText = `${data.winning_trades} thắng / ${data.losing_trades} thua (Tổng ${data.total_trades} lệnh)`;

    const pfEl = document.getElementById("bt-profit-factor");
    if (pfEl) pfEl.innerText = data.profit_factor;

    const maxDdEl = document.getElementById("bt-max-dd");
    if (maxDdEl) maxDdEl.innerText = `${data.max_drawdown_pct}%`;

    // Render Trade Logs
    const tbody = document.getElementById("bt-trades-body");
    if (tbody) {
      if (!data.trades || data.trades.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">Không có tín hiệu vào lệnh nào thỏa mãn đủ 7 tầng trong ${days} ngày qua.</td></tr>`;
      } else {
        tbody.innerHTML = data.trades.map(t => {
          const isTradeWin = t.pnl >= 0;
          return `
            <tr>
              <td>${t.entry_time}</td>
              <td>${t.exit_time}</td>
              <td>$${formatPrice(t.entry_price)}</td>
              <td>$${formatPrice(t.exit_price)}</td>
              <td style="color: ${isTradeWin ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 700;">
                ${isTradeWin ? '+' : ''}$${t.pnl.toFixed(2)}
              </td>
              <td style="color: ${isTradeWin ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 700;">
                ${isTradeWin ? '+' : ''}${t.pnl_pct.toFixed(2)}%
              </td>
              <td><span class="layer-badge" style="font-size: 0.72rem;">${t.reason} (${t.duration_m}m)</span></td>
            </tr>
          `;
        }).join("");
      }
    }
  } catch (err) {
    if (loadingEl) loadingEl.style.display = "none";
    alert("Lỗi kết nối khi chạy Backtest.");
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────
function formatPrice(val) {
  const num = Number(val);
  if (isNaN(num)) return "0.00";
  if (num >= 1000) return num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (num >= 1) return num.toFixed(4);
  if (num >= 0.001) return num.toFixed(6);
  return num.toFixed(8);
}
