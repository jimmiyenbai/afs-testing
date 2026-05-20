"""
AFS Dashboard Server
============================
Flask server + dashboard cho AFS Controller.

Chạy:
    pip install flask
    python app.py

Mở trình duyệt:
    http://localhost:5000
"""

import json
from dataclasses import asdict, fields

from flask import Flask, jsonify, request

from afs import AFSConfig, AFSController

app = Flask(__name__)
DEFAULT_CONFIG = AFSConfig()
CONFIG_FIELD_NAMES = tuple(field.name for field in fields(AFSConfig))

# ── Dashboard HTML (inline — không cần thư mục templates) ────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AFS Controller — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0c0f13;--surface:#151921;--border:#1e2530;
  --text:#d4dae3;--dim:#6b7a8d;--accent:#22d3ee;
  --warn:#f59e0b;--danger:#ef4444;--ok:#10b981;
  --yaw-color:#22d3ee;--pitch-color:#a78bfa;
  --radius:6px;
}
body{font-family:'DM Sans',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.mono{font-family:'JetBrains Mono',monospace}

/* Layout */
.shell{max-width:1400px;margin:0 auto;padding:24px 20px}
header{display:flex;align-items:baseline;gap:12px;margin-bottom:28px;border-bottom:1px solid var(--border);padding-bottom:16px}
header h1{font-size:18px;font-weight:600;letter-spacing:-.02em}
header span{font-size:12px;color:var(--dim);font-family:'JetBrains Mono',monospace}
.main-grid{display:grid;grid-template-columns:320px minmax(0,1fr) minmax(0,1fr);gap:16px;align-items:start}
.controls-column{display:flex;flex-direction:column;gap:16px;align-self:start}
.viz-card{display:flex;flex-direction:column;align-self:start;min-height:0;padding:0;border:none;background:transparent}
.debug-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
@media(max-width:1100px){.main-grid{grid-template-columns:1fr;}.debug-grid{grid-template-columns:1fr}}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px}
.card h2{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);margin-bottom:14px}

/* Sliders */
.slider-row{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.slider-row label{flex:0 0 60px;font-size:12px;color:var(--dim)}
.slider-row input[type=range]{flex:1;min-width:0;accent-color:var(--accent);height:4px;-webkit-appearance:none;background:var(--border);border-radius:2px;outline:none}
.slider-row input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--accent);cursor:pointer}
.slider-row .value-box{flex:0 0 114px;display:flex;align-items:center;gap:6px}
.slider-row .value-input{width:74px;padding:6px 8px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text);font:500 12px 'JetBrains Mono',monospace;text-align:right}
.slider-row .value-input:focus{outline:none;border-color:var(--accent)}
.slider-row .value-unit{font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--dim);white-space:nowrap}
.actions{display:flex;justify-content:flex-end;margin-top:6px}
.btn{border:1px solid var(--border);background:var(--bg);color:var(--text);padding:9px 14px;border-radius:var(--radius);font:600 11px 'JetBrains Mono',monospace;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;transition:border-color .15s ease,color .15s ease,transform .15s ease}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn:active{transform:translateY(1px)}
.presets{display:flex;flex-direction:column;gap:6px;margin-bottom:0}
.preset{border:1px solid var(--border);background:var(--surface);color:var(--dim);padding:7px 10px;border-radius:var(--radius);font:500 11px 'DM Sans',system-ui,sans-serif;cursor:pointer;transition:all .15s ease;white-space:nowrap;text-align:left}
.preset:hover{border-color:var(--accent);color:var(--accent);background:rgba(34,211,238,.06)}
.preset.active{border-color:var(--accent);color:var(--accent);background:rgba(34,211,238,.1)}

/* Config inputs */
.config-toolbar{margin-top:16px}
.config-toolbar-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:14px}
.config-toolbar-head .actions{margin-top:0;flex:0 0 auto}
.config-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.config-note{font-size:11px;line-height:1.45;color:var(--dim);margin:0;max-width:760px}
.config-section{padding:12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg)}
.config-section-label{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin-bottom:8px}
.config-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.config-item{display:flex;flex-direction:column;gap:5px}
.config-item label{font-size:11px;color:var(--dim);line-height:1.25}
.config-item input{width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text);font:500 12px 'JetBrains Mono',monospace}
.config-item input:focus{outline:none;border-color:var(--accent)}
@media(max-width:720px){.config-toolbar-head{flex-direction:column;align-items:stretch}.config-toolbar-head .actions{justify-content:stretch}.config-toolbar-head .btn{width:100%}}
@media(max-width:520px){.config-grid{grid-template-columns:1fr}}

/* Output gauges */
.gauges{display:flex;gap:16px;margin-bottom:16px}
.gauge{flex:1;text-align:center;padding:14px 0;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg)}
.gauge .num{font-size:28px;font-weight:600;font-family:'JetBrains Mono',monospace;line-height:1.1}
.gauge .lbl{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;margin-top:4px}
.yaw-num{color:var(--yaw-color)}
.pitch-num{color:var(--pitch-color)}

/* Debug table */
.dbg-table{width:100%;font-size:12px;border-collapse:collapse}
.dbg-table td{padding:4px 0;border-bottom:1px solid var(--border)}
.dbg-table td:first-child{color:var(--dim);width:55%}
.dbg-table td:last-child{text-align:right;font-family:'JetBrains Mono',monospace}

/* Car visualization — top view (yaw) — SVG based */
.car-viz{position:relative;flex:1 1 auto;width:100%;min-height:0;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);overflow:hidden;display:flex;align-items:center;justify-content:center;padding:10px}
.viz-title{position:absolute;top:12px;left:12px;z-index:2;padding:6px 10px;border:1px solid var(--border);border-radius:5px;background:rgba(12,15,19,.9);font:600 10px 'JetBrains Mono',monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--dim)}
.yaw-label{position:absolute;font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:500}
.yaw-angle-label{top:12px;right:16px;color:var(--yaw-color)}
.yaw-pitch-label{bottom:12px;right:16px;color:var(--pitch-color)}

/* Car visualization — side view (pitch) — SVG based */
.side-viz{position:relative;flex:1 1 auto;width:100%;min-height:0;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);overflow:hidden;display:flex;align-items:center;justify-content:center;padding:10px}
.viz-svg{display:block;max-width:none}
#yaw-svg{width:100%;height:100%}
#pitch-svg{width:100%;height:100%}
.pitch-info{position:absolute;font-family:'JetBrains Mono',monospace;font-size:12px}
.pitch-info-body{top:12px;left:16px;color:var(--dim)}
.pitch-info-lamp{top:12px;right:16px;color:var(--pitch-color)}
@media(max-width:1100px){.viz-card{height:auto}.car-viz,.side-viz{height:320px}#yaw-svg,#pitch-svg{width:100%;height:100%}}

/* Status bar */
.status{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:var(--radius);font-size:11px;font-family:'JetBrains Mono',monospace;background:var(--surface);border:1px solid var(--border);margin-top:16px}
.dot{width:6px;height:6px;border-radius:50%;background:var(--ok);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
</style>
</head>
<body>
<div class="shell">
  <header>
    <h1>AFS Controller</h1>
    <span>Demo mô phỏng</span>
  </header>

  <!-- Output gauges -->
  <div class="gauges">
    <div class="gauge">
      <div class="num yaw-num" id="g-yaw">+0.000</div>
      <div class="lbl">Yaw [deg]</div>
    </div>
    <div class="gauge">
      <div class="num pitch-num" id="g-pitch">+0.000</div>
      <div class="lbl">Pitch [deg]</div>
    </div>
  </div>

  <!-- Main 3-column layout: [Controls] [Yaw viz] [Pitch viz] -->
  <div class="main-grid">

<!-- LEFT COLUMN: Preset + Input -->
    <div class="controls-column">
      <div class="card">
        <h2>Preset</h2>
        <div class="presets" id="preset-bar" style="flex-direction:column"></div>
      </div>
      <div class="card">
        <h2>Input</h2>
        <div class="slider-row">
          <label>Tốc độ</label>
          <input type="range" id="s-speed" min="0" max="180" value="40" step="1">
          <div class="value-box">
            <input type="number" class="value-input" id="n-speed" min="0" max="180" value="40" step="1" inputmode="numeric">
            <span class="value-unit">km/h</span>
          </div>
        </div>
        <div class="slider-row">
          <label>Vô lăng</label>
          <input type="range" id="s-steer" min="-540" max="540" value="0" step="1">
          <div class="value-box">
            <input type="number" class="value-input" id="n-steer" min="-540" max="540" value="0" step="1" inputmode="numeric">
            <span class="value-unit">°</span>
          </div>
        </div>
        <div class="slider-row">
          <label>H trước</label>
          <input type="range" id="s-hf" min="300" max="420" value="350" step="1">
          <div class="value-box">
            <input type="number" class="value-input" id="n-hf" min="300" max="420" value="350" step="1" inputmode="numeric">
            <span class="value-unit">mm</span>
          </div>
        </div>
        <div class="slider-row">
          <label>H sau</label>
          <input type="range" id="s-hr" min="300" max="420" value="350" step="1">
          <div class="value-box">
            <input type="number" class="value-input" id="n-hr" min="300" max="420" value="350" step="1" inputmode="numeric">
            <span class="value-unit">mm</span>
          </div>
        </div>
        <div class="actions">
          <button type="button" class="btn" id="btn-reset">Reset</button>
        </div>
      </div>
      <div class="card">
        <h2>Xe đối diện</h2>
        <div class="presets" id="oncoming-bar" style="display:grid;grid-template-columns:1fr 1fr;gap:6px"></div>
        <p class="config-note" style="margin-top:10px">Preset khoảng cách dùng chung một tỉ lệ dọc: 20 / 30 / 60 m. Chùm chính kết thúc tại 60 m.</p>
      </div>
    </div>

    <!-- MIDDLE COLUMN: Yaw visualization -->
    <div class="card viz-card">
      <div class="car-viz">
        <div class="viz-title">Nhìn trên — Yaw</div>
        <svg id="yaw-svg" class="viz-svg" viewBox="80 72 360 600" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="road-grad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#233040" stop-opacity="0.82"/>
              <stop offset="100%" stop-color="#1a2533" stop-opacity="0.92"/>
            </linearGradient>
            <radialGradient id="beam-main-grad" cx="38%" cy="100%" r="98%">
              <stop offset="0%" stop-color="#ffe08a" stop-opacity="0.70"/>
              <stop offset="38%" stop-color="#ffd166" stop-opacity="0.58"/>
              <stop offset="72%" stop-color="#f4c542" stop-opacity="0.30"/>
              <stop offset="100%" stop-color="#f4c542" stop-opacity="0.10"/>
            </radialGradient>
            <radialGradient id="beam-far-grad" cx="45%" cy="100%" r="100%">
              <stop offset="0%" stop-color="#f4d35e" stop-opacity="0.22"/>
              <stop offset="100%" stop-color="#f4d35e" stop-opacity="0.03"/>
            </radialGradient>
            <filter id="beam-glow" x="-25%" y="-25%" width="150%" height="150%">
              <feGaussianBlur stdDeviation="2" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>

          <!-- road is now drawn dynamically so turning cases are visible in the top view -->
          <path id="road-fill" d="" fill="url(#road-grad)" stroke="#334155" stroke-width="1.5"/>
          <path id="road-left-edge" d="" fill="none" stroke="#506074" stroke-width="1" opacity="0.75"/>
          <path id="road-right-edge" d="" fill="none" stroke="#506074" stroke-width="1" opacity="0.75"/>
          <path id="lane-center" d="" fill="none" stroke="#f4d35e" stroke-width="3" stroke-dasharray="28 24" opacity="0.95"/>

          <g id="distance-scale" font-family="JetBrains Mono,monospace" font-size="11" fill="#93a4bb" opacity="0.92"></g>
          <g id="road-distance-guides" stroke="#93a4bb" stroke-width="0.6" stroke-dasharray="3 7" opacity="0.22"></g>

          <path id="beam-far-shape" d="" fill="url(#beam-far-grad)" stroke="#f4d35e" stroke-width="1" opacity="0.70" filter="url(#beam-glow)"/>
          <path id="beam-main-shape" d="" fill="url(#beam-main-grad)" stroke="#ffe08a" stroke-width="1.5" opacity="0.95" filter="url(#beam-glow)"/>
          <path id="beam-cutoff-line" d="" fill="none" stroke="#ffe08a" stroke-width="1.4" stroke-dasharray="8 6" opacity="0"/>
          <line id="beam-axis-line" x1="0" y1="0" x2="0" y2="0" stroke="#ffe08a" stroke-width="1.4" stroke-dasharray="8 8" opacity="0"/>
          <g id="beam-marks" font-family="JetBrains Mono,monospace" font-size="10" font-weight="700"></g>

          <g id="oncoming-car"></g>
          <g id="own-car"></g>

          <path id="yaw-arc" d="" fill="none" stroke="#22d3ee" stroke-width="1.5" opacity="0.8"/>
          <text id="yaw-angle-text" x="330" y="570" text-anchor="middle" fill="#22d3ee" font-family="JetBrains Mono,monospace" font-size="22" font-weight="700" opacity="0.95">0°</text>
          <text id="beam-status-text" x="90" y="650" fill="#10b981" font-family="JetBrains Mono,monospace" font-size="11" font-weight="700"></text>
        </svg>
        <div class="yaw-label yaw-pitch-label" id="viz-pitch-badge"></div>
      </div>
    </div>

    <!-- RIGHT COLUMN: Pitch visualization -->
    <div class="card viz-card">
      <div class="side-viz">
        <div class="viz-title">Nhìn ngang — Pitch</div>
        <svg id="pitch-svg" class="viz-svg" viewBox="110 185 300 180">
          <defs>
            <linearGradient id="pitch-beam-grad" x1="0%" y1="50%" x2="100%" y2="50%">
              <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.5"/>
              <stop offset="100%" stop-color="#a78bfa" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="310" x2="400" y2="310" stroke="#6b7a8d" stroke-width="1" opacity="0.3"/>
          <line x1="0" y1="309" x2="400" y2="309" stroke="#6b7a8d" stroke-width="0.5" stroke-dasharray="8 12" opacity="0.15"/>

          <g id="pitch-car-group" transform="rotate(0 235 290)">
            <rect x="140" y="262" width="120" height="36" rx="4" fill="none" stroke="#6b7a8d" stroke-width="1.5"/>
            <line x1="155" y1="262" x2="165" y2="252" stroke="#6b7a8d" stroke-width="1"/>
            <line x1="165" y1="252" x2="235" y2="252" stroke="#6b7a8d" stroke-width="1"/>
            <line x1="235" y1="252" x2="245" y2="262" stroke="#6b7a8d" stroke-width="1"/>
            <rect x="258" y="272" width="6" height="10" rx="1" fill="#f59e0b" opacity="0.8"/>
          </g>

          <circle cx="170" cy="300" r="10" fill="none" stroke="#6b7a8d" stroke-width="1.5"/>
          <circle cx="170" cy="300" r="3" fill="#6b7a8d" opacity="0.4"/>
          <circle cx="235" cy="300" r="10" fill="none" stroke="#6b7a8d" stroke-width="1.5"/>
          <circle cx="235" cy="300" r="3" fill="#6b7a8d" opacity="0.4"/>

          <g id="pitch-beam-group" transform="rotate(0 264 277)">
            <path d="M264,277 L400,247 L400,307 Z" fill="url(#pitch-beam-grad)" opacity="0.5"/>
            <line x1="264" y1="277" x2="400" y2="277" stroke="#a78bfa" stroke-width="0.8" stroke-dasharray="4 4" opacity="0.4"/>
          </g>

          <line x1="264" y1="277" x2="400" y2="277" stroke="#6b7a8d" stroke-width="0.5" stroke-dasharray="2 6" opacity="0.2"/>

          <g id="dh-front-group">
            <line x1="165" y1="310" x2="165" y2="320" stroke="#6b7a8d" stroke-width="0.5" opacity="0.5"/>
            <text id="dh-front-text" x="165" y="338" text-anchor="middle" fill="#6b7a8d" font-family="JetBrains Mono,monospace" font-size="10">Δf: 0</text>
          </g>
          <g id="dh-rear-group">
            <line x1="240" y1="310" x2="240" y2="320" stroke="#6b7a8d" stroke-width="0.5" opacity="0.5"/>
            <text id="dh-rear-text" x="240" y="338" text-anchor="middle" fill="#6b7a8d" font-family="JetBrains Mono,monospace" font-size="10">Δr: 0</text>
          </g>

          <text id="pitch-lamp-text" x="380" y="240" text-anchor="end" fill="#a78bfa" font-family="JetBrains Mono,monospace" font-size="14" font-weight="500"></text>
          <text id="pitch-body-text" x="130" y="245" text-anchor="end" fill="#6b7a8d" font-family="JetBrains Mono,monospace" font-size="11"></text>
        </svg>
      </div>
    </div>

  </div>

  <div class="card config-toolbar">
    <div class="config-toolbar-head">
      <div>
        <h2>Tham số tính toán</h2>
        <div class="config-note">Thanh cấu hình nằm riêng dưới hàng chính để tiện quan sát input và hai hình chiếu. Đổi tham số sẽ tính lại ngay với bộ cấu hình mới.</div>
      </div>
      <div class="actions">
        <button type="button" class="btn" id="btn-reset-config">Mặc định</button>
      </div>
    </div>

    <div class="config-strip">
      <div class="config-section">
        <div class="config-section-label">Hình học &amp; mốc chuẩn</div>
        <div class="config-grid">
          <div class="config-item">
            <label for="cfg-steering-ratio">Tỷ số lái</label>
            <input type="number" id="cfg-steering-ratio" step="0.1">
          </div>
          <div class="config-item">
            <label for="cfg-wheelbase">Wheelbase [m]</label>
            <input type="number" id="cfg-wheelbase" step="0.01">
          </div>
          <div class="config-item">
            <label for="cfg-sensor-base">Sensor base [m]</label>
            <input type="number" id="cfg-sensor-base" step="0.01">
          </div>
          <div class="config-item">
            <label for="cfg-front-ref">H ref trước [mm]</label>
            <input type="number" id="cfg-front-ref" step="1">
          </div>
          <div class="config-item">
            <label for="cfg-rear-ref">H ref sau [mm]</label>
            <input type="number" id="cfg-rear-ref" step="1">
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-label">Giới hạn actuator</div>
        <div class="config-grid">
          <div class="config-item">
            <label for="cfg-max-yaw">Max yaw [deg]</label>
            <input type="number" id="cfg-max-yaw" step="0.1">
          </div>
          <div class="config-item">
            <label for="cfg-min-pitch">Min pitch [deg]</label>
            <input type="number" id="cfg-min-pitch" step="0.1">
          </div>
          <div class="config-item">
            <label for="cfg-max-pitch">Max pitch [deg]</label>
            <input type="number" id="cfg-max-pitch" step="0.1">
          </div>
          <div class="config-item">
            <label for="cfg-max-yaw-rate">Yaw rate [deg/s]</label>
            <input type="number" id="cfg-max-yaw-rate" step="0.1">
          </div>
          <div class="config-item">
            <label for="cfg-max-pitch-rate">Pitch rate [deg/s]</label>
            <input type="number" id="cfg-max-pitch-rate" step="0.1">
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-label">Preview &amp; lọc</div>
        <div class="config-grid">
          <div class="config-item">
            <label for="cfg-lpf-tau">LPF τ [s]</label>
            <input type="number" id="cfg-lpf-tau" step="0.001">
          </div>
          <div class="config-item">
            <label for="cfg-preview-a">Preview a [s]</label>
            <input type="number" id="cfg-preview-a" step="0.001">
          </div>
          <div class="config-item">
            <label for="cfg-preview-b">Preview b [s·km/h]</label>
            <input type="number" id="cfg-preview-b" step="0.001">
          </div>
          <div class="config-item">
            <label for="cfg-preview-min">Preview min [s]</label>
            <input type="number" id="cfg-preview-min" step="0.01">
          </div>
          <div class="config-item">
            <label for="cfg-preview-max">Preview max [s]</label>
            <input type="number" id="cfg-preview-max" step="0.01">
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Debug row: 2 columns -->
  <div class="debug-grid">
    <div class="card">
      <h2>Debug — Yaw</h2>
      <table class="dbg-table">
        <tr><td>Góc bánh trước</td><td id="d-fw">—</td></tr>
        <tr><td>Curvature κ</td><td id="d-kappa">—</td></tr>
        <tr><td>Preview time tₚ</td><td id="d-tp">—</td></tr>
        <tr><td>Preview distance</td><td id="d-pd">—</td></tr>
        <tr><td>Yaw target (trước rate limit)</td><td id="d-yt">—</td></tr>
        <tr><td>Bán kính cua</td><td id="d-radius">—</td></tr>
        <tr><td>Tốc độ [m/s]</td><td id="d-vmps">—</td></tr>
      </table>
    </div>
    <div class="card">
      <h2>Debug — Pitch</h2>
      <table class="dbg-table">
        <tr><td>Δh trước (so với ref)</td><td id="d-dhf">—</td></tr>
        <tr><td>Δh sau (so với ref)</td><td id="d-dhr">—</td></tr>
        <tr><td>Pitch thân xe</td><td id="d-pb">—</td></tr>
        <tr><td>Pitch target (trước rate limit)</td><td id="d-pt">—</td></tr>
        <tr><td>Pitch đèn (output)</td><td id="d-po">—</td></tr>
        <tr><td>H trước [mm]</td><td id="d-hf-abs">—</td></tr>
        <tr><td>H sau [mm]</td><td id="d-hr-abs">—</td></tr>
      </table>
    </div>
  </div>

  <div class="status">
    <div class="dot" id="status-dot"></div>
    <span id="status-text">Controller sẵn sàng — kéo slider để thay đổi</span>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
const INPUT_FIELDS = [
  { slider: 's-speed', number: 'n-speed' },
  { slider: 's-steer', number: 'n-steer' },
  { slider: 's-hf', number: 'n-hf' },
  { slider: 's-hr', number: 'n-hr' },
];
const sliders = INPUT_FIELDS.map(field => field.slider);
const INPUT_FIELD_BY_SLIDER = Object.fromEntries(INPUT_FIELDS.map(field => [field.slider, field]));
const DEFAULT_STATUS = 'Controller sẵn sàng — kéo slider để thay đổi';
const DEFAULT_INPUTS = {
  's-speed': 40,
  's-steer': 0,
  's-hf': 350,
  's-hr': 350,
};
const DEFAULT_CONFIG = __DEFAULT_CONFIG_JSON__;
const CONFIG_FIELDS = [
  { id: 'cfg-steering-ratio', key: 'steering_ratio' },
  { id: 'cfg-wheelbase', key: 'wheelbase_m' },
  { id: 'cfg-sensor-base', key: 'sensor_base_m' },
  { id: 'cfg-front-ref', key: 'front_height_ref_mm' },
  { id: 'cfg-rear-ref', key: 'rear_height_ref_mm' },
  { id: 'cfg-max-yaw', key: 'max_yaw_deg' },
  { id: 'cfg-min-pitch', key: 'min_pitch_deg' },
  { id: 'cfg-max-pitch', key: 'max_pitch_deg' },
  { id: 'cfg-max-yaw-rate', key: 'max_yaw_rate_dps' },
  { id: 'cfg-max-pitch-rate', key: 'max_pitch_rate_dps' },
  { id: 'cfg-lpf-tau', key: 'steering_lpf_tau_s' },
  { id: 'cfg-preview-a', key: 'preview_a_s' },
  { id: 'cfg-preview-b', key: 'preview_b_s_kmh' },
  { id: 'cfg-preview-min', key: 'preview_min_s' },
  { id: 'cfg-preview-max', key: 'preview_max_s' },
];

const PRESETS = [
  { name: 'Đi thẳng 60 km/h',         speed: 60, steer:    0, hf: 350, hr: 350 },
  { name: 'Vào cua phải nhẹ',         speed: 60, steer:   18, hf: 350, hr: 350 },
  { name: 'Vào cua trái nhẹ',         speed: 60, steer:  -18, hf: 350, hr: 350 },
  { name: 'Vào cua phải vừa',         speed: 40, steer:   45, hf: 350, hr: 350 },
  { name: 'Vào cua trái vừa',         speed: 40, steer:  -45, hf: 350, hr: 350 },
  { name: 'Cua gắt phải',             speed: 20, steer:   90, hf: 350, hr: 350 },
  { name: 'Cua gắt trái',             speed: 20, steer:  -90, hf: 350, hr: 350 },
  { name: 'Tải nặng phía sau',        speed: 50, steer:    0, hf: 345, hr: 370 },
  { name: 'Phanh gấp (đầu chúi)',     speed: 50, steer:    0, hf: 365, hr: 340 },
  { name: 'Đỗ xe, cua rất gấp',       speed: 3,  steer:  220, hf: 350, hr: 350 },
];

const ONCOMING_DISTANCES_M = [20, 30, 60, 100];
let selectedOncomingDistanceM = 60;

let timer = null;
let activePreset = -1;
const controlsColumn = document.querySelector('.controls-column');
const vizCards = Array.from(document.querySelectorAll('.viz-card'));

function getControlsClusterHeight() {
  if (!controlsColumn) return 0;

  const cards = Array.from(controlsColumn.children);
  const gap = parseFloat(getComputedStyle(controlsColumn).gap || '0') || 0;
  const contentHeight = cards.reduce((sum, card) => sum + card.getBoundingClientRect().height, 0);
  return Math.round(contentHeight + gap * Math.max(cards.length - 1, 0));
}

function syncVizCardHeights() {
  if (!controlsColumn || vizCards.length === 0) return;

  if (window.innerWidth <= 1100) {
    vizCards.forEach(card => {
      card.style.height = '';
    });
    return;
  }

  const controlsHeight = getControlsClusterHeight();
  if (controlsHeight <= 0) return;

  vizCards.forEach(card => {
    card.style.height = `${controlsHeight}px`;
  });
}

// Build preset buttons
const presetBar = $('preset-bar');
PRESETS.forEach((p, i) => {
  const btn = document.createElement('button');
  btn.className = 'preset';
  btn.textContent = p.name;
  btn.addEventListener('click', () => applyPreset(i));
  presetBar.appendChild(btn);
});

const oncomingBar = $('oncoming-bar');
ONCOMING_DISTANCES_M.forEach(distanceM => {
  const btn = document.createElement('button');
  btn.className = 'preset oncoming-distance';
  btn.textContent = `${distanceM} m`;
  btn.dataset.distanceM = distanceM;
  btn.addEventListener('click', () => {
    selectedOncomingDistanceM = distanceM;
    updateOncomingDistanceHighlight();
    queueSend();
  });
  oncomingBar.appendChild(btn);
});

function updateOncomingDistanceHighlight() {
  document.querySelectorAll('.oncoming-distance').forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.distanceM) === selectedOncomingDistanceM);
  });
}

function applyPreset(idx) {
  const p = PRESETS[idx];
  $('s-speed').value = p.speed;
  $('s-steer').value = p.steer;
  $('s-hf').value    = p.hf;
  $('s-hr').value    = p.hr;
  syncAllNumberInputs();
  activePreset = idx;
  updatePresetHighlight();
  send();
}

function updatePresetHighlight() {
  document.querySelectorAll('.preset').forEach((btn, i) => {
    btn.classList.toggle('active', i === activePreset);
  });
}

function clearPresetHighlight() {
  activePreset = -1;
  updatePresetHighlight();
}

function setStatus(text, isError = false) {
  $('status-text').textContent = text;
  $('status-dot').style.background = isError ? 'var(--danger)' : 'var(--ok)';
}

function setConfigInputs(config) {
  CONFIG_FIELDS.forEach(({ id, key }) => {
    $(id).value = config[key];
  });
}

function getConfigBody() {
  const config = {};

  CONFIG_FIELDS.forEach(({ id, key }) => {
    const raw = $(id).value;
    const parsed = Number(raw);
    config[key] = raw === '' || !Number.isFinite(parsed) ? null : parsed;
  });

  return config;
}

function queueSend({ clearPreset = false } = {}) {
  clearTimeout(timer);
  if (clearPreset) clearPresetHighlight();
  timer = setTimeout(send, 30);
}

function clampToSliderRange(sliderId, value) {
  const slider = $(sliderId);
  const min = slider.min === '' ? -Infinity : Number(slider.min);
  const max = slider.max === '' ? Infinity : Number(slider.max);
  return Math.min(max, Math.max(min, value));
}

function syncNumberFromSlider(sliderId) {
  const field = INPUT_FIELD_BY_SLIDER[sliderId];
  if (!field) return;
  $(field.number).value = $(sliderId).value;
}

function syncAllNumberInputs() {
  INPUT_FIELDS.forEach(({ slider }) => {
    syncNumberFromSlider(slider);
  });
}

function setInputPair(sliderId, rawValue) {
  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed)) return null;

  const clamped = clampToSliderRange(sliderId, parsed);
  $(sliderId).value = clamped;
  syncNumberFromSlider(sliderId);
  return clamped;
}


// -----------------------------------------------------------------------------
// Low-beam footprint top-view
// Đây là hình học dashboard, không phải phân bố lux/candela. Quan trọng là:
//  1) đường/làn xe giữ cố định,
//  2) chùm sáng, cutoff và mốc 20/30/60 m dùng cùng một hệ tọa độ,
//  3) xe đối diện được đặt theo đúng khoảng cách thật trên trục dọc.
// -----------------------------------------------------------------------------
const YAW_VIEW = {
  x0: 280,      // screen x tại tim đường
  y0: 620,      // screen y tại mũi xe mình / gốc chùm sáng
  sx: 28,       // px/m ngang; dùng chung cho đường, xe và chùm sáng
  sy: 5.2,      // px/m dọc; 60 m -> 312 px
  ownLaneX: 1.85,
  oncomingLaneX: -1.85,
  laneWidthM: 3.7,
  vehicleWidthM: 1.8,
  vehicleLengthM: 4.4,
  roadLengthM: 125,   // kéo mặt đường vượt khỏi khung để không lộ nắp/đường đóng ở mép trên
  curveDisplayGain: 0.05,
  curveDisplayClamp: 0.0014,
};

// Biên dạng chùm sáng được lấy lại theo contour của ảnh mẫu Wikimedia.
// Hệ toạ độ local: x = ngang theo làn xe, y = khoảng cách phía trước xe.
// Không còn chia scale riêng cho từng vùng; footprint dùng chung thước 0–60 m của dashboard.
// Chú ý: đây vẫn là footprint nhìn từ trên xuống, không phải mô phỏng photometric/lux theo UNECE.
const LOW_BEAM_MAIN_POLY = [
  [-0.68, 0.00], [0.86, 0.00], [0.94, 0.30], [1.03, 1.30], [1.12, 3.20], [1.36, 7.20],
  [1.66, 11.80], [1.98, 16.80], [2.32, 22.40], [2.62, 29.60],
  [2.84, 37.80], [2.80, 46.20], [2.50, 54.60], [2.00, 62.50],
  [1.36, 69.60], [0.56, 75.00], [-0.32, 78.40], [-0.98, 78.10],
  [-1.46, 74.80], [-1.82, 68.10], [-2.05, 59.30], [-2.30, 49.30],
  [-2.82, 40.00], [-3.50, 31.80], [-4.00, 27.20], [-4.08, 24.00],
  [-3.86, 20.40], [-3.34, 15.00], [-2.56, 9.20], [-1.56, 4.00]
];
const LOW_BEAM_FAR_POLY = [];
const LOW_BEAM_CUTOFF = [[-0.18, 0], [-0.42, 10], [-0.82, 20], [-1.02, 30], [-1.04, 60]];

function yawDisplayDeg(realYawDeg) {
  // Do trục X/Y trên dashboard dùng hai scale khác nhau (sx != sy),
  // nếu quay trực tiếp theo real yaw thì góc nhìn sẽ bị phóng đại.
  // Hàm này bù méo hình để góc hiển thị nhìn ra gần đúng với giá trị yaw thực.
  const a = realYawDeg * Math.PI / 180;
  return Math.atan((YAW_VIEW.sy / YAW_VIEW.sx) * Math.tan(a)) * 180 / Math.PI;
}

function spanAtDistance(poly, distM) {
  const xs = [];
  if (!poly || poly.length < 3) return null;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [x1, y1] = poly[j];
    const [x2, y2] = poly[i];
    if ((y1 <= distM && y2 >= distM) || (y2 <= distM && y1 >= distM)) {
      const dy = y2 - y1;
      if (Math.abs(dy) < 1e-9) {
        xs.push(x1, x2);
      } else {
        const t = (distM - y1) / dy;
        if (t >= -1e-6 && t <= 1 + 1e-6) xs.push(x1 + t * (x2 - x1));
      }
    }
  }
  if (xs.length < 2) return null;
  xs.sort((a, b) => a - b);
  return [xs[0], xs[xs.length - 1]];
}

function yawLocalToWorld(x, y, yawDeg) {
  const a = yawDeg * Math.PI / 180;
  const c = Math.cos(a), s = Math.sin(a);
  return {
    x: YAW_VIEW.ownLaneX + x * c + y * s,
    y: y * c - x * s,
  };
}

function worldToYawLocal(x, y, yawDeg) {
  const a = yawDeg * Math.PI / 180;
  const c = Math.cos(a), s = Math.sin(a);
  const dx = x - YAW_VIEW.ownLaneX;
  return {
    x: c * dx - s * y,
    y: s * dx + c * y,
  };
}

function screenPointFromWorld(x, y) {
  return {
    x: YAW_VIEW.x0 + x * YAW_VIEW.sx,
    y: YAW_VIEW.y0 - y * YAW_VIEW.sy,
  };
}

function screenPointFromLocal(x, y, yawDeg) {
  const w = yawLocalToWorld(x, y, yawDeg);
  return screenPointFromWorld(w.x, w.y);
}


function pathFromWorldPolyline(points, closed = false, smooth = true) {
  const pts = points.map(p => screenPointFromWorld(p.x, p.y));
  if (pts.length === 0) return '';
  if (!smooth || pts.length < 3) {
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + (closed ? ' Z' : '');
  }
  let d = `M${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
  }
  return d + (closed ? ' Z' : '');
}

function displayRoadCurvature(rawKappa) {
  if (!Number.isFinite(rawKappa)) return 0;
  const mag = Math.min(Math.abs(rawKappa) * YAW_VIEW.curveDisplayGain, YAW_VIEW.curveDisplayClamp);
  return Math.sign(rawKappa) * mag;
}

function roadPoseAtDistance(distanceM, roadKappa) {
  const k = Number.isFinite(roadKappa) ? roadKappa : 0;
  if (Math.abs(k) < 1e-9) {
    return { x: 0, y: distanceM, psi: 0, tx: 0, ty: 1, nx: 1, ny: 0 };
  }
  const psi = k * distanceM;
  return {
    x: (1 - Math.cos(psi)) / k,
    y: Math.sin(psi) / k,
    psi,
    tx: Math.sin(psi),
    ty: Math.cos(psi),
    nx: Math.cos(psi),
    ny: -Math.sin(psi),
  };
}

function roadWorldPoint(distanceM, offsetRightM, roadKappa) {
  const p = roadPoseAtDistance(distanceM, roadKappa);
  return {
    x: p.x + offsetRightM * p.nx,
    y: p.y + offsetRightM * p.ny,
    psi: p.psi,
    tx: p.tx,
    ty: p.ty,
    nx: p.nx,
    ny: p.ny,
  };
}

function sampleRoadPolyline(offsetRightM, roadKappa, stepM = 4) {
  const pts = [];
  for (let s = 0; s <= YAW_VIEW.roadLengthM; s += stepM) {
    pts.push(roadWorldPoint(s, offsetRightM, roadKappa));
  }
  if (pts[pts.length - 1].y < YAW_VIEW.roadLengthM - 0.01) {
    pts.push(roadWorldPoint(YAW_VIEW.roadLengthM, offsetRightM, roadKappa));
  }
  return pts;
}

function pathFromLocalPolyline(points, yawDeg, closed = false, smooth = true) {
  const pts = points.map(([x, y]) => screenPointFromLocal(x, y, yawDeg));
  if (pts.length === 0) return '';
  if (!smooth || pts.length < 3) {
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + (closed ? ' Z' : '');
  }
  let d = `M${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
  }
  return d + (closed ? ' Z' : '');
}

function pointInPolygon(point, polygon) {
  if (!polygon || polygon.length < 3) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1];
    const xj = polygon[j][0], yj = polygon[j][1];
    const intersect = ((yi > point.y) !== (yj > point.y)) &&
      (point.x < (xj - xi) * (point.y - yi) / ((yj - yi) || 1e-9) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function eyeBoxWorld(distanceM, roadKappa) {
  const pose = roadWorldPoint(distanceM, YAW_VIEW.oncomingLaneX, roadKappa);
  const halfW = 0.78;
  const forward = { x: -pose.tx, y: -pose.ty };
  const right = { x: pose.nx, y: pose.ny };
  const eyeCenter = {
    x: pose.x + forward.x * 1.0,
    y: pose.y + forward.y * 1.0,
  };
  return [
    { x: eyeCenter.x - right.x * halfW - forward.x * 0.35, y: eyeCenter.y - right.y * halfW - forward.y * 0.35 },
    { x: eyeCenter.x + right.x * halfW - forward.x * 0.35, y: eyeCenter.y + right.y * halfW - forward.y * 0.35 },
    { x: eyeCenter.x + right.x * halfW + forward.x * 0.35, y: eyeCenter.y + right.y * halfW + forward.y * 0.35 },
    { x: eyeCenter.x - right.x * halfW + forward.x * 0.35, y: eyeCenter.y - right.y * halfW + forward.y * 0.35 },
    eyeCenter,
  ];
}

function assessGlare(yawDeg, distanceM, roadKappa) {
  const eyeLocal = eyeBoxWorld(distanceM, roadKappa).map(p => worldToYawLocal(p.x, p.y, yawDeg));
  const centerLocal = eyeLocal[4];
  const eyeCenterHits = pointInPolygon(centerLocal, LOW_BEAM_MAIN_POLY);
  const eyeCornerHits = eyeLocal.slice(0, 4).some(p => pointInPolygon(p, LOW_BEAM_MAIN_POLY));

  const pose = roadWorldPoint(distanceM, YAW_VIEW.oncomingLaneX, roadKappa);
  const forward = { x: -pose.tx, y: -pose.ty };
  const right = { x: pose.nx, y: pose.ny };
  const bodyLocal = [
    { x: pose.x - right.x * 0.95 - forward.x * 1.8, y: pose.y - right.y * 0.95 - forward.y * 1.8 },
    { x: pose.x + right.x * 0.95 - forward.x * 1.8, y: pose.y + right.y * 0.95 - forward.y * 1.8 },
    { x: pose.x + right.x * 0.95 + forward.x * 0.4, y: pose.y + right.y * 0.95 + forward.y * 0.4 },
    { x: pose.x - right.x * 0.95 + forward.x * 0.4, y: pose.y - right.y * 0.95 + forward.y * 0.4 },
  ].map(p => worldToYawLocal(p.x, p.y, yawDeg));
  const bodyHits = bodyLocal.some(p => pointInPolygon(p, LOW_BEAM_MAIN_POLY));

  if (eyeCenterHits) {
    return { level: 'danger', text: `NGUY CƠ — vùng mắt xe đối diện nằm trong footprint chùm sáng tại ${distanceM} m` };
  }
  if (eyeCornerHits) {
    return { level: 'warn', text: `CẢNH BÁO — footprint đã chạm mép vùng mắt xe đối diện tại ${distanceM} m` };
  }
  if (bodyHits) {
    return { level: 'warn', text: `CẢNH BÁO — footprint đã chạm thân/kính xe đối diện tại ${distanceM} m` };
  }
  return { level: 'ok', text: `OK — vùng mắt xe đối diện nằm ngoài footprint chùm sáng tại ${distanceM} m` };
}

function vehicleSvg(xWorld, yWorld, direction, label, labelColor, rotationDeg = 0) {
  const w = YAW_VIEW.vehicleWidthM * YAW_VIEW.sx;
  const l = YAW_VIEW.vehicleLengthM * YAW_VIEW.sy;
  const c = screenPointFromWorld(xWorld, yWorld);
  const x = c.x - w / 2;
  const y = c.y - l / 2;
  const frontY = direction === 'up' ? y : y + l;
  const lampY = direction === 'up' ? y - 4 : y + l - 2;
  const labelY = direction === 'up' ? y + l + 16 : y + l + 28;
  const eyeY = direction === 'down' ? y + l - 11 : y + 11;
  return `
    <g transform="rotate(${rotationDeg.toFixed(2)} ${c.x.toFixed(1)} ${c.y.toFixed(1)})">
      <rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${l.toFixed(1)}" rx="5" fill="#1f2937" stroke="#93a4bb" stroke-width="1.7"/>
      <line x1="${(x + 10).toFixed(1)}" y1="${frontY.toFixed(1)}" x2="${(x + w - 10).toFixed(1)}" y2="${frontY.toFixed(1)}" stroke="#e5e7eb" stroke-width="1.1" opacity="0.65"/>
      <rect x="${(x + 8).toFixed(1)}" y="${lampY.toFixed(1)}" width="13" height="7" rx="2" fill="#f59e0b" opacity="0.95"/>
      <rect x="${(x + w - 21).toFixed(1)}" y="${lampY.toFixed(1)}" width="13" height="7" rx="2" fill="#f59e0b" opacity="0.95"/>
      ${direction === 'down' ? `<rect x="${(c.x - 17).toFixed(1)}" y="${eyeY.toFixed(1)}" width="34" height="6" rx="2" fill="none" stroke="#ef4444" stroke-width="1.2"/>` : ''}
    </g>
    <text x="${c.x.toFixed(1)}" y="${labelY.toFixed(1)}" text-anchor="middle" fill="${labelColor}" font-family="JetBrains Mono,monospace" font-size="12" font-weight="700">${label}</text>
  `;
}

function drawYawScene(yawDeg, pitchDeg, rawRoadKappa) {
  const drawYawDeg = yawDisplayDeg(yawDeg);
  const roadKappa = displayRoadCurvature(rawRoadKappa);

  const leftRoad = sampleRoadPolyline(-YAW_VIEW.laneWidthM, roadKappa);
  const rightRoad = sampleRoadPolyline(YAW_VIEW.laneWidthM, roadKappa);
  const roadCenter = sampleRoadPolyline(0, roadKappa);

  $('road-fill').setAttribute('d', pathFromWorldPolyline([...leftRoad, ...rightRoad.slice().reverse()], true, true));
  $('road-left-edge').setAttribute('d', pathFromWorldPolyline(leftRoad, false, true));
  $('road-right-edge').setAttribute('d', pathFromWorldPolyline(rightRoad, false, true));
  $('lane-center').setAttribute('d', pathFromWorldPolyline(roadCenter, false, true));

  const guideMarks = [20, 30, 60];
  $('road-distance-guides').innerHTML = guideMarks.map(m => {
    const left = roadWorldPoint(m, -YAW_VIEW.laneWidthM, roadKappa);
    const right = roadWorldPoint(m, YAW_VIEW.laneWidthM, roadKappa);
    const a = screenPointFromWorld(left.x, left.y);
    const b = screenPointFromWorld(right.x, right.y);
    return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}"/>`;
  }).join('');

  $('distance-scale').innerHTML = guideMarks.map(m => {
    const edge = roadWorldPoint(m, YAW_VIEW.laneWidthM, roadKappa);
    const tickStart = screenPointFromWorld(edge.x, edge.y);
    const tickMid = screenPointFromWorld(edge.x + edge.nx * 0.42, edge.y + edge.ny * 0.42);
    const textPt = screenPointFromWorld(edge.x + edge.nx * 0.78, edge.y + edge.ny * 0.78);
    return `
      <line x1="${tickStart.x.toFixed(1)}" y1="${tickStart.y.toFixed(1)}" x2="${tickMid.x.toFixed(1)}" y2="${tickMid.y.toFixed(1)}" stroke="#93a4bb" stroke-width="1"/>
      <text x="${textPt.x.toFixed(1)}" y="${(textPt.y + 4).toFixed(1)}">${m} m</text>
    `;
  }).join('');

  $('beam-main-shape').setAttribute('d', pathFromLocalPolyline(LOW_BEAM_MAIN_POLY, drawYawDeg, true, true));
  $('beam-far-shape').setAttribute('d', '');
  $('beam-cutoff-line').setAttribute('d', '');
  $('beam-axis-line').setAttribute('x1', '0');
  $('beam-axis-line').setAttribute('y1', '0');
  $('beam-axis-line').setAttribute('x2', '0');
  $('beam-axis-line').setAttribute('y2', '0');

  const markYs = [20, 30, 60];
  $('beam-marks').innerHTML = markYs.map(m => {
    const span = spanAtDistance(LOW_BEAM_MAIN_POLY, m);
    if (!span) return '';
    const a = screenPointFromLocal(span[0], m, drawYawDeg);
    const b = screenPointFromLocal(span[1], m, drawYawDeg);
    return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="#f4d35e" stroke-width="1.1" stroke-dasharray="4 4" opacity="0.92"/>`;
  }).join('');

  const ownPose = roadWorldPoint(-1.9, YAW_VIEW.ownLaneX, roadKappa);
  const oncomingPose = roadWorldPoint(selectedOncomingDistanceM, YAW_VIEW.oncomingLaneX, roadKappa);
  $('own-car').innerHTML = vehicleSvg(ownPose.x, ownPose.y, 'up', 'xe mình', '#cbd5e1', ownPose.psi * 180 / Math.PI);
  $('oncoming-car').innerHTML = vehicleSvg(oncomingPose.x, oncomingPose.y, 'down', 'xe đối diện', '#ef4444', oncomingPose.psi * 180 / Math.PI);

  // yaw arc: dùng cùng hệ trục màn hình để cung nhỏ không bị hiểu nhầm là footprint.
  const arcAnchor = roadWorldPoint(0, YAW_VIEW.ownLaneX, roadKappa);
  const cx = screenPointFromWorld(arcAnchor.x, arcAnchor.y).x;
  const cy = screenPointFromWorld(arcAnchor.x, arcAnchor.y).y;
  const r = 44;
  const a0 = -Math.PI / 2;
  const a1 = a0 + drawYawDeg * Math.PI / 180;
  if (Math.abs(yawDeg) > 0.05) {
    const s0 = { x: cx + r * Math.cos(a0), y: cy + r * Math.sin(a0) };
    const s1 = { x: cx + r * Math.cos(a1), y: cy + r * Math.sin(a1) };
    $('yaw-arc').setAttribute('d', `M${s0.x.toFixed(1)},${s0.y.toFixed(1)} A${r},${r} 0 0,${yawDeg >= 0 ? 1 : 0} ${s1.x.toFixed(1)},${s1.y.toFixed(1)}`);
  } else {
    $('yaw-arc').setAttribute('d', '');
  }
  $('yaw-angle-text').setAttribute('x', (cx + 72).toFixed(1));
  $('yaw-angle-text').setAttribute('y', (cy - 42).toFixed(1));
  $('yaw-angle-text').textContent = (yawDeg >= 0 ? '► ' : '◄ ') + Math.abs(yawDeg).toFixed(1) + '°';
  $('viz-pitch-badge').textContent = Math.abs(pitchDeg) > 0.001 ? (pitchDeg > 0 ? '▲' : '▼') + ' ' + Math.abs(pitchDeg).toFixed(2) + '°' : '';

  // Status text intentionally hidden to keep the top-view drawing clean.
  $('beam-status-text').textContent = '';
}

function send() {
  const body = {
    speed_kmh:            +$('s-speed').value,
    steering_wheel_deg:   +$('s-steer').value,
    front_height_mm:      +$('s-hf').value,
    rear_height_mm:       +$('s-hr').value,
    config:               getConfigBody(),
  };

  fetch('/api/compute', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  .then(r => r.json())
  .then(d => {
    if (!d.ok) {
      setStatus(d.error || 'Không thể tính với bộ tham số hiện tại', true);
      return;
    }

    const yaw   = d.yaw_angle_deg;
    const pitch = d.pitch_angle_deg;
    const dbg   = d.debug;

    // Gauges
    $('g-yaw').textContent   = (yaw >= 0 ? '+' : '') + yaw.toFixed(3);
    $('g-pitch').textContent = (pitch >= 0 ? '+' : '') + pitch.toFixed(3);

    // Top-view yaw + low-beam footprint
    drawYawScene(yaw, pitch, dbg.curvature_1pm);

    // Debug — Yaw
    $('d-fw').textContent     = dbg.front_wheel_deg.toFixed(3) + '°';
    $('d-kappa').textContent  = dbg.curvature_1pm.toFixed(6) + ' 1/m';
    $('d-tp').textContent     = dbg.preview_time_s.toFixed(3) + ' s';
    $('d-pd').textContent     = dbg.preview_distance_m.toFixed(2) + ' m';
    $('d-yt').textContent     = dbg.yaw_target_deg.toFixed(3) + '°';

    const kappa = dbg.curvature_1pm;
    const radius = Math.abs(kappa) > 1e-6 ? (1/Math.abs(kappa)).toFixed(1) + ' m' : '∞';
    $('d-radius').textContent = radius;
    $('d-vmps').textContent   = (body.speed_kmh / 3.6).toFixed(2) + ' m/s';

    // Debug — Pitch
    $('d-dhf').textContent    = (dbg.dh_front_mm >= 0 ? '+' : '') + dbg.dh_front_mm.toFixed(1) + ' mm';
    $('d-dhr').textContent    = (dbg.dh_rear_mm >= 0 ? '+' : '') + dbg.dh_rear_mm.toFixed(1) + ' mm';
    $('d-pb').textContent     = (dbg.pitch_body_deg >= 0 ? '+' : '') + dbg.pitch_body_deg.toFixed(4) + '°';
    $('d-pt').textContent     = (dbg.pitch_target_deg >= 0 ? '+' : '') + dbg.pitch_target_deg.toFixed(4) + '°';
    $('d-po').textContent     = (pitch >= 0 ? '+' : '') + pitch.toFixed(3) + '°';
    $('d-hf-abs').textContent = body.front_height_mm + ' mm';
    $('d-hr-abs').textContent = body.rear_height_mm + ' mm';

    // Side view — pitch SVG visualization
    const bodyDeg = dbg.pitch_body_deg;
    const pitchDeg = pitch;

    // Car body tilts — pivot at rear axle (x=235, y=290)
    const bodyVizAngle = -bodyDeg * 3;
    $('pitch-car-group').setAttribute('transform', `rotate(${bodyVizAngle.toFixed(2)} 235 290)`);

    // Beam tilts independently — pivot at headlamp (x=264, y=277)
    const beamVizAngle = -pitchDeg * 5;
    $('pitch-beam-group').setAttribute('transform', `rotate(${beamVizAngle.toFixed(2)} 264 277)`);

    // Labels
    const pitchSign = pitchDeg >= 0 ? '+' : '';
    const bodySign = bodyDeg >= 0 ? '+' : '';
    $('pitch-lamp-text').textContent = 'Đèn: ' + pitchSign + pitchDeg.toFixed(3) + '°';
    $('pitch-body-text').textContent = 'Thân: ' + bodySign + bodyDeg.toFixed(4) + '°';

    // Δh indicators
    const dhf = dbg.dh_front_mm;
    const dhr = dbg.dh_rear_mm;
    $('dh-front-text').textContent = 'Δf: ' + (dhf >= 0 ? '+' : '') + dhf.toFixed(0);
    $('dh-rear-text').textContent = 'Δr: ' + (dhr >= 0 ? '+' : '') + dhr.toFixed(0);
    setStatus(DEFAULT_STATUS);
  })
  .catch(() => {
    setStatus('Không gọi được API /api/compute', true);
  });
}

INPUT_FIELDS.forEach(({ slider, number }) => {
  $(slider).addEventListener('input', () => {
    syncNumberFromSlider(slider);
    queueSend({ clearPreset: true });
  });

  $(number).addEventListener('input', () => {
    const raw = $(number).value.trim();
    if (raw === '' || raw === '-' || raw === '+' || raw === '.' || raw === '-.' || raw === '+.') return;
    if (setInputPair(slider, raw) !== null) {
      queueSend({ clearPreset: true });
    }
  });

  $(number).addEventListener('change', () => {
    const fallback = $(slider).value;
    const raw = $(number).value.trim();
    if (setInputPair(slider, raw) === null) {
      $(number).value = fallback;
      return;
    }
    queueSend({ clearPreset: true });
  });
});

CONFIG_FIELDS.forEach(({ id }) => {
  $(id).addEventListener('change', () => {
    queueSend();
  });
});

$('btn-reset').addEventListener('click', () => {
  clearTimeout(timer);
  clearPresetHighlight();
  Object.entries(DEFAULT_INPUTS).forEach(([id, value]) => {
    $(id).value = value;
  });
  syncAllNumberInputs();
  send();
});

$('btn-reset-config').addEventListener('click', () => {
  clearTimeout(timer);
  setConfigInputs(DEFAULT_CONFIG);
  send();
});

window.addEventListener('resize', syncVizCardHeights);
window.addEventListener('load', syncVizCardHeights);
if (window.ResizeObserver && controlsColumn) {
  new ResizeObserver(syncVizCardHeights).observe(controlsColumn);
}
if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(syncVizCardHeights);
}

// Initial
setConfigInputs(DEFAULT_CONFIG);
syncAllNumberInputs();
syncVizCardHeights();
send();
</script>
</body>
</html>"""

DASHBOARD_HTML = DASHBOARD_HTML.replace(
    "__DEFAULT_CONFIG_JSON__",
    json.dumps(asdict(DEFAULT_CONFIG), ensure_ascii=False),
)


# ── Routes ───────────────────────────────────────────────────

def build_config(raw_config) -> AFSConfig:
    if raw_config is None:
        return AFSConfig()
    if not isinstance(raw_config, dict):
        raise ValueError("config phải là object JSON")

    unknown_fields = sorted(set(raw_config) - set(CONFIG_FIELD_NAMES))
    if unknown_fields:
        raise ValueError(f"Field config không hợp lệ: {', '.join(unknown_fields)}")

    values = {}
    for field_name in CONFIG_FIELD_NAMES:
        raw_value = raw_config.get(field_name, getattr(DEFAULT_CONFIG, field_name))
        if raw_value in (None, ""):
            raw_value = getattr(DEFAULT_CONFIG, field_name)

        try:
            values[field_name] = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(f"Giá trị không hợp lệ cho `{field_name}`") from None

    return AFSConfig(**values)

@app.route("/")
def index():
    return DASHBOARD_HTML


@app.route("/api/compute", methods=["POST"])
def compute():
    """
    Nhận input từ dashboard, gọi afs thật, trả JSON.

    Request body (JSON):
        speed_kmh, steering_wheel_deg, front_height_mm, rear_height_mm

    Response (JSON):
        ok, yaw_angle_deg, pitch_angle_deg, debug
    """
    data = request.get_json(force=True)

    try:
        speed = float(data.get("speed_kmh", 0))
        steer = float(data.get("steering_wheel_deg", 0))
        hf    = float(data.get("front_height_mm", 350))
        hr    = float(data.get("rear_height_mm", 350))
        cfg   = build_config(data.get("config"))

        controller = AFSController(cfg)
        out = controller.evaluate_static(
            speed_kmh=speed,
            steering_wheel_deg=steer,
            front_height_mm=hf,
            rear_height_mm=hr,
            dt=0.02,
        )

        return jsonify({
            "ok": True,
            "yaw_angle_deg": out.yaw_angle_deg,
            "pitch_angle_deg": out.pitch_angle_deg,
            "debug": {
                "front_wheel_deg": out.front_wheel_deg,
                "curvature_1pm": out.curvature_1pm,
                "preview_time_s": out.preview_time_s,
                "preview_distance_m": out.preview_distance_m,
                "yaw_target_deg": out.yaw_target_deg,
                "pitch_body_deg": out.pitch_body_deg,
                "dh_front_mm": out.dh_front_mm,
                "dh_rear_mm": out.dh_rear_mm,
                "pitch_target_deg": out.pitch_target_deg,
            },
        })

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Lỗi: {e}"}), 500


if __name__ == "__main__":
    print()
    print("=" * 52)
    print("  AFS Dashboard")
    print("  http://localhost:5000")
    print("=" * 52)
    print()
    app.run(debug=True, port=5000)
