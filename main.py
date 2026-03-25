"""
main.py — Entry point
Starts surveillance engine + web dashboard together.

Usage:
    Local:  python3 main.py
    Docker: docker-compose up
"""

import sys
import os
import threading
import time

# ── Ensure src/ and config/ are importable ────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "config"))


def run_dashboard():
    from src.dashboard import run_dashboard as start
    from config import Config
    start(port=Config.DASHBOARD_PORT)


def run_surveillance():
    from src.surveillance import start_surveillance
    start_surveillance()


def check_requirements():
    errors   = []
    warnings = []

    # Check Ollama
    try:
        import ollama
        from config import Config
        client = ollama.Client(host=Config.OLLAMA_HOST)
        client.list()
    except Exception as e:
        errors.append(f"❌ Ollama not reachable — {e}")

    # Check config
    from config import Config

    if not Config.TELEGRAM_BOT_TOKEN:
        warnings.append("⚠️  Telegram token not set — alerts disabled")
    if not Config.TELEGRAM_CHAT_ID:
        warnings.append("⚠️  Telegram chat ID not set — alerts disabled")
    if not Config.CAMERAS:
        errors.append("❌ No cameras configured in config/config.py or CAMERA_* env vars")

    return errors, warnings


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════╗")
    print("║   AI SURVEILLANCE SYSTEM                 ║")
    print("║   Ollama + Telegram · 100% Free          ║")
    print("╚══════════════════════════════════════════╝")
    print()

    from config import Config
    print(f"  Model     : {Config.OLLAMA_MODEL}")
    print(f"  Ollama    : {Config.OLLAMA_HOST}")
    print(f"  Cameras   : {len(Config.CAMERAS)}")
    for name in Config.CAMERAS:
        print(f"              → {name}")
    print(f"  Dashboard : http://localhost:{Config.DASHBOARD_PORT}")
    print()

    errors, warnings = check_requirements()

    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")

    if errors:
        print()
        print("  Fix errors above then run again.")
        sys.exit(1)

    print("  ✓ All checks passed")
    print()

    # Start dashboard in background thread
    dash_thread = threading.Thread(target=run_dashboard, daemon=True)
    dash_thread.start()
    time.sleep(1)

    # Start surveillance (blocking main thread)
    run_surveillance()
