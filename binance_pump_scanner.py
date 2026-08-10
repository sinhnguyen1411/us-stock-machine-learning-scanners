"""
CLI Scanner Root Entry Point (Monorepo Launcher)
"""

if __name__ == "__main__":
    from apps.cli_scanner.main import run_scanner_loop
    run_scanner_loop()
