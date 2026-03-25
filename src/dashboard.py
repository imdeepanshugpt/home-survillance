"""
Web Dashboard — View camera status and alert history
Run: python dashboard.py
Open: http://localhost:5000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os
from datetime import datetime

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Surveillance Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;800&display=swap');

  :root {
    --bg: #050a0f;
    --panel: #0a1520;
    --border: #0f3460;
    --accent: #00d4ff;
    --accent2: #ff4d6d;
    --green: #00ff9d;
    --text: #c8d8e8;
    --dim: #4a6080;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    min-height: 100vh;
    background-image:
      radial-gradient(ellipse at 20% 50%, rgba(0,212,255,0.03) 0%, transparent 60%),
      radial-gradient(ellipse at 80% 20%, rgba(255,77,109,0.03) 0%, transparent 60%),
      linear-gradient(180deg, #050a0f 0%, #080d15 100%);
  }

  /* ── Header ── */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 40px;
    border-bottom: 1px solid var(--border);
    background: rgba(10,21,32,0.8);
    backdrop-filter: blur(10px);
    position: sticky; top: 0; z-index: 100;
  }

  .logo {
    display: flex; align-items: center; gap: 12px;
  }

  .logo-icon {
    width: 36px; height: 36px;
    border: 2px solid var(--accent);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    position: relative;
    animation: pulse-ring 2s infinite;
  }

  .logo-icon::after {
    content: '';
    width: 10px; height: 10px;
    background: var(--accent);
    border-radius: 50%;
    display: block;
  }

  @keyframes pulse-ring {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0,212,255,0.4); }
    50%       { box-shadow: 0 0 0 8px rgba(0,212,255,0); }
  }

  .logo h1 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 18px;
    color: var(--accent);
    letter-spacing: 3px;
  }

  .status-bar {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px;
    color: var(--green);
  }

  .status-dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    animation: blink 1.5s infinite;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.2; }
  }

  .time-display {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    color: var(--dim);
  }

  /* ── Layout ── */
  main {
    padding: 30px 40px;
    max-width: 1400px;
    margin: 0 auto;
  }

  /* ── Stats row ── */
  .stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 30px;
  }

  .stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    position: relative;
    overflow: hidden;
  }

  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }

  .stat-label {
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--dim);
    text-transform: uppercase;
    margin-bottom: 10px;
  }

  .stat-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 32px;
    color: var(--accent);
    font-weight: bold;
  }

  .stat-sub {
    font-size: 12px;
    color: var(--dim);
    margin-top: 4px;
  }

  /* ── Grid ── */
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    background: rgba(0,212,255,0.03);
  }

  .panel-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    letter-spacing: 2px;
    color: var(--accent);
    text-transform: uppercase;
  }

  .badge {
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 4px;
    padding: 3px 10px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: var(--accent);
  }

  /* ── Camera cards ── */
  .cameras {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .cam-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border: 1px solid rgba(15,52,96,0.6);
    border-radius: 8px;
    background: rgba(0,212,255,0.02);
    transition: border-color 0.3s;
  }

  .cam-card:hover { border-color: var(--accent); }

  .cam-info { display: flex; align-items: center; gap: 12px; }

  .cam-icon {
    width: 38px; height: 38px;
    border-radius: 8px;
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }

  .cam-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--text);
  }

  .cam-url {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    color: var(--dim);
    margin-top: 2px;
  }

  .cam-status {
    display: flex; align-items: center; gap: 6px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
  }

  .cam-status.online  { background: rgba(0,255,157,0.1); color: var(--green);  border: 1px solid rgba(0,255,157,0.3); }
  .cam-status.offline { background: rgba(255,77,109,0.1); color: var(--accent2); border: 1px solid rgba(255,77,109,0.3); }
  .cam-status.connecting { background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid rgba(0,212,255,0.3); }

  .status-led {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: currentColor;
  }

  .online .status-led  { animation: blink 1.5s infinite; }

  /* ── Alert log ── */
  .alerts {
    padding: 0;
    max-height: 420px;
    overflow-y: auto;
  }

  .alerts::-webkit-scrollbar { width: 4px; }
  .alerts::-webkit-scrollbar-track { background: transparent; }
  .alerts::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .alert-item {
    display: flex;
    gap: 14px;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(15,52,96,0.4);
    transition: background 0.2s;
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0); }
  }

  .alert-item:hover { background: rgba(0,212,255,0.03); }

  .alert-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent2);
    margin-top: 5px;
    flex-shrink: 0;
    box-shadow: 0 0 6px var(--accent2);
  }

  .alert-content { flex: 1; }

  .alert-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 5px;
  }

  .alert-cam {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
    font-family: 'Share Tech Mono', monospace;
  }

  .alert-time {
    font-size: 11px;
    color: var(--dim);
    font-family: 'Share Tech Mono', monospace;
  }

  .alert-text {
    font-size: 13px;
    color: var(--text);
    line-height: 1.5;
  }

  /* ── Model info ── */
  .model-panel {
    padding: 20px;
  }

  .model-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(15,52,96,0.4);
  }

  .model-row:last-child { border-bottom: none; }

  .model-key {
    font-size: 12px;
    color: var(--dim);
    letter-spacing: 1px;
  }

  .model-val {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    color: var(--accent);
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: var(--dim);
    font-size: 13px;
  }

  .empty-icon { font-size: 32px; margin-bottom: 10px; }

  /* ── Refresh btn ── */
  .refresh-btn {
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.3);
    color: var(--accent);
    padding: 6px 14px;
    border-radius: 6px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    cursor: pointer;
    letter-spacing: 1px;
    transition: all 0.2s;
  }

  .refresh-btn:hover {
    background: rgba(0,212,255,0.2);
    box-shadow: 0 0 12px rgba(0,212,255,0.2);
  }

  @media (max-width: 900px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
    .grid  { grid-template-columns: 1fr; }
    main   { padding: 20px; }
    header { padding: 16px 20px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon"></div>
    <h1>SURVEILLANCE AI</h1>
  </div>
  <div class="status-bar">
    <div class="status-dot"></div>
    <span>SYSTEM ACTIVE</span>
  </div>
  <div class="time-display" id="clock">--:--:--</div>
</header>

<main>
  <div class="stats" id="stats">
    <div class="stat-card">
      <div class="stat-label">Cameras</div>
      <div class="stat-value" id="s-cameras">—</div>
      <div class="stat-sub">configured</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Online</div>
      <div class="stat-value" id="s-online" style="color:var(--green)">—</div>
      <div class="stat-sub">active streams</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Alerts Today</div>
      <div class="stat-value" id="s-alerts" style="color:var(--accent2)">—</div>
      <div class="stat-sub">motion events</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">AI Model</div>
      <div class="stat-value" id="s-model" style="font-size:18px;margin-top:6px">—</div>
      <div class="stat-sub">local inference</div>
    </div>
  </div>

  <div class="grid">
    <!-- Cameras -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">📷 Camera Status</span>
        <span class="badge" id="cam-count">0 CAMS</span>
      </div>
      <div class="cameras" id="camera-list">
        <div class="empty-state">
          <div class="empty-icon">📡</div>
          Loading cameras...
        </div>
      </div>
    </div>

    <!-- Config -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">⚙ System Config</span>
        <button class="refresh-btn" onclick="fetchData()">↻ REFRESH</button>
      </div>
      <div class="model-panel" id="config-panel">
        <div class="model-row">
          <span class="model-key">AI MODEL</span>
          <span class="model-val" id="cfg-model">—</span>
        </div>
        <div class="model-row">
          <span class="model-key">MOTION THRESHOLD</span>
          <span class="model-val" id="cfg-threshold">—</span>
        </div>
        <div class="model-row">
          <span class="model-key">ALERT COOLDOWN</span>
          <span class="model-val" id="cfg-cooldown">—</span>
        </div>
        <div class="model-row">
          <span class="model-key">CHECK INTERVAL</span>
          <span class="model-val" id="cfg-interval">—</span>
        </div>
        <div class="model-row">
          <span class="model-key">SNAPSHOTS SAVED</span>
          <span class="model-val" id="cfg-snaps">—</span>
        </div>
        <div class="model-row">
          <span class="model-key">TELEGRAM</span>
          <span class="model-val" id="cfg-telegram">—</span>
        </div>
      </div>
    </div>

    <!-- Alerts (full width) -->
    <div class="panel" style="grid-column: 1 / -1">
      <div class="panel-header">
        <span class="panel-title">🚨 Alert Log</span>
        <span class="badge" id="alert-count">0 EVENTS</span>
      </div>
      <div class="alerts" id="alert-list">
        <div class="empty-state">
          <div class="empty-icon">✅</div>
          No alerts yet — system is monitoring
        </div>
      </div>
    </div>
  </div>
</main>

<script>
  // Clock
  function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent =
      now.toLocaleTimeString('en-US', {hour12: false});
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Fetch data
  async function fetchData() {
    try {
      const res  = await fetch('/api/status');
      const data = await res.json();
      renderDashboard(data);
    } catch(e) {
      console.error('Failed to fetch:', e);
    }
  }

  function renderDashboard(data) {
    // Stats
    const online = data.cameras.filter(c => c.status === 'online').length;
    document.getElementById('s-cameras').textContent = data.cameras.length;
    document.getElementById('s-online').textContent  = online;
    document.getElementById('s-alerts').textContent  = data.alerts_today;
    document.getElementById('s-model').textContent   = data.config.model;

    // Cameras
    document.getElementById('cam-count').textContent = data.cameras.length + ' CAMS';
    const camList = document.getElementById('camera-list');
    if (data.cameras.length === 0) {
      camList.innerHTML = '<div class="empty-state"><div class="empty-icon">📷</div>No cameras configured</div>';
    } else {
      camList.innerHTML = data.cameras.map(c => `
        <div class="cam-card">
          <div class="cam-info">
            <div class="cam-icon">📷</div>
            <div>
              <div class="cam-name">${c.name}</div>
              <div class="cam-url">${c.source}</div>
            </div>
          </div>
          <div class="cam-status ${c.status}">
            <div class="status-led"></div>
            ${c.status.toUpperCase()}
          </div>
        </div>
      `).join('');
    }

    // Config
    document.getElementById('cfg-model').textContent     = data.config.model;
    document.getElementById('cfg-threshold').textContent = data.config.motion_threshold;
    document.getElementById('cfg-cooldown').textContent  = data.config.cooldown + 's';
    document.getElementById('cfg-interval').textContent  = data.config.interval + 's';
    document.getElementById('cfg-snaps').textContent     = data.snapshots_count;
    document.getElementById('cfg-telegram').textContent  = data.config.telegram_ok ? '✓ CONNECTED' : '✗ NOT SET';

    // Alerts
    const alertList = document.getElementById('alert-list');
    document.getElementById('alert-count').textContent = data.alerts.length + ' EVENTS';
    if (data.alerts.length === 0) {
      alertList.innerHTML = '<div class="empty-state"><div class="empty-icon">✅</div>No alerts yet — system is monitoring</div>';
    } else {
      alertList.innerHTML = [...data.alerts].reverse().map(a => `
        <div class="alert-item">
          <div class="alert-dot"></div>
          <div class="alert-content">
            <div class="alert-meta">
              <span class="alert-cam">${a.camera}</span>
              <span class="alert-time">${a.time}</span>
            </div>
            <div class="alert-text">${a.analysis}</div>
          </div>
        </div>
      `).join('');
    }
  }

  // Auto-refresh every 10 seconds
  fetchData();
  setInterval(fetchData, 10000);
</script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass  # Silence logs

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())

        elif self.path == '/api/status':
            # `main.py` tweaks `sys.path` such that `config` can resolve to
            # `config/config.py` (as a module), not the `config/` package.
            from config import Config
            import src.surveillance as sv

            # Load alert log
            alerts = []
            if os.path.exists("logs/alerts.json"):
                with open("logs/alerts.json") as f:
                    for line in f:
                        try: alerts.append(json.loads(line.strip()))
                        except: pass

            # Today's alerts
            today = datetime.now().strftime("%Y-%m-%d")
            alerts_today = sum(1 for a in alerts if a['time'].startswith(today))

            # Camera list with status
            cameras = []
            for name, source in Config.CAMERAS.items():
                cameras.append({
                    "name": name,
                    "source": str(source) if isinstance(source, int) else source.split("@")[-1][:30] + "…",
                    "status": sv.camera_status.get(name, "connecting")
                })

            # Snapshots count
            snaps = len(os.listdir("snapshots")) if os.path.exists("snapshots") else 0

            data = {
                "cameras": cameras,
                "alerts": alerts[-50:],  # Last 50
                "alerts_today": alerts_today,
                "snapshots_count": snaps,
                "config": {
                    "model": Config.OLLAMA_MODEL,
                    "motion_threshold": Config.MOTION_THRESHOLD,
                    "cooldown": Config.COOLDOWN_SECONDS,
                    "interval": Config.CHECK_INTERVAL,
                    "telegram_ok": Config.TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE"
                }
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())


def run_dashboard(port=5000):
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"[DASHBOARD] Running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    # Run dashboard standalone (read-only mode)
    import sys
    sys.modules['surveillance'] = type(sys)('surveillance')
    sys.modules['surveillance'].camera_status = {}
    run_dashboard()
