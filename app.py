from flask import Flask, jsonify
from src.configuration import get_config
from src.database import init_db
from src.state import get_state
from src.monitor import start_monitor
from src.savewatcher import start_savewatcher
from src.database import get_leaderboard


app = Flask(__name__)


@app.route("/status")
def status():
    return jsonify(get_state())

@app.route("/leaderboard")
def leaderboard():
    return jsonify(get_leaderboard())


@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Dragonwilds Companion</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { margin:0; background:#070b12; color:#e5e7eb; font-family:Arial,sans-serif; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:230px; background:#0d1624; padding:24px 18px; border-right:1px solid #1f2937; }
    .brand { color:#f59e0b; font-size:22px; font-weight:bold; margin-bottom:35px; line-height:1.2; }
    .brand .logo { width:40px; height:40px; background:#f59e0b; color:#111827; border-radius:12px; display:inline-flex; align-items:center; justify-content:center; font-weight:bold; margin-right:10px; }
    .nav a { display:block; color:#cbd5e1; text-decoration:none; padding:13px 16px; border-radius:10px; margin-bottom:8px; }
    .nav a.active, .nav a:hover { background:#d97706; color:white; }
    .content { flex:1; padding:28px 34px; }
    .topbar { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:28px; }
    h1 { margin:0; color:white; }
    .subtitle { color:#94a3b8; font-size:14px; margin-top:6px; }
    .online { color:#22c55e; font-weight:bold; }
    .grid { display:grid; grid-template-columns:repeat(4,minmax(180px,1fr)); gap:16px; margin-bottom:18px; }
    .card { background:#151c2b; border:1px solid #263244; border-radius:14px; padding:18px; box-shadow:0 8px 24px #0005; }
    .label { color:#94a3b8; font-size:14px; margin-bottom:8px; }
    .value { font-size:26px; font-weight:bold; color:#f8fafc; word-break:break-word; }
    .wide-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:18px; }
    .bottom-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:18px; }
    h2 { margin-top:0; font-size:22px; }
    table { width:100%; border-collapse:collapse; }
    th,td { padding:11px 8px; border-bottom:1px solid #263244; text-align:left; }
    th { color:#94a3b8; font-weight:normal; }
    .event { padding:8px 0; border-bottom:1px solid #263244; }
    .time { color:#94a3b8; margin-right:8px; }
    .pill { display:inline-block; background:#1e293b; color:#f59e0b; padding:7px 12px; border-radius:999px; font-weight:bold; font-size:13px; }
    .status-dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:#22c55e; margin-right:8px; }
    .icon { width:38px; height:38px; border-radius:12px; background:#1e293b; display:flex; align-items:center; justify-content:center; color:#f59e0b; font-weight:bold; margin-bottom:12px; }
    .player-row { display:flex; align-items:center; justify-content:space-between; padding:12px; border:1px solid #263244; border-radius:12px; margin-bottom:10px; }
    .avatar { width:38px; height:38px; border-radius:50%; background:#1f2937; color:#22c55e; display:flex; align-items:center; justify-content:center; font-weight:bold; margin-right:12px; }
    .player-left { display:flex; align-items:center; }
    .small { color:#94a3b8; font-size:13px; }
    @media(max-width:1200px){ .grid{grid-template-columns:repeat(2,1fr);} .wide-grid,.bottom-grid{grid-template-columns:1fr;} .sidebar{display:none;} }
    @media(max-width:600px){ .grid{grid-template-columns:1fr;} .content{padding:18px;} }
  </style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand"><span class="logo">DW</span>Dragonwilds<br>Companion</div>
    <div class="nav">
      <a class="active" href="#">Overview</a>
      <a href="#players">Players</a>
      <a href="#leaderboard">Leaderboard</a>
      <a href="#events">Events</a>
      <a href="/status">API Status</a>
      <a href="/leaderboard">API Leaderboard</a>
    </div>
  </aside>

  <main class="content">
    <div class="topbar">
      <div>
        <h1>Overview</h1>
        <div class="subtitle">Real-time overview of your Dragonwilds server</div>
      </div>
      <div>
        <div class="online"><span class="status-dot"></span>Server Online</div>
        <div class="subtitle">Updated: <span id="updated">...</span></div>
      </div>
    </div>

    <div class="grid">
      <div class="card"><div class="icon">PL</div><div class="label">Players</div><div class="value" id="players">...</div></div>
      <div class="card"><div class="icon">NM</div><div class="label">Names</div><div class="value" id="names">...</div></div>
      <div class="card"><div class="icon">WD</div><div class="label">World</div><div class="value" id="world">...</div></div>
      <div class="card"><div class="icon">UP</div><div class="label">Uptime</div><div class="value" id="uptime">...</div></div>
      <div class="card"><div class="icon">SV</div><div class="label">Last Save</div><div class="value" id="save">...</div></div>
      <div class="card"><div class="icon">CPU</div><div class="label">CPU</div><div class="value" id="cpu">...</div></div>
      <div class="card"><div class="icon">RAM</div><div class="label">RAM</div><div class="value" id="ram">...</div></div>
      <div class="card"><div class="icon">VER</div><div class="label">Version</div><div class="value" id="version">...</div></div>
    </div>

    <div class="wide-grid">
      <div class="card" id="events">
        <h2>Recent Events</h2>
        <div id="event-list">Loading...</div>
      </div>

      <div class="card" id="leaderboard">
        <h2>Leaderboard <span class="pill">Top 10</span></h2>
        <table>
          <thead><tr><th>#</th><th>Player</th><th>Playtime</th><th>Sessions</th><th>Longest</th></tr></thead>
          <tbody id="leaderboard-body"><tr><td colspan="5">Loading...</td></tr></tbody>
        </table>
      </div>
    </div>

    <div class="bottom-grid">
      <div class="card" id="players-card">
        <h2>Current Players</h2>
        <div id="current-players">Loading...</div>
      </div>

      <div class="card">
        <h2>Server Health</h2>
        <div class="label">Status</div>
        <div class="value online">Healthy</div>
        <br>
        <div class="small">Server running, API responding, save path active.</div>
      </div>

      <div class="card">
        <h2>Quick Links</h2>
        <p><a style="color:#f59e0b;" href="/status">Status API</a></p>
        <p><a style="color:#f59e0b;" href="/leaderboard">Leaderboard API</a></p>
      </div>
    </div>
  </main>
</div>

<script>
async function loadStatus() {
  const res = await fetch('/status');
  const s = await res.json();

  document.getElementById('players').innerText = `${s.players_online} / ${s.max_players}`;
  document.getElementById('names').innerText = s.players_text;
  document.getElementById('world').innerText = s.world;
  document.getElementById('uptime').innerText = s.uptime;
  document.getElementById('save').innerText = s.last_save;
  document.getElementById('cpu').innerText = s.cpu;
  document.getElementById('ram').innerText = s.memory;
  document.getElementById('version').innerText = s.version;
  document.getElementById('updated').innerText = new Date().toLocaleTimeString();

  const events = document.getElementById('event-list');
  events.innerHTML = '';
  if (!s.events || s.events.length === 0) {
    events.innerHTML = '<div class="subtitle">No recent events</div>';
  } else {
    s.events.forEach(e => {
      const div = document.createElement('div');
      div.className = 'event';
      div.innerHTML = `<span class="time">[${e.timestamp || ''}]</span>${e.message}`;
      events.appendChild(div);
    });
  }

  const players = document.getElementById('current-players');
  players.innerHTML = '';
  if (!s.players || s.players.length === 0) {
    players.innerHTML = '<div class="subtitle">No players online</div>';
  } else {
    s.players.forEach(p => {
      const first = p.substring(0,1).toUpperCase();
      const row = document.createElement('div');
      row.className = 'player-row';
      row.innerHTML = `
        <div class="player-left">
          <div class="avatar">${first}</div>
          <div>
            <div><strong>${p}</strong></div>
            <div class="small">Currently online</div>
          </div>
        </div>
        <div class="online">Online</div>
      `;
      players.appendChild(row);
    });
  }
}

async function loadLeaderboard() {
  const res = await fetch('/leaderboard');
  const rows = await res.json();

  const body = document.getElementById('leaderboard-body');
  body.innerHTML = '';

  if (!rows || rows.length === 0) {
    body.innerHTML = '<tr><td colspan="5">No completed sessions yet</td></tr>';
    return;
  }

  rows.forEach((row, index) => {
    const rank = index === 0 ? '1' : index === 1 ? '2' : index === 2 ? '3' : index + 1;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${rank}</td>
      <td>${row.player}</td>
      <td>${row.playtime}</td>
      <td>${row.sessions}</td>
      <td>${row.longest_session}</td>
    `;
    body.appendChild(tr);
  });
}

async function refresh() {
  await loadStatus();
  await loadLeaderboard();
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    config = get_config()
    init_db()
    start_monitor()
    start_savewatcher()

    app.run(
        host="0.0.0.0",
        port=config.PORT
    )
    start_savewatcher()

    app.run(
        host="0.0.0.0",
        port=config.PORT
    )