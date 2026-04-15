#!/usr/bin/env python3
"""Cover Maker Web GUI — python3 app.py 启动，浏览器自动打开"""

import os, sys, io, base64, threading, webbrowser, tempfile, json
from flask import Flask, request, jsonify, render_template_string
from PIL import Image

# 加载 .env（本地开发用，线上环境变量由 Railway/服务器直接注入）
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(__file__))
from make_cover import make_cover, PRESETS
from make_pdfagile_cover import make_pdfagile_cover
from make_howtotips2_cover import make_howtotips2_cover
import localize_agent

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cover Maker — PDF Agile Tools</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:            #f5f4ed;
  --ivory:         #faf9f5;
  --white:         #ffffff;
  --warm-sand:     #e8e6dc;
  --dark-surface:  #30302e;
  --near-black:    #141413;
  --terracotta:    #c96442;
  --coral:         #d97757;
  --text-primary:  #141413;
  --text-secondary:#5e5d59;
  --text-tertiary: #87867f;
  --text-warm-mid: #4d4c48;
  --border-cream:  #f0eee6;
  --border-warm:   #e8e6dc;
  --ring-warm:     #d1cfc5;
  --ring-deep:     #c2c0b6;
  --green:         #3a8a52;
  --green-bg:      rgba(58,138,82,0.08);
  --focus-blue:    #3898ec;
  --serif:  'Lora', Georgia, serif;
  --sans:   'Inter', -apple-system, sans-serif;
  --r-sm:   8px;
  --r-md:   12px;
  --r-lg:   16px;
}
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }
body { background: var(--bg); color: var(--text-primary); font-family: var(--sans); min-height: 100vh; display: flex; flex-direction: column; }

/* ── Nav ── */
.top-nav {
  background: rgba(245,244,237,0.92);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-cream);
  padding: 0 28px; display: flex; align-items: center; height: 52px;
  position: sticky; top: 0; z-index: 100; flex-shrink: 0;
}
.nav-logo { font-family: var(--serif); font-size: 15px; font-weight: 500; color: var(--text-primary); text-decoration: none; margin-right: 6px; }
.nav-sep { color: var(--border-warm); margin: 0 2px; font-size: 16px; }
.nav-link { display: flex; align-items: center; height: 100%; padding: 0 14px; font-size: 15px; font-weight: 400; color: var(--text-secondary); text-decoration: none; position: relative; transition: color .15s; }
.nav-link:hover { color: var(--text-primary); }
.nav-link.active { color: var(--terracotta); font-weight: 500; }
.nav-link.active::after { content: ''; position: absolute; bottom: 0; left: 14px; right: 14px; height: 2px; background: var(--terracotta); border-radius: 2px 2px 0 0; }

/* ── Layout ── */
.layout { display: flex; flex: 1; min-height: 0; }
.sidebar {
  width: 300px; min-width: 300px;
  background: var(--ivory);
  border-right: 1px solid var(--border-cream);
  padding: 24px 20px;
  display: flex; flex-direction: column; gap: 16px;
  overflow-y: auto;
}
.sidebar-title { font-family: var(--serif); font-size: 22px; font-weight: 500; color: var(--text-primary); letter-spacing: 0; }

label { font-size: 13px; font-weight: 500; color: var(--text-secondary); display: block; margin-bottom: 6px; font-family: var(--sans); }
input[type=text], textarea {
  width: 100%; background: var(--white); border: 1px solid var(--border-warm);
  border-radius: var(--r-md); color: var(--text-primary); padding: 8px 10px;
  font-size: 14px; font-family: var(--sans); outline: none;
  transition: border-color .15s, box-shadow .15s;
}
input[type=text]:focus, textarea:focus { border-color: var(--focus-blue); box-shadow: 0 0 0 3px rgba(56,152,236,0.15); }
textarea { resize: vertical; min-height: 80px; }

/* ── Segmented control ── */
.seg-ctrl { display: flex; background: var(--warm-sand); border-radius: var(--r-sm); padding: 3px; gap: 2px; }
.seg-btn { flex: 1; padding: 7px 6px; border: none; border-radius: 6px; background: transparent; color: var(--text-tertiary); font-size: 12px; font-weight: 500; font-family: var(--sans); cursor: pointer; transition: all .15s; text-align: center; }
.seg-btn.active { background: var(--ivory); color: var(--text-primary); box-shadow: rgba(0,0,0,0.06) 0px 1px 3px; font-weight: 600; }

/* ── Color swatches ── */
.color-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.color-swatch { width: 30px; height: 30px; border-radius: 7px; cursor: pointer; border: 2px solid transparent; transition: transform .1s, box-shadow .15s; }
.color-swatch:hover { transform: scale(1.12); }
.color-swatch.active { box-shadow: 0 0 0 2px var(--ivory), 0 0 0 4px var(--terracotta); }
.hex-row { display: flex; gap: 8px; align-items: center; }
.hex-prefix { color: var(--text-tertiary); font-size: 14px; }
.hex-row input { width: 90px; }
.color-label { font-size: 11px; color: var(--text-tertiary); margin-top: 4px; }

.btn-sm { background: var(--warm-sand); color: var(--text-warm-mid); border: none; box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-warm) 0px 0px 0px 1px; border-radius: var(--r-sm); padding: 8px 14px; font-size: 13px; font-weight: 500; font-family: var(--sans); cursor: pointer; transition: all .15s; white-space: nowrap; }
.btn-sm:hover { box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-deep) 0px 0px 0px 1px; color: var(--text-primary); }

/* ── Drop zone ── */
.drop-zone {
  border: 1.5px dashed var(--border-warm); border-radius: var(--r-md);
  padding: 16px; text-align: center; color: var(--text-tertiary); font-size: 13px;
  cursor: pointer; transition: all .15s; background: var(--white);
}
.drop-zone:hover { border-color: var(--terracotta); color: var(--terracotta); background: rgba(201,100,66,0.04); }
.drop-zone.dragover { border-color: var(--terracotta); color: var(--terracotta); background: rgba(201,100,66,0.04); }
.drop-zone.has-file { border-color: rgba(58,138,82,0.35); color: var(--green); background: var(--green-bg); }

/* ── Section toggle ── */
.section { display: none; flex-direction: column; gap: 14px; }
.section.active { display: flex; }
.divider { height: 1px; background: var(--border-cream); margin: 2px 0; }

/* ── Pdfagile info ── */
.mode-info { font-size: 13px; color: var(--text-secondary); line-height: 1.7; background: rgba(201,100,66,0.06); border-radius: var(--r-sm); padding: 12px 14px; }

/* ── Buttons ── */
.btn-main {
  background: var(--terracotta); color: var(--ivory); border: none; border-radius: var(--r-md);
  padding: 12px; font-size: 15px; font-weight: 600; font-family: var(--sans);
  cursor: pointer; width: 100%;
  box-shadow: var(--terracotta) 0px 0px 0px 0px, var(--terracotta) 0px 0px 0px 1px;
  transition: box-shadow .15s, transform .1s, background .15s;
}
.btn-main:hover:not(:disabled) { background: #b8573a; box-shadow: var(--terracotta) 0px 0px 0px 0px, #a84e33 0px 0px 0px 1px; transform: translateY(-1px); }
.btn-main:active:not(:disabled) { transform: translateY(0); }
.btn-main:disabled { background: var(--warm-sand); color: var(--text-tertiary); cursor: not-allowed; box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-warm) 0px 0px 0px 1px; }

.btn-dl {
  background: var(--warm-sand); color: var(--text-warm-mid); border: none;
  box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-warm) 0px 0px 0px 1px;
  border-radius: var(--r-md); padding: 10px; font-size: 13px; font-weight: 500;
  font-family: var(--sans); cursor: pointer; width: 100%; transition: all .15s;
}
.btn-dl:hover:not(:disabled) { box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-deep) 0px 0px 0px 1px; color: var(--text-primary); }
.btn-dl:disabled { opacity: .4; cursor: not-allowed; }

/* ── Status ── */
.status { font-size: 12px; color: var(--text-tertiary); line-height: 1.6; min-height: 28px; }
.status.ok  { color: var(--green); }
.status.err { color: #b53333; }

/* ── Preview ── */
.preview-area {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: var(--warm-sand); position: relative;
  background-image: radial-gradient(circle at 1px 1px, var(--ring-warm) 1px, transparent 0);
  background-size: 20px 20px;
}
.preview-area img { max-width: 100%; max-height: calc(100vh - 52px); object-fit: contain; display: block; border-radius: 8px; box-shadow: rgba(0,0,0,0.12) 0px 8px 32px; }
.preview-placeholder { color: var(--text-tertiary); font-size: 15px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.preview-placeholder-icon { font-size: 40px; opacity: .35; }
.spinner { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); }
.spinner.show { display: block; }
@keyframes spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
.spinner svg { animation: spin 1s linear infinite; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-warm); border-radius: 3px; }
</style>
</head>
<body>

<nav class="top-nav">
  <a href="/" class="nav-logo">PDF Agile Tools</a>
  <span class="nav-sep">/</span>
  <a href="/" class="nav-link active">Cover Maker</a>
  <a href="/auto-publish" class="nav-link">Auto Publish</a>
  <a href="/localize" class="nav-link">Localize</a>
</nav>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-title">Cover Maker</div>

    <div>
      <label>模式</label>
      <div class="seg-ctrl">
        <button class="seg-btn active" onclick="switchMode('tutorial', this)">HowToTips</button>
        <button class="seg-btn" onclick="switchMode('pdfagile', this)">Templates</button>
        <button class="seg-btn" onclick="switchMode('howtotips2', this)">Blog</button>
      </div>
    </div>

    <div class="divider"></div>

    <div>
      <label>图片</label>
      <div class="drop-zone" id="dropZone">
        <div style="font-size:20px;margin-bottom:4px;opacity:.4">↑</div>
        拖入图片或点击选择
      </div>
      <input type="file" id="fileInput" accept="image/*" style="display:none">
    </div>

    <div>
      <label>标题</label>
      <textarea id="titleInput" placeholder="How to Add Slide Numbers..."></textarea>
    </div>

    <div class="section active" id="section-tutorial">
      <div>
        <label>背景颜色</label>
        <div class="color-grid" id="colorGrid"></div>
        <div class="color-label" id="colorLabel">Teal #4A8FA0</div>
      </div>
      <div>
        <label>自定义颜色</label>
        <div class="hex-row">
          <span class="hex-prefix">#</span>
          <input type="text" id="hexInput" placeholder="3D7A8A" maxlength="6">
          <button class="btn-sm" onclick="applyHex()">应用</button>
        </div>
      </div>
    </div>

    <div class="section" id="section-pdfagile">
      <div class="mode-info">背景使用 PDF Agile 品牌模板<br>上传模板截图 + 填标题即可生成</div>
    </div>

    <div class="section" id="section-howtotips2">
      <div>
        <label>颜色模板</label>
        <div class="color-grid" id="colorGrid2"></div>
        <div class="color-label" id="colorLabel2">青绿</div>
      </div>
    </div>

    <div class="divider"></div>

    <button class="btn-main" id="genBtn" onclick="generate()" disabled>生成封面</button>
    <button class="btn-dl" id="downloadBtn" onclick="downloadFile()" disabled>下载封面图</button>
    <div class="status" id="status">拖入图片开始</div>
  </div>

  <div class="preview-area">
    <div class="preview-placeholder" id="placeholder">
      <div class="preview-placeholder-icon">🖼</div>
      预览区
    </div>
    <img id="previewImg" style="display:none" alt="preview">
    <div class="spinner" id="spinner">
      <svg width="40" height="40" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="16" fill="none" stroke="#c96442" stroke-width="3.5"
                stroke-dasharray="60 40" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
</div>

<script>
const COLORS = {{ colors|tojson }};
const COLORS2 = {{ colors2|tojson }};
let selectedColor = 'teal';
let selectedFile = null;
let outputB64 = null;
let outputFilename = null;
let previewTimer = null;
let currentMode = 'tutorial';

// 色块 (HowToTips)
const grid = document.getElementById('colorGrid');
COLORS.forEach(([label, key, hex]) => {
  const s = document.createElement('div');
  s.className = 'color-swatch' + (key === 'teal' ? ' active' : '');
  s.style.background = hex;
  s.title = label;
  s.onclick = () => selectColor(key, label, hex, s);
  grid.appendChild(s);
});

// 色块 (HowToTips 2) — 模板选择
let selectedTemplate2 = 'teal';
const grid2 = document.getElementById('colorGrid2');
COLORS2.forEach(([label, key, bgHex]) => {
  const s = document.createElement('div');
  s.className = 'color-swatch' + (key === 'teal' ? ' active' : '');
  s.style.background = bgHex;
  s.title = label;
  s.onclick = () => selectTemplate2(key, label, s);
  grid2.appendChild(s);
});

function selectTemplate2(key, label, el) {
  selectedTemplate2 = key;
  document.querySelectorAll('#colorGrid2 .color-swatch').forEach(s => s.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('colorLabel2').textContent = label;
  schedulePreview();
}

function selectColor(key, label, hex, el) {
  selectedColor = key;
  document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('colorLabel').textContent = label + '  ' + hex;
  schedulePreview();
}

function applyHex() {
  const val = document.getElementById('hexInput').value.trim().replace('#','');
  if (/^[0-9a-fA-F]{6}$/.test(val)) {
    selectedColor = '#' + val;
    document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
    document.getElementById('colorLabel').textContent = '#' + val;
    schedulePreview();
  }
}

function switchMode(mode, btn) {
  currentMode = mode;
  document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById('section-' + mode).classList.add('active');
  schedulePreview();
}

// 拖拽
const dropZone = document.getElementById('dropZone');
dropZone.onclick = () => document.getElementById('fileInput').click();
dropZone.ondragover = e => { e.preventDefault(); dropZone.classList.add('dragover'); };
dropZone.ondragleave = () => dropZone.classList.remove('dragover');
dropZone.ondrop = e => {
  e.preventDefault(); dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) loadFile(file);
};
document.getElementById('fileInput').onchange = e => { if (e.target.files[0]) loadFile(e.target.files[0]); };

function loadFile(file) {
  // 压缩图片到 2MB 以内再存储，避免 Vercel 413
  const MAX_BYTES = 2 * 1024 * 1024;
  if (file.size <= MAX_BYTES) {
    selectedFile = file;
    dropZone.innerHTML = '<div style="font-size:16px;margin-bottom:2px">✓</div>' + file.name;
    dropZone.classList.add('has-file');
    checkReady(); schedulePreview();
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    const img = new window.Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      let w = img.width, h = img.height;
      const scale = Math.sqrt(MAX_BYTES / file.size) * 0.9;
      w = Math.round(w * scale); h = Math.round(h * scale);
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      canvas.toBlob(blob => {
        selectedFile = new File([blob], file.name, { type: 'image/jpeg' });
        dropZone.innerHTML = '<div style="font-size:16px;margin-bottom:2px">✓</div>' + file.name + ' (已压缩)';
        dropZone.classList.add('has-file');
        checkReady(); schedulePreview();
      }, 'image/jpeg', 0.85);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

document.getElementById('titleInput').oninput = () => { checkReady(); schedulePreview(); };

function checkReady() {
  const ready = selectedFile && document.getElementById('titleInput').value.trim();
  document.getElementById('genBtn').disabled = !ready;
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(doPreview, 600);
}

function doPreview() {
  if (!selectedFile || !document.getElementById('titleInput').value.trim()) return;
  const fd = buildFormData(true);
  showSpinner(true);
  fetch('/generate', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      showSpinner(false);
      if (d.preview) showPreview(d.preview);
    })
    .catch(() => showSpinner(false));
}

function generate() {
  if (!selectedFile || !document.getElementById('titleInput').value.trim()) return;
  const btn = document.getElementById('genBtn');
  btn.disabled = true; btn.textContent = '生成中…';
  setStatus('正在生成…', '');
  fetch('/generate', { method: 'POST', body: buildFormData(false) })
    .then(r => r.json())
    .then(d => {
      btn.disabled = false; btn.textContent = '生成封面';
      if (d.error) { setStatus('失败：' + d.error, 'err'); return; }
      outputB64 = d.preview; outputFilename = d.filename;
      document.getElementById('downloadBtn').disabled = false;
      setStatus('✓ 生成完成：' + d.filename, 'ok');
      showPreview(d.preview);
    })
    .catch(e => { btn.disabled = false; btn.textContent = '生成封面'; setStatus('请求失败', 'err'); });
}

function buildFormData(isPreview) {
  const fd = new FormData();
  fd.append('image', selectedFile);
  fd.append('title', document.getElementById('titleInput').value.trim());
  fd.append('mode', currentMode);
  fd.append('color', selectedColor);
  fd.append('template', selectedTemplate2);
  if (isPreview) fd.append('preview', '1');
  return fd;
}

function showPreview(b64) {
  document.getElementById('placeholder').style.display = 'none';
  const img = document.getElementById('previewImg');
  img.src = 'data:image/png;base64,' + b64;
  img.style.display = 'block';
}

function downloadFile() {
  if (!outputB64 || !outputFilename) return;
  const a = document.createElement('a');
  a.href = 'data:image/png;base64,' + outputB64;
  a.download = outputFilename;
  a.click();
}

function setStatus(msg, cls) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + cls;
}
function showSpinner(show) {
  document.getElementById('spinner').classList.toggle('show', show);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    colors = [(label, key, PRESETS[key]) for label, key in [
        ("Teal 蓝绿", "teal"), ("Tan 米棕", "tan"), ("Navy 深蓝", "navy"),
        ("Olive 橄榄", "olive"), ("Rose 玫瑰", "rose"),
        ("Slate 石板", "slate"), ("Warm 暖棕", "warm"),
    ]]
    colors2 = [
        ("青绿", "teal",   "#84DCD4"),
        ("粉色", "pink",   "#FFC0E5"),
        ("橙黄", "orange", "#FFD272"),
        ("薄荷", "mint",   "#D5FFEC"),
        ("暖黄", "warm",   "#FFBE4C"),
    ]
    return render_template_string(HTML, colors=colors, colors2=colors2)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        file       = request.files["image"]
        title      = request.form["title"]
        mode       = request.form.get("mode", "tutorial")
        color      = request.form.get("color", "teal")
        template   = request.form.get("template", "pink")
        is_preview = request.form.get("preview") == "1"

        suffix = os.path.splitext(file.filename)[1] or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            file.save(tmp_in.name)
            tmp_in_path = tmp_in.name

        out_fd, out_path = tempfile.mkstemp(suffix=".png")
        os.close(out_fd)
        base = os.path.splitext(file.filename)[0]

        if mode == "pdfagile":
            make_pdfagile_cover(tmp_in_path, title, output_path=out_path)
            filename = base + "_pdfagile_cover.png"
        elif mode == "howtotips2":
            make_howtotips2_cover(tmp_in_path, title, template, output_path=out_path)
            filename = base + "_ht2_cover.png"
        else:
            make_cover(tmp_in_path, title, color, output_path=out_path)
            filename = base + "_cover.png"

        os.unlink(tmp_in_path)

        with open(out_path, "rb") as f:
            full_bytes = f.read()

        img = Image.open(out_path)
        img.thumbnail((800, 600), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        preview_b64 = base64.b64encode(buf.getvalue()).decode()
        os.unlink(out_path)

        if is_preview:
            return jsonify({"preview": preview_b64})

        full_b64 = base64.b64encode(full_bytes).decode()
        return jsonify({"filename": filename, "preview": full_b64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

AUTO_PUBLISH_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auto Publish — PDF Agile Tools</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:            #f5f4ed;
  --ivory:         #faf9f5;
  --white:         #ffffff;
  --warm-sand:     #e8e6dc;
  --dark-surface:  #30302e;
  --near-black:    #141413;
  --terracotta:    #c96442;
  --coral:         #d97757;
  --text-primary:  #141413;
  --text-secondary:#5e5d59;
  --text-tertiary: #87867f;
  --text-warm-mid: #4d4c48;
  --warm-silver:   #b0aea5;
  --border-cream:  #f0eee6;
  --border-warm:   #e8e6dc;
  --border-dark:   #30302e;
  --ring-warm:     #d1cfc5;
  --ring-deep:     #c2c0b6;
  --green:         #3a8a52;
  --green-bg:      rgba(58,138,82,0.08);
  --red:           #b53333;
  --red-bg:        rgba(181,51,51,0.08);
  --focus-blue:    #3898ec;
  --serif:  'Lora', Georgia, serif;
  --sans:   'Inter', -apple-system, sans-serif;
  --mono:   'SF Mono', 'Fira Code', Menlo, monospace;
  --r-sm:   8px;
  --r-md:   12px;
  --r-lg:   16px;
}
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }
body { background: var(--bg); color: var(--text-primary); font-family: var(--sans); min-height: 100vh; display: flex; flex-direction: column; }

/* ── Nav ── */
.top-nav {
  background: rgba(245,244,237,0.92);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-cream);
  padding: 0 28px; display: flex; align-items: center; height: 52px;
  position: sticky; top: 0; z-index: 100; flex-shrink: 0;
}
.nav-logo { font-family: var(--serif); font-size: 15px; font-weight: 500; color: var(--text-primary); text-decoration: none; margin-right: 6px; }
.nav-sep { color: var(--border-warm); margin: 0 2px; font-size: 16px; }
.nav-link { display: flex; align-items: center; height: 100%; padding: 0 14px; font-size: 15px; font-weight: 400; color: var(--text-secondary); text-decoration: none; position: relative; transition: color .15s; }
.nav-link:hover { color: var(--text-primary); }
.nav-link.active { color: var(--terracotta); font-weight: 500; }
.nav-link.active::after { content: ''; position: absolute; bottom: 0; left: 14px; right: 14px; height: 2px; background: var(--terracotta); border-radius: 2px 2px 0 0; }

/* ── Page ── */
.page { flex: 1; display: flex; align-items: flex-start; justify-content: center; padding: 40px 24px 72px; }
.card {
  background: var(--ivory); border-radius: var(--r-lg);
  border: 1px solid var(--border-cream);
  box-shadow: rgba(0,0,0,0.04) 0px 4px 24px;
  width: 100%; max-width: 680px; overflow: hidden;
}
.card-section { padding: 20px 24px; border-bottom: 1px solid var(--border-cream); }
.card-section:last-child { border-bottom: none; }

.page-title { font-family: var(--serif); font-size: 28px; font-weight: 500; letter-spacing: 0; color: var(--text-primary); }
.page-subtitle { font-size: 14px; color: var(--text-secondary); margin-top: 5px; line-height: 1.6; }

/* ── Steps ── */
.steps { display: flex; align-items: flex-start; }
.step { flex: 1; text-align: center; font-size: 11px; color: var(--text-tertiary); position: relative; padding-bottom: 4px; }
.step::after {
  content: ''; position: absolute;
  top: 12px; left: calc(50% + 14px); right: calc(-50% + 14px);
  height: 1.5px; background: var(--border-warm); z-index: 0;
}
.step:last-child::after { display: none; }
.step .dot {
  width: 25px; height: 25px; border-radius: 50%;
  background: var(--white); border: 1.5px solid var(--border-warm);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 6px; font-size: 11px; font-weight: 700;
  position: relative; z-index: 1; transition: all .2s;
  color: var(--text-tertiary); font-family: var(--sans);
}
.step.active .dot { border-color: var(--terracotta); color: var(--terracotta); background: rgba(201,100,66,0.06); }
.step.active { color: var(--terracotta); font-weight: 500; }
.step.done .dot { background: var(--green); border-color: var(--green); color: var(--white); }
.step.done { color: var(--green); }
.step.done::after { background: var(--green); opacity: .4; }
.step.error .dot { background: var(--red); border-color: var(--red); color: var(--white); }
.step.error { color: var(--red); }

/* ── Run button ── */
.btn-main {
  background: var(--terracotta); color: var(--ivory); border: none; border-radius: var(--r-md);
  padding: 14px; font-size: 16px; font-weight: 600; font-family: var(--sans);
  cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px;
  box-shadow: var(--terracotta) 0px 0px 0px 0px, var(--terracotta) 0px 0px 0px 1px;
  transition: box-shadow .15s, transform .1s, background .15s;
}
.btn-main:hover:not(:disabled) { background: #b8573a; box-shadow: var(--terracotta) 0px 0px 0px 0px, #a84e33 0px 0px 0px 1px; transform: translateY(-1px); }
.btn-main:active:not(:disabled) { transform: translateY(0); }
.btn-main:disabled { background: var(--warm-sand); color: var(--text-tertiary); cursor: not-allowed; box-shadow: var(--warm-sand) 0px 0px 0px 0px, var(--ring-warm) 0px 0px 0px 1px; }

/* ── Log box ── */
.log-box {
  background: var(--near-black); border-radius: var(--r-sm);
  padding: 14px 16px; font-size: 12px; font-family: var(--mono);
  line-height: 1.9; min-height: 60px; max-height: 300px; overflow-y: auto;
  color: var(--warm-silver);
}
.log-line { color: var(--warm-silver); }
.log-line.done  { color: #6dbe8d; }
.log-line.error { color: #e06060; }
.log-line.active { color: var(--coral); }

/* ── Result card ── */
.result-card {
  background: var(--green-bg); border: 1px solid rgba(58,138,82,0.2);
  border-radius: var(--r-md); padding: 18px 20px;
  display: flex; flex-direction: column; gap: 10px;
}
.result-title { font-family: var(--serif); font-size: 16px; font-weight: 500; color: var(--text-primary); }
.result-url a { font-size: 13px; color: var(--terracotta); word-break: break-all; text-decoration: none; }
.result-url a:hover { text-decoration: underline; }
.badge {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--green); color: var(--white);
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-warm); border-radius: 3px; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.45} }
.pulsing { animation: pulse 1.2s ease-in-out infinite; }
</style>
</head>
<body>

<nav class="top-nav">
  <a href="/" class="nav-logo">PDF Agile Tools</a>
  <span class="nav-sep">/</span>
  <a href="/" class="nav-link">Cover Maker</a>
  <a href="/auto-publish" class="nav-link active">Auto Publish</a>
  <a href="/localize" class="nav-link">Localize</a>
</nav>

<div class="page">
  <div class="card">

    <div class="card-section">
      <div class="page-title">Auto Publish</div>
      <div class="page-subtitle">自动抓热点 → AI 写文 → 生成封面 → 发布 CMS</div>
    </div>

    <div class="card-section">
      <div class="steps">
        <div class="step" id="step-trends"><div class="dot">1</div>抓热点</div>
        <div class="step" id="step-plan"><div class="dot">2</div>AI 规划</div>
        <div class="step" id="step-content"><div class="dot">3</div>写正文</div>
        <div class="step" id="step-seo"><div class="dot">4</div>SEO 优化</div>
        <div class="step" id="step-translate"><div class="dot">5</div>法语版</div>
        <div class="step" id="step-cover"><div class="dot">6</div>生封面</div>
        <div class="step" id="step-publish"><div class="dot">7</div>发布</div>
      </div>
    </div>

    <div class="card-section">
      <button class="btn-main" id="runBtn" onclick="startPipeline()">
        <span id="btnIcon">🚀</span>
        <span id="btnText">开始自动发布</span>
      </button>
    </div>

    <div class="card-section" id="logSection" style="display:none">
      <div class="log-box" id="logBox"></div>
    </div>

    <div class="card-section" id="resultSection" style="display:none">
      <div class="result-card" id="resultCard">
        <div><span class="badge">✓ 已发布</span></div>
        <div class="result-title" id="resultTitle"></div>
        <div class="result-url"><a id="resultUrl" href="#" target="_blank"></a></div>
      </div>
    </div>

  </div>
</div>

<script>
const STEP_MAP = {
  trends:'step-trends', trends_done:'step-trends',
  plan:'step-plan', plan_done:'step-plan',
  content:'step-content', content_done:'step-content',
  seo:'step-seo', seo_done:'step-seo',
  translate:'step-translate', translate_done:'step-translate',
  cover:'step-cover', cover_done:'step-cover',
  publish_en:'step-publish', publish_fr:'step-publish', done:'step-publish',
};

function setStep(step, status) {
  const id = STEP_MAP[step]; if (!id) return;
  const el = document.getElementById(id); if (!el) return;
  el.classList.remove('active','done','error');
  if (status === 'active') el.classList.add('active');
  else if (status === 'done') el.classList.add('done');
  else if (status === 'error') el.classList.add('error');
}

function addLog(step, detail, cls='active') {
  const box = document.getElementById('logBox');
  document.getElementById('logSection').style.display = '';
  const line = document.createElement('div');
  line.className = 'log-line ' + cls;
  const icons = {trends:'🔍',trends_done:'✓',plan:'🧠',plan_done:'✓',content:'✍️',content_done:'✓',cover:'🎨',cover_done:'✓',publish:'📤',done:'✅',error:'❌'};
  line.textContent = (icons[step]||'·') + ' ' + (detail || step);
  box.appendChild(line); box.scrollTop = box.scrollHeight;
}

function startPipeline() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  document.getElementById('btnIcon').textContent = '⏳';
  document.getElementById('btnText').textContent = '处理中...';
  document.getElementById('btnText').classList.add('pulsing');
  document.getElementById('resultSection').style.display = 'none';
  document.getElementById('logSection').style.display = 'none';
  document.getElementById('logBox').innerHTML = '';
  ['step-trends','step-plan','step-content','step-seo','step-translate','step-cover','step-publish']
    .forEach(id => document.getElementById(id).classList.remove('active','done','error'));
  const es = new EventSource('/api/auto-publish/run');
  es.onmessage = (e) => {
    const d = JSON.parse(e.data);
    const { step, detail, status } = d;
    if (status === 'done')        { setStep(step, 'done');   addLog(step, detail, 'done'); }
    else if (status === 'error')  { setStep(step, 'error');  addLog(step, detail, 'error'); resetBtn(); es.close(); }
    else if (status === 'active') { setStep(step, 'active'); addLog(step, detail, 'active'); }
    else if (step === 'result') {
      const result = JSON.parse(detail);
      document.getElementById('resultTitle').textContent = result.title;
      const urlEl = document.getElementById('resultUrl');
      const enUrl = result.en ? result.en.url : result.url;
      urlEl.href = enUrl; urlEl.textContent = enUrl + (result.fr ? ' + 法语版' : '');
      document.getElementById('resultSection').style.display = '';
      resetBtn('再发一篇'); es.close();
    }
  };
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) { addLog('error', '连接已关闭', 'error'); resetBtn(); es.close(); }
  };
}

function resetBtn(label) {
  const btn = document.getElementById('runBtn');
  btn.disabled = false;
  document.getElementById('btnIcon').textContent = '🚀';
  document.getElementById('btnText').textContent = label || '重新开始';
  document.getElementById('btnText').classList.remove('pulsing');
}
</script>
</body>
</html>
"""

import queue
import threading as _threading
from flask import Response, stream_with_context

# 全局流水线状态，防止重连时重复启动
_pipeline_queue   = None   # type: queue.Queue | None
_pipeline_running = False

@app.route("/auto-publish")
def auto_publish_page():
    return auto_publish_page_html()

def auto_publish_page_html():
    from flask import make_response
    resp = make_response(AUTO_PUBLISH_HTML)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/api/auto-publish/run")
def auto_publish_run():
    global _pipeline_queue, _pipeline_running

    # 只在流水线没在跑时才启动新任务
    if not _pipeline_running:
        _pipeline_running = True
        _pipeline_queue   = queue.Queue()

        q = _pipeline_queue

        def progress_cb(step, detail="", status=None):
            if status is None:
                status = "done" if (step.endswith("_done") or step == "done") else "active"
            q.put({"step": step, "detail": detail, "status": status})

        from auto_publish import run_pipeline

        def worker():
            global _pipeline_running
            try:
                result = run_pipeline(progress_cb=progress_cb)
                q.put({"step": "result", "detail": json.dumps(result, ensure_ascii=False), "status": "result"})
            except Exception as e:
                q.put({"step": "error", "detail": str(e), "status": "error"})
            finally:
                q.put(None)  # sentinel
                _pipeline_running = False

        _threading.Thread(target=worker, daemon=True).start()

    def generate():
        import queue as _queue
        q = _pipeline_queue
        done = False
        while not done:
            try:
                item = q.get(timeout=15)
                if item is None:
                    done = True
                    q.put(None)  # 放回 sentinel，供其他重连连接读到结束
                else:
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            except _queue.Empty:
                # 心跳，防止浏览器/代理因无数据而断开连接
                yield ": keepalive\n\n"


    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

# ── Localize Agent 路由 ───────────────────────────────────────────────────────

@app.route("/localize")
def localize_page():
    from localize_html import LOCALIZE_HTML
    excel_path = os.environ.get("LOCALIZE_EXCEL", "")
    return render_template_string(LOCALIZE_HTML, excel_path=excel_path)

@app.route("/api/localize/pages")
def api_localize_pages():
    env = request.args.get("env", "test")
    try:
        pages = localize_agent.fetch_pages(env)
        return jsonify(pages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/localize/history")
def api_localize_history():
    return jsonify(localize_agent.load_history())

@app.route("/api/localize/pick-file")
def api_localize_pick_file():
    """调用 macOS 原生文件选择对话框，返回用户选中的文件路径"""
    import subprocess
    script = (
        'tell application "System Events"\n'
        '  activate\n'
        '  set f to choose file with prompt "选择 Excel 文件" '
        'of type {"xlsx","xls"}\n'
        '  return POSIX path of f\n'
        'end tell'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=60
        )
        path = result.stdout.strip()
        if path:
            return jsonify({"path": path})
        return jsonify({"path": ""}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/localize/run")
def api_localize_run():
    from flask import Response, stream_with_context
    raw_id = request.args.get("page_id", "").strip()
    if not raw_id:
        return jsonify({"error": "page_id is required"}), 400
    page_id          = int(raw_id)
    page_title       = request.args.get("page_title", "")
    page_slug        = request.args.get("page_slug", "")
    locales          = request.args.get("locales", "").split(",")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")
    gen = localize_agent.run_localize_sse(
        page_id=page_id, page_title=page_title, page_slug=page_slug, locales=locales,
        sheet_name=sheet_name, excel_path=excel_path,
        translation_mode=translation_mode, env=env,
    )
    return Response(
        stream_with_context(gen), mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.route("/api/localize/retry")
def api_localize_retry():
    from flask import Response, stream_with_context
    raw_id = request.args.get("page_id", "").strip()
    if not raw_id:
        return jsonify({"error": "page_id is required"}), 400
    page_id          = int(raw_id)
    page_title       = request.args.get("page_title", "")
    page_slug        = request.args.get("page_slug", "")
    locale           = request.args.get("locale")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")
    force_truncate   = request.args.get("force_truncate", "0") == "1"
    gen = localize_agent.run_localize_sse(
        page_id=page_id, page_title=page_title, page_slug=page_slug, locales=[locale],
        sheet_name=sheet_name, excel_path=excel_path,
        translation_mode=translation_mode, env=env, force_truncate=force_truncate,
    )
    return Response(
        stream_with_context(gen), mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def open_browser():
    import time; time.sleep(1)
    webbrowser.open("http://127.0.0.1:5299")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5299))
    if port == 5299:
        threading.Thread(target=open_browser, daemon=True).start()
        print("Cover Maker 启动中 → http://127.0.0.1:5299")
        print("Auto Publish  → http://127.0.0.1:5299/auto-publish")
        print("Localize      → http://127.0.0.1:5299/localize")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
