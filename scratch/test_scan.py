import sys
sys.path.insert(0, 'packages')
from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner

scanner = AutonomousSuperPumpScanner()
symbols = ['ZAMAUSDT', 'BTRUSDT', 'PROMUSDT', 'NEARUSDT', 'BULLAUSDT', 'AKEUSDT', 'TRBUSDT', 'SOLUSDT', 'DOGEUSDT', '1000SATSUSDT']

for sym in symbols:
    res = scanner.scan_symbol_cycle(sym)
    if res:
        print(f"{sym:14} -> is_active: {str(res.get('is_active')):5} | Peak: {res.get('peak_n', 0):5.2f}x | Curr: {res.get('current_n', 0):5.2f}x | DD: {res.get('drawdown_pct', 0):5.1f}% | Stage: {res.get('stage')}")
    else:
        print(f"{sym:14} -> No macro cycle detected")
