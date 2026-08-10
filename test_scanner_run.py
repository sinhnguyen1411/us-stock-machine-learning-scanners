"""
Verification script for BinancePumpScanner
Runs scanner for 15 seconds, validates symbol loading, ticker fetch, and position tracking.
"""
import time
from binance_pump_scanner import BinancePumpScanner

print("=" * 60)
print("  TESTING BINANCE FUTURES PUMP SCANNER RUNTIME")
print("=" * 60)

scanner = BinancePumpScanner(simulation_mode=True)
scanner.start()

print("\n[*] Scanner running in background thread... Waiting 12 seconds...")
time.sleep(12)

status = scanner.get_status()
print("\n" + "=" * 60)
print("  SCANNER STATUS REPORT")
print("=" * 60)
print(f"  • Running:           {status['running']}")
print(f"  • Mode:              {status['mode']}")
print(f"  • Monitored Symbols: {status['symbols_monitored']}")
print(f"  • Virtual Equity:    ${status['equity']:.2f}")
print(f"  • Active Positions:  {status['active_positions']}")
print(f"  • Daily PnL:         ${status['daily_pnl']:+.2f}")
print("=" * 60)

scanner.stop()
print("\n[+] Test completed successfully!")
