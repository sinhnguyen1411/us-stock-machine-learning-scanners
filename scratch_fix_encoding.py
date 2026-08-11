# -*- coding: utf-8 -*-
"""Fix script: replace corrupted phase_tag and recommendation strings in pre_pump_detector.py"""
import pathlib

path = pathlib.Path("packages/core_engine/pre_pump_detector.py")
content = path.read_bytes().decode("utf-8", errors="replace")

# Print current corrupted phase_tag lines
print("=== Current phase_tag lines ===")
for i, line in enumerate(content.split("\n"), 1):
    if "phase_tag" in line and "=" in line:
        print(f"  L{i}: {repr(line[:100])}")

print()
print("=== Replacing... ===")

# Map of old substring patterns -> new clean strings
# Use exact byte-level replacement to avoid regex issues with corrupted chars
fixes = [
    # Each tuple: (search_marker, new_full_line_content)
    # We'll replace the entire line containing the marker
]

# Instead: replace line by line
lines = content.split("\n")
new_lines = []
for line in lines:
    stripped = line.strip()

    # ── PHASE TAGS ──
    if "phase_tag" in stripped and "=" in stripped and not stripped.startswith("#"):
        if "SQUEEZE" in stripped or "SHORT SQUEEZE" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f525 SHORT SQUEEZE (10X-40X)"')
        elif "IGNITION" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f680 VUA MOI LUA (IGNITION)"')
        elif "WYCKOFF" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f3d7 NEN WYCKOFF (SIDEWAYS BASE)"')
        elif "PLATEAU" in stripped or "DINH" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f3d4 NEN VUNG DINH (HIGH PLATEAU)"')
        elif "SHORT TRAP" in stripped or "PHI AM" in stripped or "BáºªY" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f6a8 BAY PHI AM (SHORT TRAP)"')
        elif "COILING" in stripped or "NEN DAY" in stripped or "ÄANG" in stripped or "NÃ‰N" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\U0001f9ca DANG NEN DAY (COILING)"')
        elif "BINH" in stripped or "NORMAL" in stripped or "âšª" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'phase_tag = "\u26aa BINH THUONG"')
        else:
            new_lines.append(line)

    # ── RECOMMENDATIONS (single-line only, not f-string continuations) ──
    elif "recommendation" in stripped and "=" in stripped and '"' in stripped and not stripped.startswith("#") and "f\"" not in stripped[:stripped.index("=") + 3 if "=" in stripped else 0]:
        indent = line[:len(line) - len(line.lstrip())]
        # Detect by context markers in the corrupted text
        if "THANH L" in line or "THANH LY" in line or "gong" in line or "Trailing Stop" in line:
            new_lines.append(indent + 'recommendation = "\U0001f6a8 BAY THANH LY: Phe Short chiu phi am, may xay thanh ly ep gia dung cot. Kich hoat Trailing Stop 12% de gong."')
        elif "CO HOI" in line or "moi lua" in line.lower() or "thoat" in line or "VolSpike" in line or "2.2x" in line:
            new_lines.append(indent + 'recommendation = "\u26a1 CO HOI VANG: Cay nen moi lua bung no (Vol Spike > 2.2x, nen xanh). Da thoat khoi vung nen, dong tien ca voi da kich hoat."')
        elif "BAY SHORT" in line or "bu dong" in line or "CHUA" in line:
            new_lines.append(indent + 'recommendation = "\U0001f6a8 BAY SHORT CUC NANG: Phe Short bu dong (Funding am sau < -0.2%), nhung CHUA co nen moi xanh. Cho nen moi Volume xac nhan de Long."')
        elif "phat hien" in line or "bat doi" in line or "BINH" in line:
            new_lines.append(indent + 'recommendation = "Chua phat hien su bat doi xung thanh khoan hay tin hieu moi lua ro ret."')
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

new_content = "\n".join(new_lines)
path.write_bytes(new_content.encode("utf-8"))
print("Done! Written back as UTF-8.")

# Verify
content2 = path.read_bytes().decode("utf-8")
print("\n=== New phase_tag lines ===")
for i, line in enumerate(content2.split("\n"), 1):
    if "phase_tag" in line and "=" in line and not line.strip().startswith("#"):
        print(f"  L{i}: {line.strip()}")
