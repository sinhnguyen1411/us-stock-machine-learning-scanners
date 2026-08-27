/**
 * DeepAlpha US Stock & TradFi Futures Dedicated Inspection Workstation
 */

let proChart = null;
let candleSeries = null;
let volumeSeries = null;
let currentInterval = "5m";
let currentPriceLines = [];
let audioAlertEnabled = true;
let lastSignalState = null;

document.addEventListener("DOMContentLoaded", () => {
  initProChart();
  fetchStockDetails();
  fetchSectorPeers();
  setInterval(fetchStockDetails, 3500);
});

function initProChart() {
  const container = document.getElementById("pro-chart-container");
  if (!container || !window.LightweightCharts) return;

  container.innerHTML = "";

  proChart = LightweightCharts.createChart(container, {
    width: container.clientWidth || 800,
    height: 500,
    layout: {
      backgroundColor: "#0c1017",
      textColor: "#94a3b8",
      fontSize: 12,
      fontFamily: "'JetBrains Mono', 'Inter', monospace",
    },
    grid: {
      vertLines: { color: "rgba(255, 255, 255, 0.04)" },
      horzLines: { color: "rgba(255, 255, 255, 0.04)" },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: "rgba(0, 242, 254, 0.4)", width: 1, style: 3 },
      horzLine: { color: "rgba(0, 242, 254, 0.4)", width: 1, style: 3 },
    },
    rightPriceScale: {
      borderColor: "rgba(255, 255, 255, 0.08)",
      scaleMargins: { top: 0.1, bottom: 0.2 },
    },
    timeScale: {
      borderColor: "rgba(255, 255, 255, 0.08)",
      timeVisible: true,
      secondsVisible: false,
    },
  });

  // Candlestick series
  candleSeries = proChart.addCandlestickSeries({
    upColor: "#00e676",
    downColor: "#ff3366",
    borderUpColor: "#00e676",
    borderDownColor: "#ff3366",
    wickUpColor: "#00e676",
    wickDownColor: "#ff3366",
  });

  // Volume histogram overlay
  volumeSeries = proChart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "",
    scaleMargins: { top: 0.8, bottom: 0.0 },
  });

  window.addEventListener("resize", () => {
    if (proChart && container) {
      proChart.applyOptions({ width: container.clientWidth });
    }
  });
}

function changeTradFiTimeframe(tf) {
  currentInterval = tf;
  document.querySelectorAll(".timeframe-btn").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }
  fetchStockDetails();
}

async function fetchStockDetails() {
  try {
    const res = await fetch(`/api/tradfi/analyze/${CURRENT_SYMBOL}?interval=${currentInterval}`);
    if (!res.ok) return;
    const data = await res.json();

    updateHeaderBanner(data);
    updateProChart(data);
    updateDiagnosticMatrix(data);
    updateTradePlan(data);
    updateAICommentary(data);
    updateMicrostructure(data);
    updateSessionPill(data.session);
  } catch (e) {
    console.debug("Error fetching stock detail:", e);
  }
}

function updateHeaderBanner(data) {
  const price = data.price || 0;
  const pct = data.pct_24h || 0;
  const mlScore = data.ml_score || 50;
  const sigTag = data.signal_tag || "TÍCH LŨY";
  const sigClass = data.signal_class || "tradfi-signal-neutral";

  // Price & Pct
  const priceEl = document.getElementById("header-stock-price");
  const pctEl = document.getElementById("header-stock-pct");
  if (priceEl) priceEl.innerText = `$${formatStockPrice(price)}`;
  if (pctEl) {
    pctEl.innerText = `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}% (24H)`;
    pctEl.className = pct >= 0 ? "trend-up" : "trend-down";
  }

  // Score & Signal
  const scoreEl = document.getElementById("header-ml-score-text");
  const badgeEl = document.getElementById("header-signal-badge");
  if (scoreEl) {
    scoreEl.innerText = `${mlScore.toFixed(0)} / 100`;
    scoreEl.style.color = mlScore >= 75 ? "var(--accent-cyan)" : mlScore >= 60 ? "var(--accent-green)" : mlScore >= 40 ? "var(--accent-yellow)" : "var(--accent-red)";
  }
  if (badgeEl) {
    badgeEl.innerText = sigTag;
    badgeEl.className = `signal-tag ${sigClass}`;
  }

  // Audio alert if breakout triggered
  if (audioAlertEnabled && data.signal === "STRONG_BUY_BREAKOUT" && lastSignalState !== "STRONG_BUY_BREAKOUT") {
    playNotificationSound();
  }
  lastSignalState = data.signal;
}

function updateProChart(data) {
  if (!candleSeries || !data.candles || data.candles.length === 0) return;

  const candleData = [];
  const volumeData = [];

  data.candles.forEach(c => {
    candleData.push({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    });
    volumeData.push({
      time: c.time,
      value: c.volume,
      color: c.close >= c.open ? "rgba(0, 230, 118, 0.35)" : "rgba(255, 51, 102, 0.35)",
    });
  });

  candleSeries.setData(candleData);
  volumeSeries.setData(volumeData);

  const countEl = document.getElementById("chart-candle-count");
  if (countEl) countEl.innerText = `${candleData.length} Nến Vi Mô (${currentInterval.toUpperCase()})`;

  // Clear previous dynamic price lines
  currentPriceLines.forEach(pl => candleSeries.removePriceLine(pl));
  currentPriceLines = [];

  // 1. VWAP Line (Cyan Dashed)
  if (data.vwap) {
    const vwapLine = candleSeries.createPriceLine({
      price: data.vwap,
      color: "#00f2fe",
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: "VWAP Thể Chế",
    });
    currentPriceLines.push(vwapLine);
  }

  // 2. Dynamic ATR Stop Loss Line (Red Dotted)
  if (data.trade_plan && data.trade_plan.sl) {
    const slLine = candleSeries.createPriceLine({
      price: data.trade_plan.sl,
      color: "#ff3366",
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      axisLabelVisible: true,
      title: "SL (1.5x ATR)",
    });
    currentPriceLines.push(slLine);
  }

  // 3. TP1 Line (Green Dotted)
  if (data.trade_plan && data.trade_plan.tp1) {
    const tp1Line = candleSeries.createPriceLine({
      price: data.trade_plan.tp1,
      color: "#00e676",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      axisLabelVisible: true,
      title: "TP1 (+2.5%)",
    });
    currentPriceLines.push(tp1Line);
  }

  // 4. TP2 Line (Yellow Dotted)
  if (data.trade_plan && data.trade_plan.tp2) {
    const tp2Line = candleSeries.createPriceLine({
      price: data.trade_plan.tp2,
      color: "#ffb300",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      axisLabelVisible: true,
      title: "TP2 (+5.0%)",
    });
    currentPriceLines.push(tp2Line);
  }

  // 5. TP3 Line (Cyan Dotted)
  if (data.trade_plan && data.trade_plan.tp3) {
    const tp3Line = candleSeries.createPriceLine({
      price: data.trade_plan.tp3,
      color: "#00f2fe",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dotted,
      axisLabelVisible: true,
      title: "TP3 (+10.0%)",
    });
    currentPriceLines.push(tp3Line);
  }
}

function updateDiagnosticMatrix(data) {
  // 1. Taker Buy
  const tbEl = document.getElementById("factor-taker-buy-val");
  const tbDesc = document.getElementById("factor-taker-buy-desc");
  const tbVal = data.taker_buy_ratio || 50;
  if (tbEl) {
    tbEl.innerText = `${tbVal.toFixed(1)}%`;
    tbEl.style.color = tbVal >= 65 ? "var(--accent-green)" : tbVal >= 50 ? "var(--accent-yellow)" : "var(--accent-red)";
  }
  if (tbDesc) {
    tbDesc.innerText = tbVal >= 65 ? "Phe mua chủ động gom áp đảo" : tbVal >= 50 ? "Cân bằng lực cung - cầu" : "Phe bán đang chủ động xả";
  }

  // 2. Vol Spike
  const vsEl = document.getElementById("factor-vol-spike-val");
  const vsDesc = document.getElementById("factor-vol-spike-desc");
  const vsVal = data.vol_spike || 1.0;
  if (vsEl) {
    vsEl.innerText = `${vsVal.toFixed(1)}x`;
    vsEl.style.color = vsVal >= 2.0 ? "var(--accent-yellow)" : "#cbd5e1";
  }
  if (vsDesc) {
    vsDesc.innerText = vsVal >= 2.5 ? "Bùng nổ khối lượng cực mạnh" : vsVal >= 1.5 ? "Khối lượng gia tăng đột biến" : "Khối lượng ổn định quanh 20-EWMA";
  }

  // 3. VWAP Dist
  const vdEl = document.getElementById("factor-vwap-dist-val");
  const vdDesc = document.getElementById("factor-vwap-dist-desc");
  const vdVal = data.vwap_distance_pct || 0;
  if (vdEl) {
    vdEl.innerText = `${vdVal >= 0 ? "+" : ""}${vdVal.toFixed(2)}%`;
    vdEl.style.color = vdVal >= 0 ? "var(--accent-green)" : "var(--accent-red)";
  }
  if (vdDesc) {
    vdDesc.innerText = vdVal >= 0 ? "Nằm trên bệ đỡ giá thể chế VWAP" : "Nằm dưới VWAP (Phe bán ép giá)";
  }

  // 4. RSI
  const rsiEl = document.getElementById("factor-rsi-val");
  const rsiVal = data.rsi || 50;
  if (rsiEl) {
    rsiEl.innerText = rsiVal.toFixed(1);
    rsiEl.style.color = (rsiVal >= 55 && rsiVal <= 72) ? "var(--accent-green)" : rsiVal > 75 ? "var(--accent-red)" : "#cbd5e1";
  }

  // 5. Gap Velocity
  const gapEl = document.getElementById("factor-gap-val");
  const gapVal = data.price_change_5m || 0;
  if (gapEl) {
    gapEl.innerText = `${gapVal >= 0 ? "+" : ""}${gapVal.toFixed(2)}%`;
    gapEl.style.color = gapVal >= 0 ? "var(--accent-purple)" : "var(--accent-red)";
  }
}

function updateTradePlan(data) {
  const plan = data.trade_plan || {};
  const price = data.price || 0;

  const entryEl = document.getElementById("plan-entry-price");
  const slEl = document.getElementById("plan-sl-price");
  const tp1El = document.getElementById("plan-tp1-price");
  const tp2El = document.getElementById("plan-tp2-price");
  const tp3El = document.getElementById("plan-tp3-price");

  if (entryEl) entryEl.innerText = `$${formatStockPrice(price)}`;
  if (slEl) slEl.innerText = `$${formatStockPrice(plan.sl)}`;
  if (tp1El) tp1El.innerText = `$${formatStockPrice(plan.tp1)}`;
  if (tp2El) tp2El.innerText = `$${formatStockPrice(plan.tp2)}`;
  if (tp3El) tp3El.innerText = `$${formatStockPrice(plan.tp3)}`;
}

function updateAICommentary(data) {
  const reasonsEl = document.getElementById("plan-ml-reasons");
  if (!reasonsEl) return;

  const sig = data.signal || "NEUTRAL";
  const tbVal = data.taker_buy_ratio || 50;
  const vsVal = data.vol_spike || 1.0;
  const vdVal = data.vwap_distance_pct || 0;
  const rsiVal = data.rsi || 50;

  const bullets = [];

  if (data.reasons && data.reasons.length > 0) {
    data.reasons.forEach(r => bullets.push(r));
  } else {
    if (sig === "STRONG_BUY_BREAKOUT") {
      bullets.push(`<strong style="color: var(--accent-cyan);">Phát Hiện Mua Breakout:</strong> Đã kích hoạt đầy đủ điều kiện bùng nổ, khối lượng tăng vọt ${vsVal.toFixed(1)}x kết hợp lực mua Taker Buy ${tbVal.toFixed(1)}%.`);
    } else if (sig === "INSTITUTIONAL_ACCUMULATION") {
      bullets.push(`<strong style="color: var(--accent-green);">Pha Gom Hàng Thể Chế:</strong> Phe mua gom chủ động ${tbVal.toFixed(1)}% quanh mốc VWAP $${formatStockPrice(data.vwap)}, biên độ nén chặt chuẩn bị bứt phá.`);
    } else if (sig === "MOMENTUM_SURGE") {
      bullets.push(`<strong style="color: var(--accent-cyan);">Tăng Tốc Động Lượng:</strong> Xu hướng tăng được củng cố với RSI ở mức ngọt ${rsiVal.toFixed(1)}.`);
    } else if (sig === "OVERBOUGHT_EXHAUSTION") {
      bullets.push(`<strong style="color: var(--accent-red);">Cảnh Báo Quá Mua:</strong> RSI (${rsiVal.toFixed(1)}) tiến sát vùng cạn kiệt, cẩn trọng bẫy Bull Trap.`);
    } else {
      bullets.push(`Thị trường đang tích lũy ổn định quanh đường giá thể chế VWAP ($${formatStockPrice(data.vwap)}).`);
    }
  }

  bullets.push(`Đệm giá so với VWAP đạt <strong>${vdVal >= 0 ? "+" : ""}${vdVal.toFixed(2)}%</strong> (${vdVal >= 0 ? "Vị thế an toàn cho phe Long" : "Dưới áp lực bán"}).`);
  bullets.push(`Khuyến nghị quản trị rủi ro: Cắt lỗ động tại mốc <strong>$${formatStockPrice(data.trade_plan?.sl)}</strong> (1.5x ATR) để tối ưu tỷ lệ R:R &ge; 1:2.0.`);

  reasonsEl.innerHTML = bullets.map(b => `<li style="margin-bottom: 6px;">${b}</li>`).join("");
}

function updateMicrostructure(data) {
  const vwapEl = document.getElementById("micro-vwap-val");
  const distEl = document.getElementById("micro-vwap-dist");
  const hvEl = document.getElementById("micro-hv-val");
  const rsiEl = document.getElementById("micro-rsi-val");
  const atrEl = document.getElementById("micro-atr-val");

  if (vwapEl) vwapEl.innerText = `$${formatStockPrice(data.vwap)}`;
  if (distEl) {
    const vd = data.vwap_distance_pct || 0;
    distEl.innerText = `${vd >= 0 ? "+" : ""}${vd.toFixed(2)}%`;
    distEl.style.color = vd >= 0 ? "var(--accent-green)" : "var(--accent-red)";
  }
  if (hvEl) hvEl.innerText = `${(data.realized_vol_pct || 0).toFixed(1)}%`;
  if (rsiEl) rsiEl.innerText = (data.rsi || 50).toFixed(1);
  if (atrEl) atrEl.innerText = `$${formatStockPrice(data.atr)}`;
}

async function fetchSectorPeers() {
  try {
    const res = await fetch("/api/tradfi/stocks?pageSize=100");
    if (!res.ok) return;
    const data = await res.json();
    const all = data.data || [];

    // Find current stock's global rank
    all.forEach((s, idx) => {
      s.globalRank = idx + 1;
    });

    const currentItem = all.find(s => s.symbol === CURRENT_SYMBOL || s.ticker === CURRENT_TICKER);
    if (currentItem) {
      const rankEl = document.getElementById("header-global-rank");
      if (rankEl) {
        rankEl.innerText = `Hạng Toàn Cục #${currentItem.globalRank}/${all.length}`;
      }

      // Filter peers with same sector
      const peers = all.filter(s => s.sector === currentItem.sector && s.symbol !== CURRENT_SYMBOL).slice(0, 8);
      const container = document.getElementById("sector-peers-container");
      if (container && peers.length > 0) {
        container.innerHTML = peers.map(p => `
          <a href="/stock/${p.symbol}" class="filter-btn" style="text-decoration: none; padding: 5px 10px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-mono);">
            <strong style="color: #fff;">${p.ticker || p.symbol}</strong>
            <span style="color: ${(p.pct_24h || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}; font-size: 0.7rem;">
              ${(p.pct_24h || 0) >= 0 ? '+' : ''}${(p.pct_24h || 0).toFixed(1)}%
            </span>
          </a>
        `).join("");
      }
    }
  } catch (e) {
    console.debug("Error loading sector peers:", e);
  }
}

function updateSessionPill(session) {
  if (!session) return;
  const pillText = document.getElementById("session-status-text");
  if (pillText) {
    pillText.innerText = `NY Time: ${session.est_time} • ${session.session_name}`;
  }
}

function toggleAudioAlert() {
  audioAlertEnabled = !audioAlertEnabled;
  const textEl = document.getElementById("audio-status-text");
  if (textEl) {
    textEl.innerText = audioAlertEnabled ? "Chuông: BẬT" : "Chuông: TẮT";
  }
}

function playNotificationSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 note
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (e) {
    // AudioContext blocked
  }
}

function formatStockPrice(price) {
  if (!price) return "0.00";
  if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return price.toFixed(2);
  return price.toFixed(4);
}
