"""
Configuration — Edit this file with your settings
"""
from urllib.parse import quote

def make_rtsp(ip, password, username="admin", channel=101):
    """Safely builds RTSP URL — handles special chars like @ in password"""
    encoded = quote(password, safe='')
    return f"rtsp://{username}:{encoded}@{ip}:554/Streaming/Channels/{channel}"

class Config:

    # ── Ollama Model ─────────────────────────────────
    # "moondream"  → 1.7GB, fastest  (8GB  RAM — Intel Mac)
    # "llava"      → 4.7GB, balanced (16GB RAM)
    # "llava:13b"  → 8GB,   best     (32GB RAM)
    OLLAMA_MODEL = "moondream"

    # ── Cameras ──────────────────────────────────────
    # Name drives the AI profile used:
    # "Outside ..."  → outdoor security AI
    # "Kitchen ..."  → hygiene + safety AI
    # "Front Door"   → entrance security AI
    # "Garage ..."   → vehicle security AI
    # anything else  → general security AI
    CAMERAS = {
        "Outside Gate and Car": make_rtsp("192.168.1.8", "password"),
        "Porach":      make_rtsp("192.168.1.3", "password"),
        "Porach":      make_rtsp("192.168.1.5", "password"),
        "Outside Car":      make_rtsp("192.168.1.6", "password"),
        # "Webcam":    0,   # uncomment to add webcam
    }

    # ── Telegram ─────────────────────────────────────
    # Get token from @BotFather on Telegram
    # Get chat ID from @userinfobot on Telegram
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID   = ""

    # ── Low Light Enhancement ─────────────────────────
    # True  = boost dark/dim images using CLAHE algorithm
    # False = use raw image as-is
    ENHANCE_LOW_LIGHT = True

    # ── Tuning ───────────────────────────────────────
    MOTION_THRESHOLD = 3000   # Lower = more sensitive to movement
    COOLDOWN_SECONDS = 30     # Min seconds between alerts per camera
    CHECK_INTERVAL   = 2      # Seconds between frame captures
    SEND_ALL_FRAMES  = True


