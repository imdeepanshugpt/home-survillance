# 🏠 AI Home Surveillance System

**100% Free · Runs Locally · Telegram Alerts · Hikvision + Webcam Ready**

---

## Stack

| Component | Tool                        | Cost |
| --------- | --------------------------- | ---- |
| AI Vision | Ollama + Moondream          | Free |
| Alerts    | Telegram Bot                | Free |
| Camera    | Hikvision RTSP / Webcam     | —    |
| Dashboard | Built-in web UI (port 8080) | Free |

---

## One-Time Setup (macOS)

### Step 1 — Install Ollama

```bash
brew install ollama
```

> Don't have Homebrew? Install it first:
> `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Step 2 — Pull Moondream Vision Model

```bash
ollama pull moondream
```

> Downloads ~1.7GB. Recommended for 8GB RAM Intel Macs.

### Step 3 — Create Virtual Environment

```bash
cd home-survillance
python3 -m venv venv
source venv/bin/activate
```

> You'll see `(venv)` at the start of your terminal line when active.

### Step 4 — Install Python Packages

```bash
pip install opencv-python ollama requests
```

> Use `opencv-python` (NOT headless) on Mac for webcam support.

### Step 5 — Configure Telegram

```bash
open -e config.py
```

Fill in:

```python
TELEGRAM_BOT_TOKEN = "paste_your_token_here"
TELEGRAM_CHAT_ID   = "paste_your_chat_id_here"
```

### Step 6 — Add Your Cameras

Also in `config.py`:

```python
# Webcam for testing:
CAMERAS = {
    "Webcam": 0,
}

# Hikvision cameras:
CAMERAS = {
    "Outside Car":  "rtsp://admin:PASSWORD@192.168.1.64:554/Streaming/Channels/102",
    "Front Door":   "rtsp://admin:PASSWORD@192.168.1.65:554/Streaming/Channels/101",
}
```

---

## Every Day — How to Run

```bash
# Step 1 — Activate virtual environment
cd home-survillance
source venv/bin/activate

# Step 2 — Start surveillance
python3 main.py
```

Open dashboard: **http://localhost:8080**

> 💡 One-liner to save in your notes:
> `cd home-survillance && source venv/bin/activate && python3 main.py`

> Note: Ollama starts automatically in background on Mac after install.
> If you ever see "connection refused", run: `ollama serve &`

---

## Telegram Bot Setup (5 mins)

```
1. Open Telegram → search @BotFather
2. Send: /newbot
3. Give it a name  →  e.g. Home Surveillance
4. Give a username →  e.g. myhome_surv_bot  (must end in 'bot')
5. Copy the TOKEN  →  looks like 7123456789:AAFxxx...

6. Open Telegram → search @userinfobot
7. Send any message → it replies with your Chat ID (a number)
8. Copy that number
```

Paste both into `config.py` as shown in Step 5 above.

---

## Threat Level Alerts on Telegram

The AI categorizes every detection — only real threats send alerts:

| Alert            | When triggered                                |
| ---------------- | --------------------------------------------- |
| 🔴 HIGH THREAT   | Someone touching / tampering with car or door |
| 🟡 MEDIUM THREAT | Person loitering or pacing near property      |
| 🟢 LOW THREAT    | Slow or suspicious movement nearby            |
| ✅ NONE          | All clear — no Telegram message sent          |

Example alert you'll receive:

```
🔴 HIGH THREAT
📷 Outside Car
⏰ 1:05 AM, Mar 20

THREAT: High
ACTIVITY: A person is crouching next to the parked car
ACTION: Check immediately, possible break-in attempt
```

---

## Hikvision Camera Setup

### Find Camera IPs

```bash
nmap -sn 192.168.1.0/24
# Or check your router's connected device list
# Or use Hikvision SADP Tool (free Mac download)
```

### Enable RTSP on Camera

```
1. Open browser → http://192.168.1.XX
2. Login (check sticker on camera for default password)
3. Configuration → Network → Advanced → Integration Protocol
4. Enable RTSP → Save
```

### Test RTSP Stream First

```bash
# Using VLC
vlc rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101

# Using Python
source venv/bin/activate
python3 -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101')
ret, frame = cap.read()
print('✅ Connected!' if ret else '❌ Failed - check IP/password')
cap.release()
"
```

### RTSP Channel Reference

```
/Streaming/Channels/101  → Camera 1, HD (main stream)
/Streaming/Channels/102  → Camera 1, faster low-res (use for outdoors)
/Streaming/Channels/201  → Camera 2, HD
/Streaming/Channels/202  → Camera 2, faster low-res
```

---

## Motion Sensitivity Tuning

Run this to find your ideal threshold value:

```bash
source venv/bin/activate
python3 -c "
import cv2, time
cap = cv2.VideoCapture(0)  # Replace 0 with RTSP URL for Hikvision
prev = None
print('Point at your area. Note score when still vs when someone moves.')
while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    if prev is not None:
        import cv2 as c
        diff = c.absdiff(prev, blur)
        _, th = c.threshold(diff, 20, 255, c.THRESH_BINARY)
        print(f'Score: {c.countNonZero(th)}')
    prev = blur
    time.sleep(0.5)
"
```

Then set in `config.py`:

```python
MOTION_THRESHOLD = 3000   # Set just above your idle/wind score
COOLDOWN_SECONDS = 20     # Seconds between repeat alerts per camera
CHECK_INTERVAL   = 1      # Seconds between frame checks (1 = real-time)
```

| Setting            | Lower =                        | Higher =              |
| ------------------ | ------------------------------ | --------------------- |
| `MOTION_THRESHOLD` | More sensitive, more AI calls  | Fewer false positives |
| `COOLDOWN_SECONDS` | More frequent alerts           | Less spam             |
| `CHECK_INTERVAL`   | More real-time (uses more CPU) | Lighter on CPU        |

---

## File Structure

```
home-survillance/
├── main.py           ← Run this every time to start
├── surveillance.py   ← Motion detection + AI analysis engine
├── dashboard.py      ← Web UI at http://localhost:8080
├── config.py         ← All your settings (edit this)
├── setup.sh          ← Linux/Raspberry Pi setup script
├── venv/             ← Python virtual environment (your install)
├── logs/
│   └── alerts.json   ← Full alert history (JSON)
└── snapshots/        ← Saved images of every motion event
```

---

## Moving to Raspberry Pi Later

**Recommended: Raspberry Pi 5 (8GB)** — runs 24/7 at ~₹400/month electricity.

```bash
# Install Ollama on Pi
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull moondream

# Install packages
pip install opencv-python-headless ollama requests

# Remote access from anywhere — free via Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# SSH into Pi from anywhere in the world:
ssh pi@100.x.x.x   # Tailscale IP shown after setup
```

---

## Troubleshooting

**`ollama serve` → address already in use**
Ollama is already running in background — this is fine. Skip `ollama serve` and just run `python3 main.py`.

**Port 8080 already in use**
Change in `main.py`: `start(port=9090)` then open `http://localhost:9090`

**Black image or webcam not working**

- Reinstall: `pip uninstall opencv-python-headless && pip install opencv-python`
- Grant camera permission: System Settings → Privacy & Security → Camera → Enable Terminal

**Hikvision not connecting**

- Test stream in VLC first
- Enable RTSP in camera web interface
- Find correct IP: `nmap -sn 192.168.1.0/24`

**No Telegram alerts arriving**

- Double check token and chat ID in `config.py`
- Make sure you tapped START on your bot in Telegram
- Lower `MOTION_THRESHOLD` in config if motion not triggering

**AI analysis is slow (20-40 seconds)**
Normal on Intel Mac — no GPU acceleration. Moondream is the lightest model available. Alerts will still arrive, just with a short delay. This improves significantly on Raspberry Pi 5.
