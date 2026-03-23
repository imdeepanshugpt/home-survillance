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

## ⚠️ Python Version Warning

This project requires **Python 3.11**. Python 3.12+ and 3.14 have compatibility issues with OpenCV and NumPy.

```bash
# Check your Python version first
python3 --version

# If it shows 3.12, 3.13 or 3.14 — install 3.11
brew install python@3.11

# Verify 3.11 is available
/usr/local/bin/python3.11 --version
```

---

## One-Time Setup (macOS)

### Step 1 — Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2 — Install Ollama

```bash
brew install ollama
```

### Step 3 — Pull Moondream Vision Model

```bash
ollama pull moondream
```

> Downloads ~1.7GB. Only suitable model for 8GB RAM Intel Mac.
> RAM guide: 8GB → moondream | 16GB → llava | 32GB → llava:13b

### Step 4 — Install ffmpeg (required for Hikvision RTSP)

```bash
brew install ffmpeg
```

### Step 5 — Create Virtual Environment with Python 3.11

```bash
cd home-survillance

# Use Python 3.11 explicitly
/usr/local/bin/python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Verify correct version inside venv
python3 --version
# Must show: Python 3.11.x
```

### Step 6 — Install Python Packages

```bash
# Downgrade numpy for OpenCV compatibility
pip install "numpy<2"

# Install all required packages
pip install opencv-contrib-python ollama requests

# Verify everything works
python3 -c "
import cv2, numpy as np, ollama, requests
print('✅ Python:', __import__('sys').version[:6])
print('✅ NumPy:', np.__version__)
print('✅ OpenCV:', cv2.__version__)
print('✅ All packages OK')
"
```

### Step 7 — Configure Telegram

```bash
open -e config.py
```

Fill in:

```python
TELEGRAM_BOT_TOKEN = "paste_your_token_here"
TELEGRAM_CHAT_ID   = "paste_your_chat_id_here"
```

### Step 8 — Add Your Cameras

Also in `config.py`:

```python
from urllib.parse import quote

def make_rtsp(ip, password, username="admin", channel=101):
    """Handles special characters like @ in password"""
    encoded = quote(password, safe='')
    return f"rtsp://{username}:{encoded}@{ip}:554/Streaming/Channels/{channel}"

CAMERAS = {
    # Hikvision cameras — use make_rtsp() for passwords with special chars
    "Outside Car": make_rtsp("192.168.1.8",  "your_password"),
    "Porach":      make_rtsp("192.168.1.3",  "your_password"),

    # Webcam for testing (comment out when using real cameras)
    # "Webcam": 0,
}
```

---

## Every Day — How to Run

```bash
# Activate venv and start
cd home-survillance
source venv/bin/activate
python3 main.py
```

Open dashboard: **http://localhost:8080**

> 💡 One-liner to save in your notes:
> `cd home-survillance && source venv/bin/activate && python3 main.py`

> Note: Ollama starts automatically on Mac after install.
> If you see "connection refused" run: `ollama serve &`

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

---

## Threat Level Alerts on Telegram

The AI categorizes every detection — only real threats send alerts:

| Alert       | When triggered                                       |
| ----------- | ---------------------------------------------------- |
| 🆘 CRITICAL | Active break-in, assault, fire, person under vehicle |
| 🔴 HIGH     | Tampering with locks/vehicles, property damage       |
| 🟡 MEDIUM   | Loitering 2+ minutes, suspicious examination         |
| 🟢 LOW      | Slow walk-by staring, unfamiliar parked vehicle      |
| ✅ NONE     | All clear — no Telegram message sent                 |

Camera name drives the AI used:

| Camera Name Contains              | AI Profile          |
| --------------------------------- | ------------------- |
| outside, car, front, yard, garden | 🏠 Outdoor Security |
| kitchen, cook, chef, food         | 🍳 Kitchen Monitor  |
| door, entrance, gate, lobby       | 🚪 Entry Security   |
| garage, workshop, storage         | 🚗 Garage Monitor   |
| anything else                     | 🔍 General Security |

Example Telegram alert:

```
🔴 HIGH — Outdoor / Property
📷 Outside Car
⏰ 1:05 AM, Mar 23

👥 People detected: 1

📋 What is happening:
A person in dark clothing is crouching beside the rear wheel
of the parked white car. Their right hand appears to be
touching the tyre valve area.

⚠️ Concern: Possible tyre deflation or catalytic converter theft
✅ Action needed: Check immediately, consider calling police
```

---

## Find Hikvision Camera IPs

```bash
source venv/bin/activate

python3 -c "
import socket, requests, concurrent.futures
from requests.auth import HTTPDigestAuth

NETWORK  = '192.168.1.'
PASSWORD = 'your_password'
TIMEOUT  = 2

def check_hikvision(ip):
    for port in [80, 554]:
        try:
            s = socket.socket()
            s.settimeout(TIMEOUT)
            if s.connect_ex((ip, port)) == 0:
                s.close()
                try:
                    r = requests.get(
                        f'http://{ip}/ISAPI/System/deviceInfo',
                        auth=HTTPDigestAuth('admin', PASSWORD),
                        timeout=TIMEOUT
                    )
                    if r.status_code == 200:
                        import xml.etree.ElementTree as ET
                        root  = ET.fromstring(r.text)
                        ns    = {'ns': 'http://www.hikvision.com/ver20/XMLSchema'}
                        name  = root.findtext('ns:deviceName', namespaces=ns) or 'Hikvision Camera'
                        model = root.findtext('ns:model',      namespaces=ns) or 'Unknown'
                        print(f'  ✅ {ip}  →  {name}  ({model})')
                        print(f'     Main : rtsp://admin:{PASSWORD}@{ip}:554/Streaming/Channels/101')
                        print(f'     Sub  : rtsp://admin:{PASSWORD}@{ip}:554/Streaming/Channels/102')
                        print()
                        return
                except: pass
                print(f'  📷 {ip}  →  Device on port {port}')
                return
            s.close()
        except: pass

print()
print('Scanning 192.168.1.0/24 ...')
print('─' * 55)
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    ex.map(check_hikvision, [f'{NETWORK}{i}' for i in range(1, 255)])
print('─' * 55)
print('Done.')
"
```

> Change `NETWORK` and `PASSWORD` to match your setup.
> Find your subnet: `ipconfig getifaddr en0`

---

## Hikvision Camera Setup

### Enable RTSP on Camera

```
1. Open browser → http://192.168.1.XX
2. Login (check sticker on camera for default password)
3. Configuration → Network → Advanced → Integration Protocol
4. Enable RTSP → Authentication: Basic → Save
```

### Test RTSP Stream

```bash
# Test with VLC (most reliable)
vlc "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101"

# Test with ffmpeg (what our code uses)
ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101" \
  -frames:v 1 test.jpg -y && echo "✅ Connected!" || echo "❌ Failed"

# Check port is open
nc -zv 192.168.1.XX 554
```

### RTSP Channel Reference

```
/Streaming/Channels/101  → Camera 1, HD main stream
/Streaming/Channels/102  → Camera 1, sub stream (faster, use outdoors)
/Streaming/Channels/201  → Camera 2, HD main stream
/Streaming/Channels/202  → Camera 2, sub stream
```

---

## Test Image Quality on Telegram

Send a test snapshot to Telegram without waiting for motion:

```bash
source venv/bin/activate

python3 -c "
import cv2, subprocess, json, numpy as np, requests
from urllib.parse import quote
from config import Config

def grab_frame(ip, password):
    encoded = quote(password, safe='')
    source  = f'rtsp://admin:{encoded}@{ip}:554/Streaming/Channels/101'
    probe   = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_streams',source], capture_output=True, timeout=10)
    streams = json.loads(probe.stdout).get('streams',[])
    video   = next((s for s in streams if s['codec_type']=='video'), None)
    w, h    = int(video['width']), int(video['height'])
    result  = subprocess.run(['ffmpeg','-rtsp_transport','tcp','-i',source,'-frames:v','1','-f','image2pipe','-pix_fmt','bgr24','-vcodec','rawvideo','-loglevel','quiet','pipe:1'], capture_output=True, timeout=15)
    return np.frombuffer(result.stdout, dtype=np.uint8).reshape((h,w,3)).copy()

def send(frame, caption):
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    requests.post(
        f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendPhoto',
        data={'chat_id': Config.TELEGRAM_CHAT_ID, 'caption': caption},
        files={'photo': ('test.jpg', buf.tobytes(), 'image/jpeg')}
    )
    print(f'✅ Sent: {caption}')

frame = grab_frame('192.168.1.8', 'password')
print(f'Frame: {frame.shape[1]}x{frame.shape[0]}')

# Send raw image
send(frame, '📷 RAW — Outside Car')

# Send enhanced image
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
enhanced = cv2.cvtColor(cv2.merge((clahe.apply(l), a, b)), cv2.COLOR_LAB2BGR)
send(enhanced, '💡 ENHANCED — Outside Car (low light boost)')

print('Check Telegram — 2 images sent for quality comparison!')
"
```

---

## Motion Sensitivity Tuning

```bash
source venv/bin/activate

# For webcam
python3 -c "
import cv2, time, subprocess, json, numpy as np
from urllib.parse import quote

# Change to RTSP URL for Hikvision
source = 0

cap  = cv2.VideoCapture(source) if isinstance(source, int) else None
prev = None
print('Watching scores — note value when still vs when person moves')
while True:
    if isinstance(source, int):
        ret, frame = cap.read()
    else:
        from urllib.parse import quote as q
        # use ffprobe + ffmpeg for RTSP
        break
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    if prev is not None:
        diff = cv2.absdiff(prev, blur)
        _, th = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        print(f'Score: {cv2.countNonZero(th)}')
    prev = blur
    time.sleep(0.5)
"
```

Then set in `config.py`:

```python
MOTION_THRESHOLD = 3000   # Just above your idle score
COOLDOWN_SECONDS = 30     # Seconds between repeat alerts
CHECK_INTERVAL   = 2      # Seconds between frame checks
```

| Setting            | Lower =                   | Higher =           |
| ------------------ | ------------------------- | ------------------ |
| `MOTION_THRESHOLD` | More sensitive            | Fewer false alarms |
| `COOLDOWN_SECONDS` | More frequent alerts      | Less spam          |
| `CHECK_INTERVAL`   | More real-time (more CPU) | Lighter on CPU     |

---

## File Structure

```
home-survillance/
├── main.py           ← Run this every time to start
├── surveillance.py   ← Motion detection + AI analysis engine
├── dashboard.py      ← Web UI at http://localhost:8080
├── config.py         ← All your settings (edit this)
├── setup.sh          ← Linux/Raspberry Pi setup script
├── venv/             ← Python 3.11 virtual environment
├── logs/
│   └── alerts.json   ← Full alert history
└── snapshots/        ← Saved images of every motion event
```

---

## Moving to Raspberry Pi Later

**Recommended: Raspberry Pi 5 (8GB)** — runs 24/7 at ~₹400/month electricity.

```bash
# Install Ollama on Pi
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull moondream

# Install ffmpeg
sudo apt install ffmpeg -y

# Install packages
pip install opencv-python-headless ollama requests numpy

# Remote access from anywhere — free via Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# SSH into Pi from anywhere:
ssh pi@100.x.x.x
```

---

## Troubleshooting

**Wrong Python version (3.12/3.13/3.14)**

```bash
brew install python@3.11
rm -rf venv
/usr/local/bin/python3.11 -m venv venv
source venv/bin/activate
pip install "numpy<2" opencv-contrib-python ollama requests
```

**NumPy version conflict**

```bash
pip install "numpy<2" --force-reinstall
# Ignore the opencv compatibility warning — it still works
```

**OpenCV has no FFmpeg support**
Not needed — our code uses ffmpeg subprocess directly.
Make sure ffmpeg is installed: `brew install ffmpeg`

**`ollama serve` → address already in use**
Ollama already running in background. Skip this, just run `python3 main.py`.

**Port 8080 in use**
Change in `main.py`: `start(port=9090)` → open `http://localhost:9090`

**Black image / webcam not working**

```bash
pip uninstall opencv-python-headless -y
pip install opencv-contrib-python
```

Then: System Settings → Privacy & Security → Camera → Enable Terminal

**Hikvision RTSP not connecting**

```bash
# Check port is open
nc -zv 192.168.1.XX 554

# Test with ffmpeg
ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101" \
  -frames:v 1 test.jpg -y && echo "✅" || echo "❌"
```

If ffmpeg works but code doesn't — check password encoding in config.py uses `make_rtsp()`.

**Password has @ or special characters**
Always use `make_rtsp()` in config.py — it handles encoding automatically:

```python
"Outside Car": make_rtsp("192.168.1.8", "password"),
```

**No Telegram alerts arriving**

- Check token and chat ID in config.py
- Make sure you tapped START on your bot in Telegram
- Lower `MOTION_THRESHOLD` in config
- Set `SEND_ALL_FRAMES = True` in config to test without needing motion

**AI analysis slow (20-40 seconds)**
Normal on Intel Mac — no GPU. Moondream is the lightest available model.
Improves significantly on Raspberry Pi 5.
