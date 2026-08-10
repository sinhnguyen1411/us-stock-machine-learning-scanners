"""
Root Web Application Entry Point (Monorepo Launcher)
"""

import os
import sys
from pathlib import Path

# Add packages directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

if __name__ == "__main__":
    from apps.web_terminal.app import app, radar_scanner_loop
    import threading

    radar_thread = threading.Thread(target=radar_scanner_loop, daemon=True)
    radar_thread.start()

    port = int(os.getenv("PORT", 5050))
    print(f"""
============================================================
  DEEPALPHA BINANCE FUTURES MONOREPO WEB TERMINAL RUNNING!
  Access Web UI at: http://localhost:{port}
============================================================
    """)
    app.run(host="127.0.0.1", port=port, debug=False)
