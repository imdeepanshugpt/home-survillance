#!/bin/bash
# ═══════════════════════════════════════════════════
#  AI Surveillance Setup Script
#  Run once to install everything
# ═══════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   AI Surveillance Setup              ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Install Ollama ─────────────────────────────
echo "▶ Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✓ Ollama already installed"
else
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "  ✓ Ollama installed"
fi

# ── 2. Pull vision model ──────────────────────────
echo ""
echo "▶ Pulling AI vision model..."
echo "  Choose based on your RAM:"
echo "  [1] moondream  - 1.7GB (8GB  RAM)"
echo "  [2] llava      - 4.7GB (16GB RAM)"
echo "  [3] llava:13b  - 8GB   (32GB RAM)"
echo ""
read -p "  Enter choice [1/2/3] (default: 1): " model_choice

case "$model_choice" in
    2) MODEL="llava"      ;;
    3) MODEL="llava:13b"  ;;
    *) MODEL="moondream"  ;;
esac

echo "  Pulling $MODEL (this may take a few minutes)..."
ollama pull $MODEL
echo "  ✓ Model ready: $MODEL"

# Update config with chosen model
sed -i "s/OLLAMA_MODEL = .*/OLLAMA_MODEL = \"$MODEL\"/" config.py

# ── 3. Python dependencies ────────────────────────
echo ""
echo "▶ Installing Python packages..."
pip install opencv-python-headless ollama requests --break-system-packages 2>/dev/null \
  || pip install opencv-python-headless ollama requests

echo "  ✓ Python packages installed"

# ── 4. Create folders ─────────────────────────────
mkdir -p logs snapshots
echo "  ✓ Created logs/ and snapshots/ folders"

# ── 5. Test Ollama ────────────────────────────────
echo ""
echo "▶ Testing Ollama..."
ollama_response=$(ollama run $MODEL "Say OK" 2>/dev/null | head -1)
echo "  ✓ Ollama test: $ollama_response"

# ── 6. Telegram setup guide ───────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Telegram Setup (2 mins)            ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  1. Open Telegram → Search @BotFather"
echo "  2. Send: /newbot"
echo "  3. Follow prompts → Copy the TOKEN"
echo ""
echo "  4. Open Telegram → Search @userinfobot"
echo "  5. Send any message → Copy your Chat ID"
echo ""
read -p "  Enter your Bot TOKEN: " bot_token
read -p "  Enter your Chat ID:   " chat_id

if [ ! -z "$bot_token" ] && [ ! -z "$chat_id" ]; then
    sed -i "s/TELEGRAM_BOT_TOKEN = .*/TELEGRAM_BOT_TOKEN = \"$bot_token\"/" config.py
    sed -i "s/TELEGRAM_CHAT_ID   = .*/TELEGRAM_CHAT_ID   = \"$chat_id\"/" config.py
    echo "  ✓ Telegram config saved"

    # Test Telegram
    echo ""
    echo "▶ Sending test message to Telegram..."
    curl -s -X POST "https://api.telegram.org/bot$bot_token/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"$chat_id\", \"text\": \"✅ Surveillance setup complete! System is ready.\"}" \
        > /dev/null
    echo "  ✓ Check Telegram for test message!"
fi

# ── 7. Camera setup ───────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Camera Setup                       ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  For Hikvision cameras, find their IPs:"
echo "  Option 1: nmap -sn 192.168.1.0/24"
echo "  Option 2: Check your router's device list"
echo "  Option 3: Use Hikvision SADP Tool"
echo ""
echo "  RTSP URL format:"
echo "  rtsp://admin:PASSWORD@192.168.1.XX:554/Streaming/Channels/101"
echo ""
echo "  Edit config.py to add your camera URLs"
echo "  (Webcam '0' is enabled by default for testing)"
echo ""

# ── Done ──────────────────────────────────────────
echo "╔══════════════════════════════════════╗"
echo "║   Setup Complete! ✓                  ║"
echo "╠══════════════════════════════════════╣"
echo "║                                      ║"
echo "║  To start surveillance:              ║"
echo "║    python surveillance.py            ║"
echo "║                                      ║"
echo "║  To view dashboard:                  ║"
echo "║    python dashboard.py               ║"
echo "║    Open: http://localhost:5000        ║"
echo "║                                      ║"
echo "╚══════════════════════════════════════╝"
echo ""
