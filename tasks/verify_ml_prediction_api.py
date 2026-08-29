"""
Verify ML Multiplier Prediction API and Active Campaigns.
"""

import urllib.request
import json
import time

def verify_all():
    time.sleep(2)

    # 1. Test Research API
    r1 = urllib.request.urlopen("http://127.0.0.1:5050/api/ml/pump_multiplier_research")
    data1 = json.loads(r1.read().decode())
    print("=== 1. ML RESEARCH API ===")
    print("Status:", data1.get("status"))
    print("Events Count:", data1.get("events_count"))
    print("Model Summary:", data1.get("model_summary"))

    # 2. Test In-Flight ML Prediction API
    url2 = "http://127.0.0.1:5050/api/ml/predict_pump_multiplier?symbol=BTRUSDT&base_price=0.01587&current_price=0.15663&vol_spike_ratio=18.5&funding_rate=-0.012"
    r2 = urllib.request.urlopen(url2)
    data2 = json.loads(r2.read().decode())
    print("\n=== 2. IN-FLIGHT ML PREDICTION API (BTRUSDT) ===")
    pred = data2.get("prediction", {})
    print(f"Symbol: {pred.get('symbol')}")
    print(f"Base Price: ${pred.get('base_price')} | Curr Price: ${pred.get('current_price')} ({pred.get('current_n')}x)")
    print(f"ML Predicted n: {pred.get('n_expected')}x [{pred.get('n_low')}x - {pred.get('n_high')}x]")
    print(f"Target Peak Price: ${pred.get('target_peak_price')} | Range: ${pred.get('target_price_low')} - ${pred.get('target_price_high')}")
    print(f"Progress: {pred.get('progress_pct')}% | Remaining Upside: +{pred.get('remaining_upside_pct')}%")
    rec = str(pred.get('stage_recommendation', '')).encode('ascii', 'replace').decode()
    print(f"Recommendation: {rec}")

    # 3. Test Active Campaigns API with ML enrichment
    r3 = urllib.request.urlopen("http://127.0.0.1:5050/api/ml/active_pump_campaigns")
    data3 = json.loads(r3.read().decode())
    print("\n=== 3. ACTIVE CAMPAIGNS WITH ENRICHED ML PREDICTIONS ===")
    print("Active Count:", data3.get("active_count"))
    for ac in data3.get("active_campaigns", []):
        mlp = ac.get("ml_prediction", {})
        print(
            f"  {ac['symbol']:<10}: Curr {ac['current_n']}x "
            f"-> ML Target: {mlp.get('n_expected', 'N/A')}x (${mlp.get('target_peak_price', 'N/A')}) "
            f"| Progress: {mlp.get('progress_pct', 'N/A')}% | Upside: +{mlp.get('remaining_upside_pct', 'N/A')}%"
        )

if __name__ == "__main__":
    verify_all()
