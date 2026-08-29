import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))
sys.path.insert(0, str(ROOT_DIR))

from core_engine.pump_multiplier_regressor import get_pump_multiplier_regressor

def run_test():
    reg = get_pump_multiplier_regressor()
    print("Model Summary:", reg.get_model_summary())

    test_cases = [
        {"symbol": "BTRUSDT", "base_price": 0.01587, "current_price": 0.15663, "vol_spike": 18.5, "funding": -0.012},
        {"symbol": "AKEUSDT", "base_price": 0.0001729, "current_price": 0.0107, "vol_spike": 35.0, "funding": -0.018},
        {"symbol": "BULLAUSDT", "base_price": 0.003824, "current_price": 0.01664, "vol_spike": 12.0, "funding": -0.008},
        {"symbol": "PUMPUSDT", "base_price": 0.001149, "current_price": 0.00456, "vol_spike": 15.0, "funding": -0.015},
        {"symbol": "HEMIUSDT", "base_price": 0.004101, "current_price": 0.01152, "vol_spike": 8.5, "funding": -0.005},
        {"symbol": "SNXXUSDT", "base_price": 6.20, "current_price": 12.77, "vol_spike": 6.0, "funding": -0.003},
    ]

    print("\n" + "=" * 110)
    print("=== ML PUMP MULTIPLIER (n) PREDICTIONS FOR ACTIVE CAMPAIGNS ===")
    print("=" * 110)
    for tc in test_cases:
        pred = reg.predict(
            symbol=tc["symbol"],
            current_price=tc["base_price"],
            vol_spike_ratio=tc["vol_spike"],
            pct_24h=50.0,
        )
        curr_n = tc["current_price"] / tc["base_price"]
        n_expected = pred.n_expected
        target_price = tc["base_price"] * n_expected
        upside_pct = max(0.0, (target_price - tc["current_price"]) / tc["current_price"] * 100.0)
        completion_pct = min(100.0, curr_n / n_expected * 100.0)

        print(
            f"  {tc['symbol']:<10}: Base ${tc['base_price']:<10} | Curr ${tc['current_price']:<10} ({curr_n:5.2f}x) "
            f"-> ML Predicted n: {n_expected:5.2f}x [{pred.n_low:4.1f}x - {pred.n_high:5.1f}x] "
            f"| Target Price: ${target_price:<10.6f} | Progress: {completion_pct:5.1f}% | Upside Left: +{upside_pct:5.1f}%"
        )

if __name__ == "__main__":
    run_test()
