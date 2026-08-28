"""
High-Speed Parallel Multi-Threaded Binance USD-M Super-Pump Scanner (2026 Cycle).
Discovers all active super pumps (holding near peak) and completed dumps across all 735+ pairs in seconds.
"""

import urllib.request
import json
import time
import datetime
import concurrent.futures
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def analyze_symbol_cycle(sym):
    try:
        k_url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&limit=120"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        k_req = urllib.request.Request(k_url, headers=headers)
        with urllib.request.urlopen(k_req, timeout=5) as k_resp:
            klines = json.loads(k_resp.read().decode())
        
        if len(klines) < 15:
            return None
        
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        times = [k[0] for k in klines]
        
        min_low = min(lows)
        min_idx = lows.index(min_low)
        
        # Peak must occur at or after cycle bottom
        peak_high = max(highs[min_idx:])
        peak_idx = min_idx + highs[min_idx:].index(peak_high)
        curr_price = closes[-1]
        
        if min_low <= 0 or peak_high <= 0:
            return None
            
        n_peak = peak_high / min_low
        n_curr = curr_price / min_low
        dd = (peak_high - curr_price) / peak_high * 100.0
        
        min_date = datetime.datetime.fromtimestamp(times[min_idx]/1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        peak_date = datetime.datetime.fromtimestamp(times[peak_idx]/1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        
        if n_peak >= 3.0:  # Major pump wave threshold
            item = {
                "symbol": sym,
                "origin_date": min_date,
                "peak_date": peak_date,
                "base_price": min_low,
                "peak_price": peak_high,
                "curr_price": curr_price,
                "peak_n": round(n_peak, 2),
                "curr_n": round(n_curr, 2),
                "dd_pct": round(dd, 1),
            }
            if dd < 38.0:
                item["stage"] = "ACTIVE"
            elif dd >= 45.0:
                item["stage"] = "DUMPED"
            else:
                item["stage"] = "EXHAUSTION"
            return item
    except Exception:
        return None
    return None


def run_parallel_scan():
    print("Fetching symbols from ticker/price...")
    url = "https://fapi.binance.com/fapi/v1/ticker/price"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())

    symbols = [
        p["symbol"] for p in data
        if p.get("symbol", "").endswith("USDT")
        and not p["symbol"].startswith(("USDC", "FDUSD", "TUSD", "BUSD", "EUR", "DAI"))
    ]
    print(f"Starting parallel scan across {len(symbols)} USDT-M Futures pairs with 12 workers...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for item in executor.map(analyze_symbol_cycle, symbols):
            if item:
                results.append(item)

    active_super_pumps = [r for r in results if r["stage"] == "ACTIVE"]
    completed_dumps = [r for r in results if r["stage"] == "DUMPED"]
    exhaustion_pumps = [r for r in results if r["stage"] == "EXHAUSTION"]

    print("\n" + "=" * 90)
    print(f">>> FOUND {len(active_super_pumps)} ACTIVE SUPER PUMPS (Peak n >= 3.0x, Drawdown < 38%):")
    print("=" * 90)
    for p in sorted(active_super_pumps, key=lambda x: x["peak_n"], reverse=True):
        print(f"  {p['symbol']:<12}: Base ${p['base_price']:<10.6f} ({p['origin_date']}) -> Peak ${p['peak_price']:<10.6f} ({p['peak_date']}, {p['peak_n']}x) | Curr: ${p['curr_price']:<10.6f} ({p['curr_n']}x, DD: -{p['dd_pct']}%)")

    print("\n" + "=" * 90)
    print(f">>> FOUND {len(exhaustion_pumps)} EXHAUSTION / AT RISK PUMPS (Peak n >= 3.0x, Drawdown 38% - 45%):")
    print("=" * 90)
    for p in sorted(exhaustion_pumps, key=lambda x: x["peak_n"], reverse=True):
        print(f"  {p['symbol']:<12}: Base ${p['base_price']:<10.6f} ({p['origin_date']}) -> Peak ${p['peak_price']:<10.6f} ({p['peak_n']}x) | Curr: ${p['curr_price']:<10.6f} (DD: -{p['dd_pct']}%)")

    print("\n" + "=" * 90)
    print(f">>> FOUND {len(completed_dumps)} COMPLETED DUMPS (Peak n >= 3.0x, Drawdown >= 45%):")
    print("=" * 90)
    for p in sorted(completed_dumps, key=lambda x: x["peak_n"], reverse=True)[:30]:
        print(f"  {p['symbol']:<12}: Base ${p['base_price']:<10.6f} ({p['origin_date']}) -> Peak ${p['peak_price']:<10.6f} ({p['peak_n']}x) | Curr: ${p['curr_price']:<10.6f} (DD: -{p['dd_pct']}%)")

    # Output JSON for automated ingestion
    output_path = ROOT_DIR / "data" / "all_scanned_super_pumps_2026.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scanned_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "active_super_pumps": active_super_pumps,
            "exhaustion_pumps": exhaustion_pumps,
            "completed_dumps": completed_dumps,
        }, f, indent=2)
    print(f"\nSaved full results to {output_path}")

if __name__ == "__main__":
    run_parallel_scan()
