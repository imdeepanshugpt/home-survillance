"""
Configuration — Edit this file with your settings
"""

class Config:

    # ── Ollama Model ─────────────────────────────────
    # Options:
    #   "moondream"  → 1.7GB, fastest  (8GB  RAM laptops)
    #   "llava"      → 4.7GB, balanced (16GB RAM laptops)
    #   "llava:13b"  → 8GB,   best     (32GB RAM laptops)
    OLLAMA_MODEL = "moondream"

    # ── Cameras ──────────────────────────────────────
    # For Hikvision IP cameras:
    #   "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101"
    #   Channel 101 = Cam1 main stream (HD)
    #   Channel 102 = Cam1 sub stream  (lower res, faster)
    #   Channel 201 = Cam2 main stream
    #
    # For laptop webcam testing:
    #   "Webcam": 0
    CAMERAS = {
        "Webcam Test": 0,
        # "Front Door": "rtsp://admin:PASSWORD@192.168.1.64:554/Streaming/Channels/101",
        # "Kitchen":    "rtsp://admin:PASSWORD@192.168.1.65:554/Streaming/Channels/101",
        # "Living Room":"rtsp://admin:PASSWORD@192.168.1.66:554/Streaming/Channels/101",
    }

    # ── Telegram ─────────────────────────────────────
    # Step 1: Message @BotFather on Telegram → /newbot → get TOKEN
    # Step 2: Message @userinfobot on Telegram → get your CHAT_ID
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID   = ""

    # # ── Tuning ───────────────────────────────────────
    # MOTION_THRESHOLD = 8000   # Lower = more sensitive, Higher = less sensitive
    # COOLDOWN_SECONDS = 60     # Min seconds between alerts per camera
    # CHECK_INTERVAL   = 2      # Seconds between frame checks
    # CHECK_INTERVAL   = 5      # Check every 5s instead of 2s (saves CPU)
    # MOTION_THRESHOLD = 12000  # Higher = less sensitive (fewer AI calls)
    # COOLDOWN_SECONDS = 120    # 2 min cooldown (fewer AI calls)
    # ── Tuning ───────────────────────────────────────
    MOTION_THRESHOLD = 8000   # Lower = more sensitive, Higher = less sensitive
    COOLDOWN_SECONDS = 60     # Min seconds between alerts per camera
    CHECK_INTERVAL   = 2      # Seconds between frame checks
