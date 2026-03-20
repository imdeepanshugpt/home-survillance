"""
AI Home Surveillance System
Uses Ollama (local AI) + Telegram for free alerts
"""

import cv2
import ollama
import base64
import time
import threading
import requests
import json
import os
from datetime import datetime
from config import Config

# ── State tracking ───────────────────────────────────
last_alert_time = {}
alert_log = []
camera_status = {}

# ── Telegram ─────────────────────────────────────────
def send_telegram(message, image_frame=None):
    """Send alert to Telegram with optional snapshot"""
    base_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}"
    try:
        if image_frame is not None:
            _, buf = cv2.imencode('.jpg', image_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            requests.post(
                f"{base_url}/sendPhoto",
                data={"chat_id": Config.TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "Markdown"},
                files={"photo": ("alert.jpg", buf.tobytes(), "image/jpeg")},
                timeout=10
            )
        else:
            requests.post(
                f"{base_url}/sendMessage",
                json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"},
                timeout=10
            )
        print(f"[TELEGRAM] Alert sent ✓")
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


# ── Frame capture ─────────────────────────────────────
def capture_frame(source, retries=3):
    """Capture a single frame from camera source"""
    for attempt in range(retries):
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return frame
        print(f"[WARN] Frame capture attempt {attempt+1} failed")
        time.sleep(2)
    return None


# ── Motion detection ──────────────────────────────────
def detect_motion(frame1, frame2):
    """Returns True if significant motion detected between frames"""
    diff  = cv2.absdiff(frame1, frame2)
    gray  = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    score = cv2.countNonZero(th)
    return score > Config.MOTION_THRESHOLD, score


# ── Ollama AI analysis ────────────────────────────────
def analyze_with_ollama(frame, camera_name):
    """Send frame to local Ollama model for analysis"""
    _, buf  = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_b64 = base64.b64encode(buf).decode('utf-8')

    prompt = f"""You are an outdoor home security AI monitoring: {camera_name}

Analyze this image and respond in this exact format:
THREAT: [None / Low / Medium / High]
ACTIVITY: [one sentence what you see]
ACTION: [what homeowner should do, or 'No action needed']

Watch for:
- People touching, approaching or looking into parked cars
- Someone loitering or pacing near property
- Tampering with gates, doors or vehicles
- Anyone carrying tools near vehicles suspiciously
- Unusual activity near the house entrance

If nothing suspicious: THREAT: None / ACTIVITY: Area clear / ACTION: No action needed"""

    try:
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }]
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"Analysis error: {e}"


# ── Save snapshot ─────────────────────────────────────
def save_snapshot(frame, camera_name):
    """Save snapshot to disk"""
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = camera_name.replace(" ", "_")
    path     = f"snapshots/{safe_name}_{ts}.jpg"
    cv2.imwrite(path, frame)
    return path


# ── Log alert ─────────────────────────────────────────
def log_alert(camera_name, analysis, snapshot_path):
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera": camera_name,
        "analysis": analysis,
        "snapshot": snapshot_path
    }
    alert_log.append(entry)

    # Write to log file
    with open("logs/alerts.json", "a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Camera monitor thread ─────────────────────────────
def monitor_camera(camera_name, source):
    """Main loop for monitoring a single camera"""
    print(f"[START] Monitoring: {camera_name}")
    camera_status[camera_name] = "connecting"
    prev_frame = None

    while True:
        try:
            frame = capture_frame(source)

            if frame is None:
                camera_status[camera_name] = "offline"
                print(f"[WARN] {camera_name} unreachable, retrying in 10s...")
                time.sleep(10)
                continue

            camera_status[camera_name] = "online"

            if prev_frame is not None:
                motion_detected, score = detect_motion(prev_frame, frame)

                if motion_detected:
                    now = time.time()
                    cooldown_ok = (now - last_alert_time.get(camera_name, 0)) >= Config.COOLDOWN_SECONDS

                    if cooldown_ok:
                        print(f"[MOTION] {camera_name} (score: {score}) — analyzing...")
                        analysis = analyze_with_ollama(frame, camera_name)

                        threat = "none"
                        if "threat:" in analysis.lower():
                            line = [l for l in analysis.splitlines() if "threat:" in l.lower()]
                            if line:
                                threat = line[0].lower().split("threat:")[-1].strip()

                        # Emoji based on threat level
                        icons = {
                            "high":   "🔴",
                            "medium": "🟡",
                            "low":    "🟢",
                            "none":   "✅"
                        }
                        icon = icons.get(threat, "⚠️")

                        if threat != "none":
                            timestamp = datetime.now().strftime("%I:%M %p, %b %d")
                            snapshot  = save_snapshot(frame, camera_name)
                            msg = (
                                f"{icon} *{threat.upper()} THREAT*\n"
                                f"📷 *{camera_name}*\n"
                                f"⏰ {timestamp}\n\n"
                                f"{analysis}"
                            )
                            send_telegram(msg, image_frame=frame)
                            log_alert(camera_name, analysis, snapshot)
                            last_alert_time[camera_name] = now
                            print(f"[{threat.upper()}] Alert sent for {camera_name}")
                        else:
                            print(f"[CLEAR] {camera_name} — no threat detected")

            prev_frame = frame
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            print(f"[ERROR] {camera_name}: {e}")
            camera_status[camera_name] = "error"
            time.sleep(10)


# ── Entry point ───────────────────────────────────────
def start_surveillance():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("snapshots", exist_ok=True)

    print("=" * 50)
    print("  AI SURVEILLANCE SYSTEM")
    print(f"  Model  : {Config.OLLAMA_MODEL}")
    print(f"  Cameras: {len(Config.CAMERAS)}")
    print("=" * 50)

    send_telegram(
        f"🏠 *Surveillance System ONLINE*\n"
        f"📷 {len(Config.CAMERAS)} camera(s) active\n"
        f"🤖 Model: {Config.OLLAMA_MODEL}\n"
        f"⏰ {datetime.now().strftime('%I:%M %p, %b %d')}"
    )

    threads = []
    for name, source in Config.CAMERAS.items():
        t = threading.Thread(target=monitor_camera, args=(name, source), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(1)  # Stagger camera starts

    for t in threads:
        t.join()


if __name__ == "__main__":
    start_surveillance()
