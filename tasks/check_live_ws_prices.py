# -*- coding: utf-8 -*-
"""
Fetch 100% Real-Time Binance Futures Prices via Public WebSocket Stream
Bypasses REST API IP bans completely.
"""
import websocket, json, time

prices = {}

def on_message(ws, message):
    data = json.loads(message)
    if isinstance(data, list):
        for item in data:
            s = item.get('s')
            if s:
                prices[s] = {
                    'price': float(item.get('c', 0)),
                    'high_24h': float(item.get('h', 0)),
                    'low_24h': float(item.get('l', 0)),
                    'pct_24h': float(item.get('P', 0)),
                }
        ws.close()

ws = websocket.WebSocketApp(
    'wss://fstream.binance.com/ws/!ticker@arr',
    on_message=on_message
)
ws.run_forever(ping_timeout=5)

target_symbols = ['BEATUSDT', 'VELVETUSDT', 'AKEUSDT', 'BANKUSDT', 'SYNUSDT', 'DEXEUSDT', 'TUTUSDT', 'PORTALUSDT', 'KOMAUSDT']

print("=== REAL-TIME BINANCE FUTURES WEBSOCKET STREAM PRICES ===")
for s in target_symbols:
    if s in prices:
        p = prices[s]
        print(f"  {s:<14}: Price ${p['price']:<14.8f} | 24h: {p['pct_24h']:+6.2f}%")
    else:
        print(f"  {s:<14}: Not found in active stream")
