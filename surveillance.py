"""
AI Home Surveillance System
Deep intelligent analysis + low light enhancement
Uses ffmpeg for RTSP + Ollama (local AI) + Telegram alerts
"""

import cv2
import ollama
import base64
import time
import threading
import requests
import json
import os
import subprocess
import numpy as np
from datetime import datetime
from config import Config

# ── State tracking ───────────────────────────────────
last_alert_time = {}
alert_log       = []
camera_status   = {}

# ── Per-camera intelligence profiles ─────────────────
CAMERA_PROFILES = {

    "outside": {
        "label": "Outdoor / Property",
        "prompt": """You are an expert outdoor property security analyst with 20 years of experience.
Study every pixel of this image with forensic-level attention.

Respond in EXACTLY this format:
THREAT: [None / Low / Medium / High / Critical]
PEOPLE: [exact number visible]
ACTIVITY: [3-4 detailed sentences — every person, their exact position, what each hand is doing, posture, pace, direction of gaze, interaction with objects or property]
DAMAGE: [any visible damage to property, vehicles, walls, gates in precise detail — or None]
OBJECTS: [every tool, bag, or object visible and who is near it]
CONCERN: [expert security assessment — why this is or is not suspicious with specific observations]
ACTION: [precise owner action — e.g. call police immediately, check vehicle now, review footage]

Analyse with forensic detail:

PEOPLE — describe each person precisely:
- Exact location (crouching behind rear tyre, standing at front gate, walking along wall)
- Every hand movement (right hand reaching into bag, left hand pulling door handle)
- Body language (nervous glancing, slow deliberate movements, running, frozen still)
- Clothing (dark hoodie, cap pulled low, gloves, carrying black backpack)

PROPERTY DAMAGE — report precisely:
- Scratches, dents or marks on vehicles
- Broken glass, locks, hinges, fencing
- Graffiti or new markings on walls
- Damaged cables, meters or pipes

VEHICLES:
- Person touching, leaning on, crouching under or beside any vehicle
- Door handles being tested or windows examined
- Person lying under vehicle (possible catalytic converter theft)
- Tyres being touched, punctured or deflated

THREAT LEVELS:
Critical = active break-in, assault, fire, person under vehicle right now
High     = tampering with locks or vehicles, property damage happening
Medium   = loitering 2+ minutes, suspicious close examination of property
Low      = slow walk-by with staring, unfamiliar vehicle parked long time

If nothing suspicious at all: THREAT: None""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "kitchen": {
        "label": "Kitchen / Food Area",
        "prompt": """You are a professional kitchen hygiene inspector and food safety expert conducting an official inspection.
Analyze every detail of this kitchen image like you are writing an official report.

Respond in EXACTLY this format:
THREAT: [None / Low / Medium / High / Critical]
PEOPLE: [exact number visible]
ACTIVITY: [3-4 detailed sentences — exactly what each person is doing step by step, what they are cooking, which utensils they are using, how they are handling food and ingredients]
DISH: [what is being cooked — be specific, e.g. chopping onions for curry, deep frying chicken, kneading dough for bread]
HYGIENE: [list every hygiene observation good or bad — be specific and detailed, or Good if perfect]
SAFETY: [list every safety concern with exact detail — which burner, how high the flame, what is at risk — or Safe]
CONCERN: [your most important finding the owner must know right now]
ACTION: [precise corrective action, or No action needed]

Inspect every detail:

ACTIVITY — describe like writing a food safety report:
- Is person washing hands, wearing gloves, wearing hairnet
- Exact cooking technique step by step
- How ingredients are handled and stored
- Is food covered or exposed on counter
- Flame height and cooking temperature

HYGIENE — check and state each:
- Hand washing before touching food
- Touching face, hair, nose, phone then food
- Cross contamination (raw meat near vegetables or cooked food)
- Cooked food left out uncovered for too long
- Dirty surfaces, chopping boards or utensils visible
- Jewellery or rings worn while cooking
- Tasting with cooking spoon and returning to pot
- Wiping hands on clothing

SAFETY — check each:
- Open flame unattended (which burner, what is cooking)
- Pots boiling over
- Knives at counter edge
- Water near electrical appliances
- Oil overheating and smoking (fire risk)
- Wet slippery floor

MISCONDUCT — flag immediately:
- Person putting food into personal bag or pocket
- Excessive phone use during food handling
- Eating directly from cooking pots
- Giving food to unauthorised person outside
- Deliberately damaging or wasting food

If kitchen empty or everything perfect: THREAT: None""",
        "alert_on": ["medium", "high", "critical"]
    },

    "entrance": {
        "label": "Main Entrance / Door",
        "prompt": """You are a professional entrance security analyst trained to detect threats at entry points.
Examine every detail of this entrance image with the scrutiny of a trained security guard.

Respond in EXACTLY this format:
THREAT: [None / Low / Medium / High / Critical]
PEOPLE: [exact number visible]
ACTIVITY: [3-4 detailed sentences — every person, what they are doing at the entrance, exact interaction with door/bell/lock/frame, behaviour pattern over time]
IDENTITY: [full description of each person — clothing colour and type, height/build estimate, hat/hood/mask, whether face visible or hidden, anything identifying]
BEHAVIOUR: [describe behaviour pattern — how long at door, how many times rang bell, whether nervous or calm, whether checking surroundings repeatedly]
CONCERN: [expert security assessment — exactly what is or is not concerning and why]
ACTION: [precise action — do not open door, call police now, safe to answer, verify identity first]

Analyse in full detail:

ENTRY ATTEMPTS:
- Ringing bell or knocking (how many times, how aggressively)
- Waiting patiently or pacing back and forth
- Touching or testing the door handle or lock mechanism
- Leaning in to examine door frame, hinges, lock or camera
- Trying to peer through letterbox, gaps or side windows
- Any attempt to push, pull or force the door open

SUSPICIOUS SIGNS:
- Deliberately turning away from or covering the camera
- Using phone to photograph entrance, lock or security camera
- Checking if neighbours are watching before acting
- Unusual timing (very late night, early morning)
- Left a package then walked away unusually fast
- Multiple people where some stay back while one approaches

IDENTITY:
- Face clearly visible or hidden under hood/cap/mask/scarf
- Carrying bags, tools, or any equipment
- Wearing gloves (especially suspicious in warm weather)
- Any distinguishing marks or clothing details

If clearly normal expected activity: THREAT: None""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "garage": {
        "label": "Garage / Parking",
        "prompt": """You are an expert vehicle security analyst and garage safety inspector.
Examine every detail of this image like you are investigating a vehicle crime scene.

Respond in EXACTLY this format:
THREAT: [None / Low / Medium / High / Critical]
PEOPLE: [exact number visible]
VEHICLES: [every vehicle visible — type, colour, condition, any damage or tampering signs]
ACTIVITY: [3-4 detailed sentences — exact position of every person relative to vehicles, what each hand is doing, every tool or object visible, precise actions happening]
DAMAGE: [any vehicle or property damage in precise detail — location, type, severity — or None]
CONCERN: [expert assessment of exactly what is suspicious or normal and why]
ACTION: [precise action for owner]

Inspect with expert precision:

VEHICLE CRIME SIGNS:
- Person crouching beside or under vehicle (which side, which part)
- Hands on door handles (which door, testing or casual touch)
- Looking into windows (which window, how long, cupping hands to block reflection)
- Tools near vehicle (screwdrivers, slim jims, angle grinder, jack)
- Person lying fully under vehicle (catalytic converter or exhaust theft)
- Tyre being touched, punctured or deflated (which tyre)
- Fuel cap area being accessed (fuel siphoning)
- Anything being placed on or attached to vehicle underside

GARAGE SAFETY:
- Chemical or fuel spills on floor
- Electrical hazards (exposed wires, sparking)
- Fire hazard (fuel near open flame)
- Heavy items stored unsafely at height

If all normal and clear: THREAT: None""",
        "alert_on": ["low", "medium", "high", "critical"]
    },

    "general": {
        "label": "General Area",
        "prompt": """You are an expert security analyst and safety inspector.
Examine this image with professional forensic attention to detail.

Respond in EXACTLY this format:
THREAT: [None / Low / Medium / High / Critical]
PEOPLE: [exact number visible]
ACTIVITY: [3-4 detailed sentences — describe every person, their exact actions step by step, body language, what they are touching or interacting with, their apparent purpose and intent]
OBJECTS: [every notable object visible — what it is, where it is, who is near it]
CONCERN: [specific expert assessment of what is wrong or unusual, with precise details — or Nothing suspicious]
ACTION: [exact action owner should take right now, or No action needed]

Be extremely observant:

PEOPLE — describe fully:
- What every visible person is doing in precise detail
- Their exact location in the scene
- Body language (tense, relaxed, nervous, purposeful, confused)
- Any objects they are holding or interacting with
- Whether their behaviour seems normal for the location and time

ANOMALIES — look for:
- Objects that are out of place or should not be there
- Signs of previous activity (broken items, moved furniture, spills)
- Anything that looks tampered with or damaged
- Unusual combinations of people, objects or locations

SAFETY HAZARDS:
- Fire, smoke, electrical issues
- Structural damage
- Spills or slip hazards
- Medical emergency signs

If nothing unusual at all: THREAT: None""",
        "alert_on": ["low", "medium", "high", "critical"]
    }
}


# ── Detect camera profile from name ──────────────────
def get_profile(camera_name):
    name = camera_name.lower()
    if any(w in name for w in ["outside", "outdoor", "car", "parking", "street", "garden", "yard", "front", "back"]):
        return CAMERA_PROFILES["outside"]
    elif any(w in name for w in ["kitchen", "cook", "chef", "dining", "food"]):
        return CAMERA_PROFILES["kitchen"]
    elif any(w in name for w in ["entrance", "door", "entry", "gate", "lobby"]):
        return CAMERA_PROFILES["entrance"]
    elif any(w in name for w in ["garage", "workshop", "store", "storage"]):
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
        print(f"[TELEGRAM] Sent ✓")
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


# ── Low light enhancement ─────────────────────────────
def enhance_low_light(frame):
    """CLAHE enhancement for dark/low light images"""
    lab      = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b  = cv2.split(lab)
    clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl       = clahe.apply(l)
    merged   = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return enhanced


# ── Frame capture ─────────────────────────────────────
def capture_frame(source, retries=3):

    # ── Webcam → use OpenCV ──────────────────────────
    if isinstance(source, int):
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 160)
        cap.set(cv2.CAP_PROP_CONTRAST,   50)
        ret, frame = cap.read()
        cap.release()
        if ret and Config.ENHANCE_LOW_LIGHT:
            frame = enhance_low_light(frame)
        return frame if ret else None

    # ── RTSP → use ffmpeg subprocess ─────────────────
    for attempt in range(retries):
        try:
            # Step 1: get stream resolution via ffprobe
            probe = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams', source
            ], capture_output=True, timeout=10)

            streams = json.loads(probe.stdout).get('streams', [])
            video   = next((s for s in streams if s['codec_type'] == 'video'), None)

            if not video:
                print(f"[WARN] No video stream found, retrying...")
                time.sleep(2)
                continue

            w = int(video['width'])
            h = int(video['height'])

            # Step 2: grab single frame as raw bytes
            result = subprocess.run([
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i',              source,
                '-frames:v',       '1',
                '-f',              'image2pipe',
                '-pix_fmt',        'bgr24',
                '-vcodec',         'rawvideo',
                '-loglevel',       'quiet',
                'pipe:1'
            ], capture_output=True, timeout=15)

            expected = w * h * 3
            if result.returncode == 0 and len(result.stdout) == expected:
                frame = np.frombuffer(result.stdout, dtype=np.uint8)
                frame = frame.reshape((h, w, 3)).copy()
                if Config.ENHANCE_LOW_LIGHT:
                    frame = enhance_low_light(frame)
                print(f"[FRAME] {w}x{h} captured ✓")
                return frame
            else:
                print(f"[RETRY {attempt+1}] Unexpected frame size")

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT {attempt+1}] {source[:50]}")
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
    result = {
        "threat": "", "people": "0", "activity": "",
        "concern": "", "action": "", "hygiene": "", "safety": "",
        "identity": "", "vehicles": "", "damage": "",
        "objects": "", "dish": "", "behaviour": ""
    }

    # Try structured key: value parsing
    for line in text.splitlines():
        line = line.strip()
        for key in result:
            if line.lower().startswith(f"{key}:"):
                result[key] = line.split(":", 1)[-1].strip()

    # Fallback: moondream often ignores format instructions
    # Infer threat level from keywords in raw response
    if not result["threat"] or result["threat"].lower() == "none":
        tl = text.lower()
        if any(w in tl for w in ["break","smash","steal","weapon","assault","attack","fire","smoke","forced"]):
            result["threat"] = "High"
        elif any(w in tl for w in ["suspicious","loiter","tamper","crouch","hiding","damage","unknown person"]):
            result["threat"] = "Medium"
        elif any(w in tl for w in ["unusual","unfamiliar","staring","watching","lingering"]):
            result["threat"] = "Low"
        else:
            result["threat"] = "None"

    # If no activity parsed, use full AI response as the activity description
    if not result["activity"].strip():
        result["activity"] = text.strip()[:600]

    # Try to detect people count from natural language
    if result["people"] == "0":
        import re
        mapping = {"one":"1","two":"2","three":"3","four":"4","five":"5"}
        nums = re.findall(r"(one|two|three|four|five|\d+)", text.lower())
        if any(w in text.lower() for w in ["person","people","man","woman","individual","someone"]):
            result["people"] = mapping.get(nums[0], nums[0]) if nums else "1+"

    return result


# ── Format Telegram message ───────────────────────────
def format_alert(camera_name, profile, parsed, timestamp):
    threat = parsed["threat"].upper()
    icons  = {"NONE":"✅", "LOW":"🟢", "MEDIUM":"🟡", "HIGH":"🔴", "CRITICAL":"🆘"}
    icon   = icons.get(threat, "⚠️")

    lines = [
        f"{icon} *{threat} — {profile['label']}*",
        f"📷 *{camera_name}*",
        f"⏰ {timestamp}",
        f"",
        f"👥 *People detected:* {parsed['people']}",
        f"",
        f"📋 *What is happening:*",
        f"{parsed['activity']}",
    ]

    extras = [
        ("dish",      "🍳", "Dish"),
        ("hygiene",   "🧼", "Hygiene"),
        ("safety",    "🔥", "Safety"),
        ("damage",    "🔨", "Damage"),
        ("objects",   "🎒", "Objects"),
        ("identity",  "👤", "Person"),
        ("behaviour", "👀", "Behaviour"),
        ("vehicles",  "🚗", "Vehicles"),
        ("concern",   "⚠️",  "Concern"),
    ]

    skip = {"none", "nothing suspicious", "all good", "good", "safe", "", "no action needed", "unknown"}

    for key, emoji, label in extras:
        val = parsed.get(key, "").strip()
        if val and val.lower() not in skip:
            lines += ["", f"{emoji} *{label}:* {val}"]

    if parsed.get("action", "").strip().lower() not in skip:
        lines += ["", f"✅ *Action needed:* {parsed['action']}"]

    return "\n".join(lines)


# ── Ollama AI analysis ────────────────────────────────
def analyze_with_ollama(frame, camera_name):
    profile = get_profile(camera_name)
    _, buf  = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    img_b64 = base64.b64encode(buf).decode('utf-8')
    try:
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": profile["prompt"], "images": [img_b64]}]
        )
        raw = response['message']['content'].strip()
        print(f"\n[AI ANALYSIS]\n{raw}\n{'─'*40}")
        return raw, profile
    except Exception as e:
        return f"THREAT: None\nACTIVITY: Analysis error: {e}", profile


# ── Save snapshot ─────────────────────────────────────
def save_snapshot(frame, camera_name):
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = camera_name.replace(" ", "_")
    path      = f"snapshots/{safe_name}_{ts}.jpg"
    cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return path


# ── Log alert ─────────────────────────────────────────
def log_alert(camera_name, analysis, snapshot_path, threat):
    entry = {
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera":   camera_name,
        "threat":   threat,
        "analysis": analysis,
        "snapshot": snapshot_path
    }
    alert_log.append(entry)
    with open("logs/alerts.json", "a") as f:
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

                        timestamp = datetime.now().strftime("%I:%M %p, %b %d")

                        if threat in profile["alert_on"]:
                            snapshot = save_snapshot(frame, camera_name)
                            msg      = format_alert(camera_name, profile, parsed, timestamp)
                            send_telegram(msg, image_frame=frame)
                            log_alert(camera_name, raw, snapshot, threat)
                            last_alert_time[camera_name] = now
                            print(f"[ALERT SENT] {threat.upper()} — {camera_name}")

                        elif getattr(Config, "SEND_ALL_FRAMES", False):
                            # Testing mode — send every frame even if no threat
                            msg = (
                                f"✅ *ALL CLEAR — {profile['label']}*"
                                f"📷 *{camera_name}*"
                                f"⏰ {timestamp}"
                                f"📋 *AI Analysis:*"
                                f"{parsed['activity'][:400]}"
                            )
                            send_telegram(msg, image_frame=frame)
                            last_alert_time[camera_name] = now
                            print(f"[TEST FRAME] Sent for {camera_name}")

                        else:
                            print(f"[CLEAR] {camera_name} — threat={threat}")

            prev_frame = frame
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            print(f"[ERROR] {camera_name}: {e}")
            camera_status[camera_name] = "error"
            time.sleep(10)


# ── Entry point ───────────────────────────────────────
def start_surveillance():
    os.makedirs("logs",      exist_ok=True)
    os.makedirs("snapshots", exist_ok=True)

    print("=" * 55)
    print("  AI SURVEILLANCE — DEEP INTELLIGENT ANALYSIS")
    print(f"  Model      : {Config.OLLAMA_MODEL}")
    print(f"  Cameras    : {len(Config.CAMERAS)}")
    print(f"  Low Light  : {'ON' if Config.ENHANCE_LOW_LIGHT else 'OFF'}")
    print(f"  RTSP       : ffmpeg subprocess")
    print("=" * 55)
    for name in Config.CAMERAS:
        print(f"  📷 {name:25s} → {get_profile(name)['label']}")
    print("=" * 55)

    send_telegram(
        f"🏠 *Surveillance ONLINE*\n"
        f"📷 {len(Config.CAMERAS)} camera(s) active\n"
        f"🤖 Model: {Config.OLLAMA_MODEL}\n"
        f"💡 Low light boost: {'ON' if Config.ENHANCE_LOW_LIGHT else 'OFF'}\n"
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
