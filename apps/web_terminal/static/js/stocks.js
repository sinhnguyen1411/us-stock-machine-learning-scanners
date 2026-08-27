/**
 * DeepAlpha US Stock Machine Learning Scanners — Frontend Client Logic
 * Handles 90+ TradFi perpetual futures, VWAP, ML scoring & TradingView Lightweight Charts
 */

let allTradFiStocks = [];
let currentSectorFilter = "ALL";
let currentSearchQuery = "";
let selectedTradFiSymbol = "NVDAUSDT";
let currentTradFiTimeframe = "5m";
let tradFiChart = null;
let tradFiCandleSeries = null;
let tradFiVolumeSeries = null;
let tradFiPriceLines = [];
let isAudioEnabled = true;
let audioContext = null;

document.addEventListener("DOMContentLoaded", () => {
  initTradFiChart();
  fetchTradFiData();
  loadTradFiDetail(selectedTradFiSymbol);

  // Auto-refresh every 3.5 seconds
  setInterval(fetchTradFiData, 3500);
});

function initTradFiChart() {
  const container = document.getElementById("tradfi-chart-container");
  if (!container) return;

  container.innerHTML = "";

  if (typeof LightweightCharts === "undefined") {
    console.error("LightweightCharts library is not loaded.");
    return;
  }

  tradFiChart = LightweightCharts.createChart(container, {
    width: container.clientWidth || 380,
    height: 280,
    layout: {
      backgroundColor: "#0c1017",
      textColor: "#8898aa",
      fontSize: 11,
      fontFamily: "'JetBrains Mono', monospace",
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

  tradFiCandleSeries = tradFiChart.addCandlestickSeries({
    upColor: "#00e676",
    downColor: "#ff3366",
    borderDownColor: "#ff3366",
    borderUpColor: "#00e676",
    wickDownColor: "#ff3366",
    wickUpColor: "#00e676",
  });

  tradFiVolumeSeries = tradFiChart.addHistogramSeries({
    color: "#00f2fe",
    priceFormat: { type: "volume" },
    priceScaleId: "",
    scaleMargins: {
      top: 0.8,
      bottom: 0,
    },
  });

  window.addEventListener("resize", () => {
    if (tradFiChart && container) {
      tradFiChart.applyOptions({ width: container.clientWidth });
    }
  });
}

async function fetchTradFiData() {
  try {
    const res = await fetch("/api/tradfi/stocks?pageSize=100");
    if (!res.ok) return;
    const data = await res.json();
    allTradFiStocks = data.data || [];

    // Assign true global rank before any filtering
    allTradFiStocks.forEach((s, idx) => {
      s.globalRank = idx + 1;
    });

    updateSessionHeader(data.session);
    updateTopStatCards();
    renderTradFiTable();
  } catch (e) {
    console.debug("Error fetching TradFi data:", e);
  }
}

function updateSessionHeader(session) {
  if (!session) return;
  const timeEl = document.getElementById("ny-session-time");
  const stateEl = document.getElementById("ny-session-state");
  const pillText = document.getElementById("session-status-text");

  if (timeEl) timeEl.innerText = `NY Time: ${session.est_time}`;
  if (stateEl) stateEl.innerText = session.session_name;
  if (pillText) pillText.innerText = session.session_name;
}

function updateTopStatCards() {
  if (!allTradFiStocks || allTradFiStocks.length === 0) return;

  // 1. Top 1 ML Score
  const top1 = allTradFiStocks[0];
  const topSymEl = document.getElementById("stat-top-stock-symbol");
  const topScoreEl = document.getElementById("stat-top-stock-score");
  if (topSymEl && top1) {
    topSymEl.innerText = top1.ticker || top1.symbol;
  }
  if (topScoreEl && top1) {
    topScoreEl.innerText = `Điểm ML: ${top1.ml_score.toFixed(0)}/100 (${top1.signal_tag || "Gom hàng"})`;
  }

  // 2. Buy Breakouts count
  const breakouts = allTradFiStocks.filter(s => s.signal === "STRONG_BUY_BREAKOUT" || s.ml_score >= 70.0).length;
  const brkEl = document.getElementById("stat-breakout-stock-count");
  if (brkEl) brkEl.innerText = breakouts;

  // 3. Accumulation count
  const accums = allTradFiStocks.filter(s => s.signal === "INSTITUTIONAL_ACCUMULATION" || (s.taker_buy_ratio >= 60.0 && s.vwap_distance_pct >= -0.5)).length;
  const accEl = document.getElementById("stat-accum-stock-count");
  if (accEl) accEl.innerText = accums;

  // 4. Total Count
  const totEl = document.getElementById("stat-total-stock-count");
  if (totEl) totEl.innerText = `${allTradFiStocks.length} mã`;

  const timeEl = document.getElementById("tradfi-updated-time");
  if (timeEl) {
    timeEl.innerText = `Cập nhật: ${new Date().toLocaleTimeString()}`;
  }
}

function filterBySector(sector) {
  currentSectorFilter = sector;
  document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }
  renderTradFiTable();
}

function handleStockSearch(val) {
  currentSearchQuery = (val || "").trim().toUpperCase();
  renderTradFiTable();
}

function renderTradFiTable() {
  const tbody = document.getElementById("tradfi-stock-body");
  const titleEl = document.getElementById("tradfi-table-title");
  const subtitleEl = document.getElementById("tradfi-table-subtitle");
  if (!tbody) return;

  let list = allTradFiStocks;
  if (currentSectorFilter !== "ALL") {
    list = list.filter(s => s.sector === currentSectorFilter);
  }

  if (currentSearchQuery) {
    list = list.filter(s => 
      s.symbol.includes(currentSearchQuery) || 
      (s.ticker && s.ticker.includes(currentSearchQuery)) || 
      (s.name && s.name.toUpperCase().includes(currentSearchQuery))
    );
  }

  // Dynamic panel title & subtitle to avoid misleading "Bảng Xếp Hạng" on single lookup
  if (titleEl && subtitleEl) {
    if (currentSearchQuery) {
      if (list.length === 1) {
        const item = list[0];
        titleEl.innerText = `Kết Quả Tra Cứu Vi Mô: ${item.ticker || item.symbol} (Hạng #${item.globalRank}/${allTradFiStocks.length})`;
        subtitleEl.innerText = `Tra cứu vi mô thời gian thực • Giữ nguyên thứ hạng thực tế toàn hệ thống`;
      } else {
        titleEl.innerText = `Kết Quả Tìm Kiếm: "${currentSearchQuery}" (${list.length} mã)`;
        subtitleEl.innerText = `Danh sách tìm kiếm theo ký tự • Giữ nguyên thứ hạng thực tế`;
      }
    } else if (currentSectorFilter !== "ALL") {
      const sectorNames = {
        "MEGA_TECH": "Mega Tech",
        "SEMICONDUCTORS": "Bán Dẫn (Semi)",
        "INDEX_AND_ETFS": "Index & ETF",
        "AI_AND_PRE_IPO": "AI & Pre-IPO",
        "FINANCIALS": "Tài Chính",
        "GLOBAL_EQUITIES": "Quốc Tế",
        "CONSUMER_AND_HEALTHCARE": "Tiêu Dùng"
      };
      const secName = sectorNames[currentSectorFilter] || currentSectorFilter;
      titleEl.innerText = `Danh Sách Phân Ngành: ${secName} (${list.length} mã)`;
      subtitleEl.innerText = `Lọc theo lĩnh vực • Giữ nguyên thứ hạng thực tế trong toàn hệ thống`;
    } else {
      titleEl.innerText = `Bảng Xếp Hạng Machine Learning Phái Sinh Chứng Khoán Mỹ`;
      subtitleEl.innerText = `Xếp hạng theo điểm tổng hợp ML Score (0 - 100) • Tự động tính toán VWAP, Taker Buy, Gap %`;
    }
  }

  if (!list || list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" style="text-align: center; color: var(--text-dim); padding: 35px;">
          Chưa tìm thấy mã chứng khoán nào phù hợp với từ khóa "${currentSearchQuery || currentSectorFilter}". Đang quét vi mô 5M...
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = list.map((s) => {
    const rank = s.globalRank;
    const rankBadge = rank === 1 ? "🥇 #1" : rank === 2 ? "🥈 #2" : rank === 3 ? "🥉 #3" : `#${rank}`;
    const rankStyle = rank <= 3 ? "color: var(--accent-cyan); font-weight: 800;" : "color: var(--text-muted);";

    const chgClass = (s.pct_24h || 0) >= 0 ? "trend-up" : "trend-down";
    const chgSign = (s.pct_24h || 0) >= 0 ? "+" : "";

    const vwapDist = s.vwap_distance_pct || 0;
    const vwapDistColor = vwapDist >= 0 ? "var(--accent-green)" : "var(--accent-red)";
    const vwapDistSign = vwapDist >= 0 ? "+" : "";

    // Gradient bar color for ML Score
    const score = s.ml_score || 50;
    const scoreColor = score >= 75 ? "linear-gradient(90deg, #00f2fe, #4facfe)" :
                       score >= 60 ? "linear-gradient(90deg, #00e676, #00b0ff)" :
                       score >= 40 ? "linear-gradient(90deg, #ffb300, #ff9100)" :
                                     "linear-gradient(90deg, #ff3366, #ff1744)";

    const isSelected = s.symbol === selectedTradFiSymbol;
    const rowClass = isSelected ? "style='background: rgba(0, 242, 254, 0.08);'" : "";

    return `
      <tr ${rowClass} onclick="selectTradFiStock('${s.symbol}')" style="cursor: pointer;">
        <td style="${rankStyle} text-align: center; font-family: var(--font-mono);">${rankBadge}</td>
        <td>
          <div style="font-weight: 800; color: #fff; font-size: 0.92rem; line-height: 1.2;">${s.ticker || s.symbol}</div>
          <div style="font-size: 0.68rem; color: var(--text-dim); line-height: 1.2; max-width: 140px; overflow: hidden; text-overflow: ellipsis;">${s.name || "US Stock"}</div>
        </td>
        <td>
          <span class="sector-badge">
            ${s.sector_name || s.sector}
          </span>
        </td>
        <td style="text-align: right; font-family: var(--font-mono); font-weight: 700; color: #fff;">
          $${formatStockPrice(s.price)}
        </td>
        <td style="text-align: right; font-family: var(--font-mono); font-weight: 700;" class="${chgClass}">
          ${chgSign}${(s.pct_24h || 0).toFixed(2)}%
        </td>
        <td style="text-align: right; font-family: var(--font-mono);">
          <div style="color: #cbd5e1; font-size: 0.78rem;">$${formatStockPrice(s.vwap)}</div>
          <div style="font-size: 0.68rem; color: ${vwapDistColor}; font-weight: 700;">${vwapDistSign}${vwapDist.toFixed(2)}%</div>
        </td>
        <td style="text-align: center; font-family: var(--font-mono); font-size: 0.82rem; color: ${s.vol_spike >= 2.0 ? 'var(--accent-yellow)' : 'var(--text-muted)'}; font-weight: 700;">
          ${(s.vol_spike || 1.0).toFixed(1)}x
        </td>
        <td style="text-align: center; font-family: var(--font-mono); font-size: 0.82rem; color: ${s.taker_buy_ratio >= 60 ? 'var(--accent-green)' : 'var(--text-muted)'}; font-weight: 700;">
          ${(s.taker_buy_ratio || 50).toFixed(1)}%
        </td>
        <td style="width: 130px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <div style="flex: 1; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
              <div style="width: ${score}%; height: 100%; background: ${scoreColor}; border-radius: 3px;"></div>
            </div>
            <span style="font-family: var(--font-mono); font-weight: 700; font-size: 0.8rem; width: 24px; text-align: right; color: #fff;">
              ${score.toFixed(0)}
            </span>
          </div>
        </td>
        <td style="text-align: center;">
          <span class="signal-tag ${s.signal_class || 'tradfi-signal-neutral'}">
            ${s.signal_tag || "TÍCH LŨY"}
          </span>
        </td>
        <td style="text-align: center;">
          <button class="action-btn-mini" onclick="event.stopPropagation(); window.location.href='/stock/${s.symbol}'" title="Chuyển đến trang soi nến và phân tích chi tiết">
            Soi Nến
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function formatStockPrice(price) {
  if (!price) return "0.00";
  if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return price.toFixed(2);
  return price.toFixed(4);
}

function openDedicatedStockPage() {
  if (selectedTradFiSymbol) {
    window.location.href = `/stock/${selectedTradFiSymbol}`;
  }
}

function selectTradFiStock(symbol) {
  selectedTradFiSymbol = symbol;
  renderTradFiTable();
  loadTradFiDetail(symbol);
}

async function loadTradFiDetail(symbol) {
  try {
    const res = await fetch(`/api/tradfi/analyze/${symbol}?interval=${currentTradFiTimeframe}`);
    if (!res.ok) return;
    const data = await res.json();

    // 1. Update Chart Header
    const tickerEl = document.getElementById("chart-stock-ticker");
    const nameEl = document.getElementById("chart-stock-name");
    if (tickerEl) tickerEl.innerText = data.ticker ? `${data.ticker} / USD-M` : symbol;
    if (nameEl) nameEl.innerText = data.name || "US Equity Derivative";

    // 2. Update Quick Metrics
    const vwapEl = document.getElementById("detail-vwap-val");
    const vwapDistEl = document.getElementById("detail-vwap-dist");
    const hvEl = document.getElementById("detail-hv-val");
    const rsiEl = document.getElementById("detail-rsi-val");

    if (vwapEl) vwapEl.innerText = `$${formatStockPrice(data.vwap)}`;
    if (vwapDistEl) {
      const dist = data.vwap_distance_pct || 0;
      vwapDistEl.innerText = `Cách VWAP: ${dist >= 0 ? '+' : ''}${dist.toFixed(2)}%`;
      vwapDistEl.style.color = dist >= 0 ? "var(--accent-green)" : "var(--accent-red)";
    }
    if (hvEl) hvEl.innerText = `${(data.realized_vol_pct || 0).toFixed(1)}% (HV)`;
    if (rsiEl) rsiEl.innerText = `RSI (14): ${(data.rsi || 50).toFixed(1)}`;

    // 3. Update Trade Setup
    const tp = data.trade_plan || {};
    const entryEl = document.getElementById("detail-entry-price");
    const slEl = document.getElementById("detail-sl-price");
    const tp1El = document.getElementById("detail-tp1-price");
    const tp2El = document.getElementById("detail-tp2-price");
    const tp3El = document.getElementById("detail-tp3-price");

    if (entryEl) entryEl.innerText = `$${formatStockPrice(tp.entry || data.price)}`;
    if (slEl) slEl.innerText = `$${formatStockPrice(tp.sl)}`;
    if (tp1El) tp1El.innerText = `$${formatStockPrice(tp.tp1)}`;
    if (tp2El) tp2El.innerText = `$${formatStockPrice(tp.tp2)}`;
    if (tp3El) tp3El.innerText = `$${formatStockPrice(tp.tp3)}`;

    // 4. Update ML Reasons
    const reasonsEl = document.getElementById("detail-ml-reasons");
    if (reasonsEl && data.reasons) {
      reasonsEl.innerHTML = data.reasons.map(r => `<li>${r}</li>`).join("");
    }

    // 5. Update Candles on Chart
    if (data.candles && tradFiCandleSeries) {
      const formattedCandles = data.candles.map(c => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));
      tradFiCandleSeries.setData(formattedCandles);

      if (tradFiVolumeSeries) {
        const formattedVols = data.candles.map(c => ({
          time: c.time,
          value: c.volume,
          color: c.close >= c.open ? "rgba(0, 230, 118, 0.4)" : "rgba(255, 51, 102, 0.4)",
        }));
        tradFiVolumeSeries.setData(formattedVols);
      }

      // Dynamic Price Lines (VWAP, SL, TP1)
      clearTradFiPriceLines();
      if (data.vwap) {
        tradFiPriceLines.push(tradFiCandleSeries.createPriceLine({
          price: data.vwap,
          color: "#00f2fe",
          lineWidth: 2,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          axisLabelVisible: true,
          title: "VWAP",
        }));
      }
      if (tp.sl) {
        tradFiPriceLines.push(tradFiCandleSeries.createPriceLine({
          price: tp.sl,
          color: "#ff3366",
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dotted,
          axisLabelVisible: true,
          title: "SL (1.5x ATR)",
        }));
      }
      if (tp.tp1) {
        tradFiPriceLines.push(tradFiCandleSeries.createPriceLine({
          price: tp.tp1,
          color: "#00e676",
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dotted,
          axisLabelVisible: true,
          title: "TP1 (+2.5%)",
        }));
      }

      tradFiChart.timeScale().fitContent();
    }

  } catch (e) {
    console.error("Error loading TradFi detail:", e);
  }
}

function clearTradFiPriceLines() {
  if (!tradFiCandleSeries || !tradFiPriceLines) return;
  tradFiPriceLines.forEach(pl => {
    try { tradFiCandleSeries.removePriceLine(pl); } catch (e) {}
  });
  tradFiPriceLines = [];
}

function changeTradFiTimeframe(tf) {
  currentTradFiTimeframe = tf;
  document.querySelectorAll(".timeframe-btn").forEach(btn => {
    btn.classList.toggle("active", btn.innerText.toLowerCase() === tf.toLowerCase());
  });
  loadTradFiDetail(selectedTradFiSymbol);
}

function toggleAudioAlert() {
  isAudioEnabled = !isAudioEnabled;
  const icon = document.getElementById("audio-icon");
  const txt = document.getElementById("audio-status-text");
  if (isAudioEnabled) {
    if (txt) txt.innerText = "Chuông: BẬT";
  } else {
    if (txt) txt.innerText = "Chuông: TẮT";
  }
  if (icon) icon.innerText = "";
}
