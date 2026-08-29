import urllib.request
import json
import urllib.parse
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')

def main():
    sym = '龙虾USDT'
    enc_sym = urllib.parse.quote(sym)
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={enc_sym}&interval=1d&limit=15'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        klines = json.loads(resp.read().decode())

    print(f"=== LỊCH SỬ GIÁ 15 NGÀY GẦN NHẤT CỦA {sym} ===")
    for k in klines:
        dt = datetime.datetime.fromtimestamp(k[0]/1000).strftime('%Y-%m-%d')
        o, h, l, c, v = float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
        print(f"{dt} | Mở: ${o:.5f} | Cao: ${h:.5f} | Thấp: ${l:.5f} | Đóng: ${c:.5f} | Khối lượng: {v:,.0f}")

    # Check 24h ticker
    url_24 = f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={enc_sym}'
    req_24 = urllib.request.Request(url_24, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_24, timeout=10) as resp:
        t24 = json.loads(resp.read().decode())
    
    print("\n=== THÔNG SỐ REALTIME 24H ===")
    print(f"Symbol: {t24['symbol']}")
    print(f"Giá hiện tại (Last Price): ${float(t24['lastPrice']):.6f}")
    print(f"Tăng trưởng 24h (Change): {float(t24['priceChangePercent']):+.2f}%")
    print(f"Đỉnh 24h (High): ${float(t24['highPrice']):.6f}")
    print(f"Đáy 24h (Low): ${float(t24['lowPrice']):.6f}")
    print(f"Khối lượng giao dịch 24h: ${float(t24['quoteVolume'])/1e6:,.1f} Triệu USD")

if __name__ == '__main__':
    main()
