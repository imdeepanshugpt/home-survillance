# 🏠 AI Home Surveillance System

**100% Free · Runs Locally · Telegram Alerts · Hik vision + Webcam Ready**

---

## Stack

| Component | Tool                        | Cost |
| --------- | --------------------------- | ---- |
| AI Vision | Ollama + LLaVA / Moondream  | Free |
| Alerts    | Telegram Bot                | Free |
| Camera    | Hikvision RTSP / Webcam     | —    |
| Dashboard | Built-in web UI (port 8080) | Free |
| Env Mgmt  | Conda (miniconda)           | Free |

> ✅ We use **conda** for environment management — no venv needed.
> Conda handles OpenCV + NumPy + ffmpeg compatibility automatically.

---

## Project Structure

```
home-survillance/
├── main.py                 ← single entry point
├── Dockerfile              ← miniconda3 base image
├── docker-compose.yml      ← surveillance + ollama services
├── environment.yml         ← conda dependencies
├── .env.example            ← copy to .env and fill in values
├── .gitignore
├── .dockerignore
│
├── config/
│   ├── __init__.py
│   ├── config.py           ← your settings (gitignored)
│   └── config.example.py  ← safe template to commit
│
├── src/
│   ├── __init__.py
│   ├── surveillance.py     ← core AI + motion engine
│   └── dashboard.py        ← web UI
│
├── logs/
│   └── alerts.json         ← alert history
└── snapshots/              ← motion event images
```

---

## One-Time Setup (macOS / Linux)

### Step 1 — Install Miniconda

```bash
# macOS
brew install --cask miniconda

# Linux
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Verify
conda --version
```

### Step 2 — Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 3 — Pull AI Vision Model

```bash
ollama pull llava
```

> Model guide by RAM:
> 8GB → `moondream` (1.7GB) | 16GB → `llava` (4.7GB) | 32GB → `llava:13b` (8GB)

### Step 4 — Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg -y
```

### Step 5 — Create Conda Environment

```bash
cd home-survillance
conda env create -f environment.yml
conda activate surveillance
```

> You'll see `(surveillance)` at the start of your terminal.
> This replaces venv — conda IS the environment manager.

### Step 6 — Configure

```bash
# Copy example config
cp config/config.example.py config/config.py

# Edit with your values
open -e config/config.py       # macOS
nano config/config.py          # Linux
```

Fill in:

```python
TELEGRAM_BOT_TOKEN = "your_token"
TELEGRAM_CHAT_ID   = "your_chat_id"

CAMERAS = {
    "Outside Car": make_rtsp("192.168.1.8", "your_password"),
    "Kitchen":     make_rtsp("192.168.1.9", "your_password"),
}
```

---

## Every Day — How to Run

```bash
conda activate surveillance
python3 main.py
```

Open dashboard: **http://localhost:8080**

> 💡 One-liner:
> `conda activate surveillance && python3 main.py`

> Ollama starts automatically on Mac after install.
> If you see "connection refused": `ollama serve &`

---

## Run with Docker (Windows / Mac / Linux)

```bash
# 1 — Setup
cp .env.example .env
# Edit .env with your values

# 2 — Start everything
docker-compose up -d

# 3 — Watch logs
docker-compose logs -f surveillance

# 4 — Stop
docker-compose down
```

Docker uses **miniconda3** base image — same conda environment, fully reproducible.

---

## Telegram Bot Setup (5 mins)

```
1. Open Telegram → search @BotFather
2. Send: /newbot
3. Name it e.g. Home Surveillance
4. Username e.g. myhome_surv_bot (must end in 'bot')
5. Copy the TOKEN

6. Search @userinfobot on Telegram
7. Send any message → copy your Chat ID
```

---

## Camera AI Profiles

Camera name determines which AI brain is used:

| Camera Name Contains            | AI Profile          |
| ------------------------------- | ------------------- |
| outside, car, front, gate, yard | 🏠 Outdoor Security |
| kitchen, cook, chef, food       | 🍳 Kitchen Monitor  |
| door, entrance, gate, lobby     | 🚪 Entry Security   |
| garage, workshop, storage       | 🚗 Garage Monitor   |
| anything else                   | 🔍 General Security |

## Threat Levels

| Alert       | Meaning                            |
| ----------- | ---------------------------------- |
| 🆘 CRITICAL | Active break-in, fire, emergency   |
| 🔴 HIGH     | Property damage, vehicle tampering |
| 🟡 MEDIUM   | Suspicious behaviour, loitering    |
| 🟢 LOW      | Slightly unusual activity          |
| ✅ NONE     | All clear — no alert sent          |

---

## Find Hikvision Camera IPs

```bash
conda activate surveillance

python3 -c "
import socket, requests, concurrent.futures
from requests.auth import HTTPDigestAuth

NETWORK  = '192.168.1.'
PASSWORD = 'your_password'
TIMEOUT  = 2

def check(ip):
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
                        model = root.findtext('ns:model', namespaces=ns) or 'Unknown'
                        print(f'  ✅ {ip}  →  {name}  ({model})')
                        print(f'     rtsp://admin:{PASSWORD}@{ip}:554/Streaming/Channels/101')
                        return
                except: pass
                print(f'  📷 {ip}  →  Device on port {port}')
                return
            s.close()
        except: pass

print('Scanning 192.168.1.0/24 ...')
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    ex.map(check, [f'{NETWORK}{i}' for i in range(1, 255)])
print('Done.')
"
```

---

## Hikvision RTSP Setup

### Enable RTSP on Camera

```
Browser → http://192.168.1.XX
Login → Configuration → Network → Advanced → Integration Protocol
Enable RTSP → Authentication: Basic → Save
```

### Test RTSP

```bash
# VLC test
vlc "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101"

# ffmpeg test (what our code uses)
ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101" \
  -frames:v 1 test.jpg -y && echo "✅ Connected!" || echo "❌ Failed"

# Port check
nc -zv 192.168.1.XX 554
```

### Channel Reference

```
/Streaming/Channels/101  → Camera 1 HD
/Streaming/Channels/102  → Camera 1 sub-stream (faster)
/Streaming/Channels/201  → Camera 2 HD
/Streaming/Channels/202  → Camera 2 sub-stream
```

---

## Test Image Quality

Send a snapshot to Telegram immediately (no motion needed):

```bash
conda activate surveillance

python3 -c "
import cv2, subprocess, json, numpy as np, requests
from urllib.parse import quote
import sys
sys.path.insert(0, '.')
from config import Config

def grab(ip, pwd):
    enc = quote(pwd, safe='')
    src = f'rtsp://admin:{enc}@{ip}:554/Streaming/Channels/101'
    p   = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_streams',src], capture_output=True, timeout=10)
    v   = next(s for s in json.loads(p.stdout)['streams'] if s['codec_type']=='video')
    w,h = int(v['width']), int(v['height'])
    r   = subprocess.run(['ffmpeg','-rtsp_transport','tcp','-i',src,'-frames:v','1','-f','image2pipe','-pix_fmt','bgr24','-vcodec','rawvideo','-loglevel','quiet','pipe:1'], capture_output=True, timeout=15)
    return np.frombuffer(r.stdout, dtype=np.uint8).reshape((h,w,3)).copy()

def send(frame, caption):
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    requests.post(
        f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendPhoto',
        data={'chat_id': Config.TELEGRAM_CHAT_ID, 'caption': caption},
        files={'photo': ('snap.jpg', buf.tobytes(), 'image/jpeg')}
    )
    print(f'Sent: {caption}')

frame = grab('192.168.1.8', 'cctv@12345')
send(frame, '📷 RAW image')

lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
l,a,b = cv2.split(lab)
cl = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(l)
enhanced = cv2.cvtColor(cv2.merge((cl,a,b)), cv2.COLOR_LAB2BGR)
send(enhanced, '💡 ENHANCED image')
print('Check Telegram — 2 images sent!')
"
```

---

## Motion Sensitivity Tuning

```bash
conda activate surveillance

python3 -c "
import cv2, time
cap  = cv2.VideoCapture(0)   # replace 0 with RTSP URL for Hikvision
prev = None
print('Watch scores — note value when still vs when person moves')
while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5,5),0)
    if prev is not None:
        diff = cv2.absdiff(prev, blur)
        _,th = cv2.threshold(diff,20,255,cv2.THRESH_BINARY)
        print(f'Score: {cv2.countNonZero(th)}')
    prev = blur
    time.sleep(0.5)
"
```

Set in `config/config.py`:

```python
MOTION_THRESHOLD = 3000   # just above your idle score
COOLDOWN_SECONDS = 30     # seconds between repeat alerts
CHECK_INTERVAL   = 2      # seconds between frame checks
```

---

## Moving to Raspberry Pi

**Recommended: Raspberry Pi 5 (8GB)** — runs 24/7 at ~₹400/month.

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llava

# Install Miniconda on Pi
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh

# Setup project
conda env create -f environment.yml
conda activate surveillance
python3 main.py

# Remote access from anywhere — free
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# SSH: ssh pi@100.x.x.x
```

---

## Troubleshooting

**`conda: command not found`**

```bash
# Restart terminal or run:
source ~/miniconda3/etc/profile.d/conda.sh
```

**Conda env already exists**

```bash
conda env remove -n surveillance
conda env create -f environment.yml
```

**Ollama not running**

```bash
ollama serve &
# or on Mac it auto-starts — check: curl http://localhost:11434/api/tags
```

**Port 8080 in use (macOS AirPlay)**

```bash
# Option 1 — disable AirPlay receiver:
# System Settings → General → AirDrop & Handoff → AirPlay Receiver → OFF

# Option 2 — change port in config/config.py:
DASHBOARD_PORT = 9090
```

**Hikvision RTSP not connecting**

```bash
nc -zv 192.168.1.XX 554          # check port open
ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:PASS@IP:554/Streaming/Channels/101" \
  -frames:v 1 test.jpg -y        # test frame grab
```

**Password has @ or special characters**

```python
# Always use make_rtsp() in config.py — handles encoding:
"Outside Car": make_rtsp("192.168.1.8", "cctv@12345"),
```

**AI analysis returns garbage (numbers/symbols)**
Switch from moondream to llava:

```python
OLLAMA_MODEL = "llava"   # in config/config.py or .env
```
