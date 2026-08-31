import json
import re
import os

db_path = "data/pump_events_db.json"
print("Reading", db_path)

with open(db_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Match every event object between { "symbol": ... }
raw_blocks = re.findall(r'\{\s*"symbol":\s*"[^"]+".*?\n    \}', content, re.DOTALL)
print(f"Found {len(raw_blocks)} candidate blocks")

valid_events = []
for b in raw_blocks:
    try:
        obj = json.loads(b)
        if "symbol" in obj and "n_actual" in obj:
            valid_events.append(obj)
    except Exception:
        # Clean control characters and try again
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', b)
        cleaned = re.sub(r',\s*\}', '}', cleaned)
        try:
            obj = json.loads(cleaned)
            if "symbol" in obj and "n_actual" in obj:
                valid_events.append(obj)
        except Exception:
            pass

print(f"Extracted {len(valid_events)} valid event records")

# Deduplicate
seen = set()
unique_events = []
for ev in valid_events:
    key = (ev["symbol"], ev.get("event_date"))
    if key not in seen:
        seen.add(key)
        unique_events.append(ev)

print(f"Total unique events: {len(unique_events)}")

payload = {
    "version": "1.0",
    "count": len(unique_events),
    "events": unique_events
}

# Backup first
os.replace(db_path, db_path + ".bak")

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print("Saved clean reconstructed data/pump_events_db.json!")
