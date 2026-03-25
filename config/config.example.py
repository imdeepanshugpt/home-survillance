"""
Configuration
Reads from environment variables (Docker) or falls back to defaults.
For local dev: set values directly or use a .env file.
For Docker:    set in .env file or docker-compose.yml
"""

import os
from urllib.parse import quote


def fix_rtsp_url(url):
    """
    Fixes RTSP URLs where password contains @ symbol.
    e.g. rtsp://admin:cctv@12345@192.168.1.8:554/...
    Works by splitting on the LAST @ to find the host.
    """
    if not url.startswith("rtsp://"):
        return url

    # Remove rtsp://
    rest = url[7:]

    # Split on LAST @ to separate credentials from host
    last_at = rest.rfind("@")
    if last_at == -1:
        return url  # no @ found, return as-is

    credentials = rest[:last_at]   # admin:cctv@12345
    host_path   = rest[last_at+1:] # 192.168.1.8:554/Streaming/...

    # Split credentials into username:password
    colon = credentials.find(":")
    if colon == -1:
        return url

    username = credentials[:colon]
    password = credentials[colon+1:]

    # URL-encode the password
    encoded  = quote(password, safe="")

    return f"rtsp://{username}:{encoded}@{host_path}"


def make_rtsp(url_or_ip, password=None, username="admin", channel=101):
    """
    Accepts either:
    - Full RTSP URL (from env var): make_rtsp("rtsp://admin:cctv@12345@ip:554/...")
    - IP + password:                make_rtsp("192.168.1.8", "cctv@12345")
    Handles special characters like @ in password automatically.
    """
    if url_or_ip.startswith("rtsp://"):
        return fix_rtsp_url(url_or_ip)
    else:
        encoded = quote(password or "", safe="")
        return f"rtsp://{username}:{encoded}@{url_or_ip}:554/Streaming/Channels/{channel}"


def get_cameras_from_env():
    """
    Auto-discovers cameras from environment variables.
    Any env var starting with CAMERA_ is treated as a camera.
    e.g. CAMERA_Outside_Car=rtsp://admin:cctv@12345@ip:554/...
      → {"Outside Car": "rtsp://admin:cctv%4012345@ip:554/..."}
    Automatically fixes passwords containing @ symbol.
    """
    cameras = {}
    for key, value in os.environ.items():
        if key.startswith("CAMERA_") and value:
            name = key[7:].replace("_", " ")
            # Fix @ in password before storing
            cameras[name] = fix_rtsp_url(value)
    return cameras


class Config:

    # ── Ollama Model ─────────────────────────────────
    # Set via env: OLLAMA_MODEL=llava
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava")

    # ── Ollama Host ───────────────────────────────────
    # Docker:     http://ollama:11434  (service name)
    # Local dev:  http://localhost:11434
    OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # ── Telegram ─────────────────────────────────────
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

    # ── Cameras ──────────────────────────────────────
    # Auto-loaded from CAMERA_* environment variables
    # Falls back to hardcoded values if no env vars set
    _env_cameras = get_cameras_from_env()
    CAMERAS = _env_cameras if _env_cameras else {
        "Webcam":    0,
    }

    # ── Low Light Enhancement ─────────────────────────
    ENHANCE_LOW_LIGHT = os.getenv("ENHANCE_LOW_LIGHT", "true").lower() == "true"

    # ── Testing ───────────────────────────────────────
    # True  = send every analyzed frame to Telegram (testing)
    # False = only send when threat detected (production)
    SEND_ALL_FRAMES = os.getenv("SEND_ALL_FRAMES", "false").lower() == "true"

    # ── Tuning ───────────────────────────────────────
    MOTION_THRESHOLD = int(os.getenv("MOTION_THRESHOLD", "3000"))
    COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "30"))
    CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL",   "2"))

    # ── Dashboard ────────────────────────────────────
    DASHBOARD_PORT   = int(os.getenv("DASHBOARD_PORT",   "8080"))
