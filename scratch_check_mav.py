import requests
import time

time.sleep(3)
s = requests.Session()
s.trust_env = False
res = s.get("http://127.0.0.1:5050/api/pre_pump_radar")
print("Status code:", res.status_code)
data = res.json()
print("Timestamp:", data.get("timestamp"))
print("Total analyzed:", data.get("total_analyzed"))
for i, c in enumerate(data.get("candidates", [])[:10]):
    print(f"{i+1}. {c['symbol']} | Score: {c['pre_pump_score']} | Phase: {c['phase']} | FR: {c.get('funding_pct', 0):.4f}% | VolSpike: {c.get('vol_spike_1h', 0):.1f}x | 1H Candle: {c.get('candle_1h_pct', 0):+.2f}% | Bullish: {c.get('is_bullish_ignition')}")
