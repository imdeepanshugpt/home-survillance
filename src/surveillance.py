"""
src/surveillance.py
Core surveillance engine — motion detection + AI analysis + Telegram alerts
"""

import cv2
import ollama
import base64
import time
import threading
import requests
import json
import os
import re
import subprocess
import numpy as np
from datetime import datetime

# ── Import config from config/ package ───────────────
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# ── State tracking ───────────────────────────────────
last_alert_time = {}
alert_log       = []
camera_status   = {}

# ── Camera intelligence profiles ─────────────────────
CAMERA_PROFILES = {

    "outside": {
        "label": "Outdoor / Property",
        "prompt": """Look at this security camera image carefully.

Answer these questions in simple sentences:
1. How many people do you see? Describe what each person is doing.
2. Is anything suspicious happening? (tampering, damage, loitering)
3. Describe the vehicles and property visible.

Then give a threat level:
- NONE if everything looks normal
- LOW if something is slightly unusual
- MEDIUM if someone is acting suspiciously
- HIGH if someone is damaging property or breaking in
- CRITICAL if there is active violence or emergency

End your response with exactly one line:
THREAT: [None/Low/Medium/High/Critical]""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "kitchen": {
        "label": "Kitchen / Food Area",
        "prompt": """Look at this kitchen camera image carefully.

Answer these questions in simple sentences:
1. How many people are in the kitchen? What is each person doing?
2. What food or dish is being prepared?
3. Are there any hygiene problems? (dirty hands, hair in food, cross contamination)
4. Are there any safety hazards? (unattended flame, boiling over, knives at edge)
5. Is anyone doing something they should not? (stealing food, eating from pot, on phone)

Then give a threat level:
- NONE if everything is fine
- LOW if something minor is wrong
- MEDIUM if there is a hygiene or safety concern
- HIGH if there is a serious safety risk or misconduct
- CRITICAL if there is a fire or emergency

End your response with exactly one line:
THREAT: [None/Low/Medium/High/Critical]""",
        "alert_on": ["medium", "high", "critical"]
    },

    "entrance": {
        "label": "Main Entrance / Door",
        "prompt": """Look at this entrance camera image carefully.

Answer these questions in simple sentences:
1. How many people are at the entrance? Describe their appearance.
2. What are they doing? (ringing bell, waiting, trying door, looking around)
3. Does anything look suspicious? (trying to force entry, hiding face, checking locks)

Then give a threat level:
- NONE if it looks like a normal visitor or resident
- LOW if something is slightly unusual
- MEDIUM if the person is acting suspiciously
- HIGH if someone is trying to break in or force entry
- CRITICAL if there is active break-in or violence

End your response with exactly one line:
THREAT: [None/Low/Medium/High/Critical]""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "garage": {
        "label": "Garage / Parking",
        "prompt": """Look at this garage or parking camera image carefully.

Answer these questions in simple sentences:
1. How many people do you see? What is each person doing?
2. Describe the vehicles. Is anyone touching or near the vehicles?
3. Is anyone doing something suspicious? (checking handles, crouching under car, using tools)

Then give a threat level:
- NONE if everything is normal
- LOW if something is slightly unusual
- MEDIUM if someone is acting suspiciously near a vehicle
- HIGH if someone is breaking into or damaging a vehicle
- CRITICAL if there is active theft or violence

End your response with exactly one line:
THREAT: [None/Low/Medium/High/Critical]""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "general": {
        "label": "General Area",
        "prompt": """Look at this security camera image carefully.

Answer these questions in simple sentences:
1. How many people do you see? What is each person doing?
2. Does anything look unusual or out of place?
3. Are there any safety or security concerns?

Then give a threat level:
- NONE if everything looks normal
- LOW if something is slightly unusual
- MEDIUM if there is a moderate concern
- HIGH if there is a serious security issue
- CRITICAL if there is an emergency

End your response with exactly one line:
THREAT: [None/Low/Medium/High/Critical]""",
        "alert_on": ["low", "medium", "high", "critical"]
    }
}


# ── Detect camera profile from name ──────────────────
def get_profile(camera_name):
    name = camera_name.lower()
    if any(w in name for w in ["outside","outdoor","car","parking","street","garden","yard","front","back","gate"]):
        return CAMERA_PROFILES["outside"]
    elif any(w in name for w in ["kitchen","cook","chef","dining","food"]):
        return CAMERA_PROFILES["kitchen"]
    elif any(w in name for w in ["entrance","door","entry","lobby"]):
        return CAMERA_PROFILES["entrance"]
    elif any(w in name for w in ["garage","workshop","store","storage"]):
        return CAMERA_PROFILES["garage"]
    else:
        return CAMERA_PROFILES["general"]


# ── Telegram ─────────────────────────────────────────
def send_telegram(message, image_frame=None):
    base_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}"
    try:
        if image_frame is not None:
            _, buf = cv2.imencode('.jpg', image_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
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
        print("[TELEGRAM] Sent ✓")
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


# ── Low light enhancement ─────────────────────────────
def enhance_low_light(frame):
    lab      = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b  = cv2.split(lab)
    clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl       = clahe.apply(l)
    merged   = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


# ── Frame capture ─────────────────────────────────────
def capture_frame(source, retries=3):
    # Webcam → OpenCV
    if isinstance(source, int):
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 160)
        cap.set(cv2.CAP_PROP_CONTRAST,   50)
        ret, frame = cap.read()
        cap.release()
        if ret and Config.ENHANCE_LOW_LIGHT:
            frame = enhance_low_light(frame)
        return frame if ret else None

    # RTSP → ffmpeg subprocess
    for attempt in range(retries):
        try:
            probe = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-rtsp_transport', 'tcp',
                    '-print_format', 'json',
                    '-show_streams',
                    source,
                ],
                capture_output=True, timeout=10
            )
            streams = json.loads(probe.stdout).get('streams', [])
            video   = next((s for s in streams if s['codec_type'] == 'video'), None)
            if not video:
                time.sleep(2)
                continue

            w = int(video['width'])
            h = int(video['height'])

            result = subprocess.run([
                'ffmpeg', '-rtsp_transport', 'tcp',
                '-i', source, '-frames:v', '1',
                '-f', 'image2pipe', '-pix_fmt', 'bgr24',
                '-vcodec', 'rawvideo', '-loglevel', 'quiet', 'pipe:1'
            ], capture_output=True, timeout=15)

            if result.returncode == 0 and len(result.stdout) == w * h * 3:
                frame = np.frombuffer(result.stdout, dtype=np.uint8).reshape((h, w, 3)).copy()
                if Config.ENHANCE_LOW_LIGHT:
                    frame = enhance_low_light(frame)
                return frame

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT {attempt+1}]")
        except Exception as e:
            print(f"[ERROR {attempt+1}] {e}")
        time.sleep(2)

    return None


# ── Motion detection ──────────────────────────────────
def detect_motion(frame1, frame2):
    diff  = cv2.absdiff(frame1, frame2)
    gray  = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    score = cv2.countNonZero(th)
    return score > Config.MOTION_THRESHOLD, score


# ── Parse AI response ─────────────────────────────────
def parse_analysis(text):
    threat   = ""
    activity = ""

    # Find THREAT: line
    for line in text.splitlines():
        if line.strip().lower().startswith("threat:"):
            threat = line.split(":", 1)[-1].strip().strip("[]").lower()

    # Everything except THREAT line = activity
    activity_lines = [
        l.strip() for l in text.splitlines()
        if l.strip() and not l.strip().lower().startswith("threat:")
    ]
    activity = " ".join(activity_lines).strip()[:500]

    # Keyword fallback if threat not parsed
    if threat not in ["none", "low", "medium", "high", "critical"]:
        tl = text.lower()
        if any(w in tl for w in ["break", "smash", "steal", "weapon", "assault", "fire", "forced"]):
            threat = "high"
        elif any(w in tl for w in ["suspicious", "loiter", "tamper", "crouch", "hiding", "damage"]):
            threat = "medium"
        elif any(w in tl for w in ["unusual", "unfamiliar", "staring", "lingering"]):
            threat = "low"
        else:
            threat = "none"

    # People count
    people = "0"
    if any(w in text.lower() for w in ["person", "people", "man", "woman", "individual", "someone"]):
        nums = re.findall(r'\b(\d+)\b', text)
        people = nums[0] if nums else "1+"

    return {"threat": threat, "activity": activity, "people": people}


# ── Format Telegram message ───────────────────────────
def format_alert(camera_name, profile, parsed, timestamp, is_clear=False):
    threat = parsed["threat"].upper()
    icons  = {"NONE":"✅","LOW":"🟢","MEDIUM":"🟡","HIGH":"🔴","CRITICAL":"🆘"}
    icon   = icons.get(threat, "⚠️")
    header = f"✅ *ALL CLEAR — {profile['label']}*" if is_clear else f"{icon} *{threat} — {profile['label']}*"

    return "\n".join([
        header,
        f"📷 *{camera_name}*",
        f"⏰ {timestamp}",
        "",
        f"👥 *People:* {parsed['people']}",
        "",
        "📋 *Analysis:*",
        parsed["activity"],
    ])


# ── Ollama AI analysis ────────────────────────────────
def analyze_with_ollama(frame, camera_name):
    profile = get_profile(camera_name)
    _, buf  = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    img_b64 = base64.b64encode(buf).decode('utf-8')
    try:
        client   = ollama.Client(host=Config.OLLAMA_HOST)
        response = client.chat(
            model=Config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": profile["prompt"], "images": [img_b64]}]
        )
        raw = response['message']['content'].strip()
        print(f"\n[AI RAW]\n{raw}\n{'─'*40}")
        return raw, profile
    except Exception as e:
        print(f"[OLLAMA ERROR] {e}")
        return f"Unable to analyze. Error: {e}\nTHREAT: None", profile


# ── Save snapshot ─────────────────────────────────────
def save_snapshot(frame, camera_name):
    os.makedirs(Config.SNAPSHOTS_DIR, exist_ok=True)
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = camera_name.replace(" ", "_")
    path      = os.path.join(Config.SNAPSHOTS_DIR, f"{safe_name}_{ts}.jpg")
    cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return path


# ── Log alert ─────────────────────────────────────────
def log_alert(camera_name, analysis, snapshot_path, threat):
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    entry = {
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera":   camera_name,
        "threat":   threat,
        "analysis": analysis,
        "snapshot": snapshot_path
    }
    alert_log.append(entry)
    log_path = os.path.join(Config.LOGS_DIR, "alerts.json")
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Camera monitor thread ─────────────────────────────
def monitor_camera(camera_name, source):
    print(f"[START] {camera_name} → {get_profile(camera_name)['label']}")
    camera_status[camera_name] = "connecting"
    prev_frame = None

    while True:
        try:
            frame = capture_frame(source)

            if frame is None:
                camera_status[camera_name] = "offline"
                print(f"[OFFLINE] {camera_name} — retrying in 10s")
                time.sleep(10)
                continue

            camera_status[camera_name] = "online"

            if prev_frame is not None:
                motion_detected, score = detect_motion(prev_frame, frame)
                if motion_detected:
                    now = time.time()
                    if (now - last_alert_time.get(camera_name, 0)) >= Config.COOLDOWN_SECONDS:
                        print(f"[MOTION] {camera_name} score={score} — analyzing...")
                        raw, profile = analyze_with_ollama(frame, camera_name)
                        parsed       = parse_analysis(raw)
                        threat       = parsed["threat"].lower()
                        timestamp    = datetime.now().strftime("%I:%M %p, %b %d")

                        if threat in profile["alert_on"]:
                            snapshot = save_snapshot(frame, camera_name)
                            msg      = format_alert(camera_name, profile, parsed, timestamp)
                            send_telegram(msg, image_frame=frame)
                            log_alert(camera_name, raw, snapshot, threat)
                            last_alert_time[camera_name] = now
                            print(f"[ALERT] {threat.upper()} — {camera_name}")

                        elif Config.SEND_ALL_FRAMES:
                            msg = format_alert(camera_name, profile, parsed, timestamp, is_clear=True)
                            send_telegram(msg, image_frame=frame)
                            last_alert_time[camera_name] = now
                            print(f"[TEST] Frame sent — {camera_name}")

                        else:
                            print(f"[CLEAR] {camera_name}")

            prev_frame = frame
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            print(f"[ERROR] {camera_name}: {e}")
            camera_status[camera_name] = "error"
            time.sleep(10)


# ── Entry point ───────────────────────────────────────
def start_surveillance():
    # os.makedirs(Config.LOGS_DIR,      exist_ok=True)
    # os.makedirs(Config.SNAPSHOTS_DIR, exist_ok=True)

    print("=" * 55)
    print("  AI SURVEILLANCE — INTELLIGENT ANALYSIS")
    print(f"  Model      : {Config.OLLAMA_MODEL}")
    print(f"  Host       : {Config.OLLAMA_HOST}")
    print(f"  Cameras    : {len(Config.CAMERAS)}")
    print(f"  Low Light  : {'ON' if Config.ENHANCE_LOW_LIGHT else 'OFF'}")
    print(f"  Test Mode  : {'ON' if Config.SEND_ALL_FRAMES else 'OFF'}")
    print("=" * 55)
    for name in Config.CAMERAS:
        print(f"  📷 {name:25s} → {get_profile(name)['label']}")
    print("=" * 55)

    send_telegram(
        f"🏠 *Surveillance ONLINE*\n"
        f"📷 {len(Config.CAMERAS)} camera(s) active\n"
        f"🤖 Model: {Config.OLLAMA_MODEL}\n"
        f"🧪 Test mode: {'ON' if Config.SEND_ALL_FRAMES else 'OFF'}\n"
        f"⏰ {datetime.now().strftime('%I:%M %p, %b %d')}"
    )

    threads = []
    for name, source in Config.CAMERAS.items():
        t = threading.Thread(target=monitor_camera, args=(name, source), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(1)

    for t in threads:
        t.join()


if __name__ == "__main__":
    start_surveillance()
