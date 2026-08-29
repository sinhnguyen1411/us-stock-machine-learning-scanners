import urllib.request
import json
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

def scan():
    print("=== 1. SCANNING BINANCE FUTURES ===")
    url_f = 'https://fapi.binance.com/fapi/v1/ticker/24hr'
    req_f = urllib.request.Request(url_f, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_f, timeout=10) as resp:
        data_f = json.loads(resp.read().decode())
    
    candidates_f = []
    chinese_symbols = []
    for item in data_f:
        sym = item['symbol']
        last_price = float(item['lastPrice'])
        price_change_pct = float(item['priceChangePercent'])
        quote_vol = float(item['quoteVolume'])
        high_price = float(item['highPrice'])
        low_price = float(item['lowPrice'])
        
        # Check if symbol has non-ascii characters (e.g. Chinese characters)
        has_non_ascii = any(ord(char) > 127 for char in sym)
        if has_non_ascii:
            chinese_symbols.append({
                'symbol': sym,
                'price': last_price,
                'change_24h': price_change_pct,
                'quote_vol_m': quote_vol / 1e6
            })
            
        if 0.035 <= last_price <= 0.095:
            candidates_f.append({
                'symbol': sym,
                'price': last_price,
                'change_24h': price_change_pct,
                'quote_vol_m': quote_vol / 1e6,
                'high': high_price,
                'low': low_price,
                'has_non_ascii': has_non_ascii
            })
            
    print(f"Non-ASCII / Chinese Symbols found on Binance Futures: {len(chinese_symbols)}")
    for cs in chinese_symbols:
        print(f" -> CHINESE / NON-ASCII FUTURES: {cs['symbol']} | Price: ${cs['price']:.6f} | 24h: {cs['change_24h']:+.2f}% | Vol: ${cs['quote_vol_m']:.1f}M")
        
    candidates_f.sort(key=lambda x: abs(x['price'] - 0.064))
    print(f"\nAll candidates near 0.064 (sorted by closest to 0.064):")
    for c in candidates_f[:30]:
        print(f"FUTURES: {c['symbol']:<18} | Price: ${c['price']:<9.5f} (24h: {c['change_24h']:>+6.2f}%) | Vol: ${c['quote_vol_m']:>6.1f}M | Range: ${c['low']} - ${c['high']}")

    print("\n=== 2. SCANNING BINANCE SPOT ===")
    url_s = 'https://api.binance.com/api/v3/ticker/24hr'
    req_s = urllib.request.Request(url_s, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_s, timeout=10) as resp:
        data_s = json.loads(resp.read().decode())
        
    candidates_s = []
    chinese_spot = []
    for item in data_s:
        sym = item['symbol']
        if not sym.endswith('USDT'):
            continue
        last_price = float(item['lastPrice'])
        price_change_pct = float(item['priceChangePercent'])
        quote_vol = float(item['quoteVolume'])
        high_price = float(item['highPrice'])
        low_price = float(item['lowPrice'])
        
        has_non_ascii = any(ord(char) > 127 for char in sym)
        if has_non_ascii:
            chinese_spot.append({
                'symbol': sym,
                'price': last_price,
                'change_24h': price_change_pct,
                'quote_vol_m': quote_vol / 1e6
            })
            
        if 0.035 <= last_price <= 0.095:
            candidates_s.append({
                'symbol': sym,
                'price': last_price,
                'change_24h': price_change_pct,
                'quote_vol_m': quote_vol / 1e6,
                'high': high_price,
                'low': low_price,
                'has_non_ascii': has_non_ascii
            })
            
    print(f"Non-ASCII / Chinese Symbols found on Binance Spot: {len(chinese_spot)}")
    for cs in chinese_spot:
        print(f" -> CHINESE / NON-ASCII SPOT: {cs['symbol']} | Price: ${cs['price']:.6f} | 24h: {cs['change_24h']:+.2f}% | Vol: ${cs['quote_vol_m']:.1f}M")
        
    candidates_s.sort(key=lambda x: abs(x['price'] - 0.064))
    for c in candidates_s[:30]:
        print(f"SPOT:    {c['symbol']:<18} | Price: ${c['price']:<9.5f} (24h: {c['change_24h']:>+6.2f}%) | Vol: ${c['quote_vol_m']:>6.1f}M")

if __name__ == '__main__':
    scan()
