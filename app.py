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
    </div>

    <!-- MIDDLE COLUMN: Yaw visualization -->
    <div class="card viz-card">
      <div class="car-viz">
        <div class="viz-title">Nhìn trên — Yaw</div>
        <svg id="yaw-svg" class="viz-svg" viewBox="70 15 260 390">
          <defs>
            <radialGradient id="beam-grad" cx="50%" cy="100%" r="70%" fx="50%" fy="100%">
              <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.5"/>
              <stop offset="60%" stop-color="#22d3ee" stop-opacity="0.15"/>
              <stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <g id="beam-left-group">
            <path id="beam-left-fan" d="" fill="url(#beam-grad)" opacity="0.5"/>
            <line id="beam-left-center" x1="188" y1="361" x2="188" y2="30" stroke="#22d3ee" stroke-width="0.9" stroke-dasharray="6 4" opacity="0.45"/>
          </g>
          <g id="beam-right-group">
            <path id="beam-right-fan" d="" fill="url(#beam-grad)" opacity="0.5"/>
            <line id="beam-right-center" x1="212" y1="361" x2="212" y2="30" stroke="#22d3ee" stroke-width="0.9" stroke-dasharray="6 4" opacity="0.45"/>
          </g>
          <path id="yaw-arc" d="" fill="none" stroke="#22d3ee" stroke-width="1.5" opacity="0.7"/>
          <text id="yaw-angle-text" x="200" y="240" text-anchor="middle" fill="#22d3ee" font-family="JetBrains Mono,monospace" font-size="18" font-weight="600" opacity="0.9"></text>
          <text id="yaw-arrow" x="200" y="224" text-anchor="middle" fill="#22d3ee" font-family="JetBrains Mono,monospace" font-size="14" opacity="0.7"></text>
          <line x1="200" y1="380" x2="200" y2="30" stroke="#6b7a8d" stroke-width="0.5" stroke-dasharray="3 6" opacity="0.3"/>
          <rect x="178" y="362" width="44" height="30" rx="4" fill="none" stroke="#6b7a8d" stroke-width="1.5"/>
          <rect x="183" y="358" width="10" height="6" rx="2" fill="#f59e0b" opacity="0.8"/>
          <rect x="207" y="358" width="10" height="6" rx="2" fill="#f59e0b" opacity="0.8"/>
          <line x1="120" y1="30" x2="120" y2="400" stroke="#6b7a8d" stroke-width="0.5" stroke-dasharray="8 8" opacity="0.15"/>
          <line x1="280" y1="30" x2="280" y2="400" stroke="#6b7a8d" stroke-width="0.5" stroke-dasharray="8 8" opacity="0.15"/>
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
  { name: 'Đi thẳng 60 km/h',      speed: 60,  steer:    0, hf: 350, hr: 350 },
  { name: 'Rẽ phải vừa (40 km/h)',  speed: 40,  steer:   20, hf: 350, hr: 350 },
  { name: 'Rẽ trái gắt (40 km/h)',  speed: 40,  steer: -40, hf: 350, hr: 350 },
  { name: 'Cao tốc, chỉnh làn',       speed: 100, steer:   8, hf: 350, hr: 350 },
  { name: 'Tải nặng phía sau',      speed: 50,  steer:   0, hf: 345, hr: 370 },
  { name: 'Phanh gấp (đầu chúi)',   speed: 50,  steer:   0, hf: 365, hr: 340 },
  { name: 'Đỗ xe, cua rất gấp',     speed: 3,   steer:  220, hf: 350, hr: 350 },
];

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

    // Beam visualization — two headlamp beams in top view
    const beamLen = 340;
    const halfSpread = 14;
    const yawRad = yaw * Math.PI / 180;
    const baseAngle = -Math.PI / 2; // pointing up
    const beamCenter = baseAngle + yawRad;
    const a1 = beamCenter - halfSpread * Math.PI / 180;
    const a2 = beamCenter + halfSpread * Math.PI / 180;

    [
      { fanId: 'beam-left-fan', lineId: 'beam-left-center', ox: 188, oy: 361 },
      { fanId: 'beam-right-fan', lineId: 'beam-right-center', ox: 212, oy: 361 },
    ].forEach(({ fanId, lineId, ox, oy }) => {
      const x1 = ox + beamLen * Math.cos(a1);
      const y1 = oy + beamLen * Math.sin(a1);
      const x2 = ox + beamLen * Math.cos(a2);
      const y2 = oy + beamLen * Math.sin(a2);
      const lx = ox + beamLen * Math.cos(beamCenter);
      const ly = oy + beamLen * Math.sin(beamCenter);

      $(fanId).setAttribute(
        'd',
        `M${ox},${oy} L${x1.toFixed(1)},${y1.toFixed(1)} A${beamLen},${beamLen} 0 0,1 ${x2.toFixed(1)},${y2.toFixed(1)} Z`
      );
      $(lineId).setAttribute('x1', ox.toFixed(1));
      $(lineId).setAttribute('y1', oy.toFixed(1));
      $(lineId).setAttribute('x2', lx.toFixed(1));
      $(lineId).setAttribute('y2', ly.toFixed(1));
    });

    // Angle arc
    const cx = 200, cy = 380;
    const arcR = 100;
    const arcA1 = -Math.PI / 2;
    const arcA2 = -Math.PI / 2 + yawRad;
    if (Math.abs(yaw) > 0.1) {
      const ax1 = cx + arcR * Math.cos(arcA1);
      const ay1 = cy + arcR * Math.sin(arcA1);
      const ax2 = cx + arcR * Math.cos(arcA2);
      const ay2 = cy + arcR * Math.sin(arcA2);
      const sweep = yaw > 0 ? 1 : 0;
      $('yaw-arc').setAttribute('d', `M${ax1.toFixed(1)},${ay1.toFixed(1)} A${arcR},${arcR} 0 0,${sweep} ${ax2.toFixed(1)},${ay2.toFixed(1)}`);
    } else {
      $('yaw-arc').setAttribute('d', '');
    }

    // Angle text
    const labelR = 105;
    const labelA = -Math.PI / 2 + yawRad / 2;
    const lx = cx + labelR * Math.cos(labelA);
    const ly = cy + labelR * Math.sin(labelA);
    $('yaw-angle-text').setAttribute('x', lx.toFixed(0));
    $('yaw-angle-text').setAttribute('y', ly.toFixed(0));
    $('yaw-angle-text').textContent = Math.abs(yaw) > 0.01 ? (yaw > 0 ? '► ' : '◄ ') + Math.abs(yaw).toFixed(1) + '°' : '0°';

    // Arrow indicator
    $('yaw-arrow').setAttribute('x', lx.toFixed(0));
    $('yaw-arrow').setAttribute('y', (ly - 16).toFixed(0));
    $('yaw-arrow').textContent = '';

    // Pitch badge on yaw viz
    $('viz-pitch-badge').textContent = Math.abs(pitch) > 0.001 ? (pitch > 0 ? '▲' : '▼') + ' ' + Math.abs(pitch).toFixed(2) + '°' : '';

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
