"""
Main Launcher — Runs surveillance + dashboard together
Usage: python main.py
"""

import threading
import time
import sys
import os

def run_dashboard():
    """Start web dashboard in background thread"""
    from dashboard import run_dashboard as start
    start(port=8089)

def run_surveillance():
    """Start surveillance engine"""
    from surveillance import start_surveillance
    start_surveillance()

def check_requirements():
    """Verify everything is set up correctly"""
    errors = []

    # Check Ollama running
    try:
        import ollama
        ollama.list()
    except Exception:
        errors.append("❌ Ollama not running. Start it with: ollama serve")

    # Check config
    from config import Config
    if Config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("⚠️  Telegram not configured (alerts will be skipped)")
    if not Config.CAMERAS:
        errors.append("❌ No cameras configured in config.py")

    return errors

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════╗")
    print("║   AI SURVEILLANCE SYSTEM             ║")
    print("║   Ollama + Telegram (100% Free)      ║")
    print("╚══════════════════════════════════════╝")
    print()

    # Pre-flight checks
    issues = check_requirements()
    if issues:
        for issue in issues:
            print(f"  {issue}")
        print()
        if any("❌" in i for i in issues):
            print("  Fix errors above then run again.")
            sys.exit(1)

    print("  ✓ All checks passed")
    print(f"  ✓ Dashboard → http://localhost:8089")
    print()

    # Start dashboard in background
    dash_thread = threading.Thread(target=run_dashboard, daemon=True)
    dash_thread.start()
    time.sleep(1)

    # Start surveillance (blocking)
    run_surveillance()
