#!/usr/bin/env python3
"""Cover Maker Web GUI — python3 app.py 启动，浏览器自动打开"""

import os, sys, io, base64, threading, webbrowser, tempfile
from flask import Flask, request, jsonify, render_template_string
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_cover import make_cover, PRESETS
from make_pdfagile_cover import make_pdfagile_cover
from make_howtotips2_cover import make_howtotips2_cover

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Cover Maker</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #1a1a1a; color: #f0f0f0; font-family: -apple-system, sans-serif; min-height: 100vh; }
.layout { display: flex; gap: 0; min-height: 100vh; }

.sidebar { width: 300px; min-width: 300px; background: #242424; padding: 28px 24px; display: flex; flex-direction: column; gap: 18px; overflow-y: auto; }
.sidebar h1 { font-size: 20px; color: #4A8FA0; font-weight: 700; }
label { font-size: 13px; color: #aaa; display: block; margin-bottom: 6px; }
input[type=text], textarea {
  width: 100%; background: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 6px;
  color: #f0f0f0; padding: 8px 10px; font-size: 14px; outline: none; transition: border-color .2s;
}
input[type=text]:focus, textarea:focus { border-color: #4A8FA0; }
textarea { resize: vertical; min-height: 80px; font-family: inherit; }

/* 模式切换 */
.mode-tabs { display: flex; gap: 6px; }
.mode-tab {
  flex: 1; padding: 8px; border: none; border-radius: 6px; font-size: 12px; font-weight: 600;
  cursor: pointer; background: #2d2d2d; color: #777; transition: all .15s;
}
.mode-tab.active { background: #4A8FA0; color: #fff; }

.btn-sm { background: #3a3a3a; color: #f0f0f0; border: none; border-radius: 6px; padding: 8px 14px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-sm:hover { background: #4a4a4a; }

.color-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.color-swatch { width: 32px; height: 32px; border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: border-color .15s, transform .1s; }
.color-swatch:hover { transform: scale(1.1); }
.color-swatch.active { border-color: #fff; }
.hex-row { display: flex; gap: 8px; align-items: center; }
.hex-prefix { color: #aaa; font-size: 14px; }
.hex-row input { width: 90px; }

.btn-main { background: #4A8FA0; color: #fff; border: none; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; transition: background .2s; }
.btn-main:hover { background: #3a7f90; }
.btn-main:disabled { background: #3a3a3a; color: #777; cursor: not-allowed; }
.btn-dl { background: #2d2d2d; color: #aaa; border: none; border-radius: 8px; padding: 9px; font-size: 13px; cursor: pointer; width: 100%; }
.btn-dl:hover { background: #3a3a3a; color: #f0f0f0; }
.btn-dl:disabled { opacity: .4; cursor: not-allowed; }

.status { font-size: 12px; color: #666; line-height: 1.5; min-height: 32px; }
.status.ok  { color: #5cb85c; }
.status.err { color: #e05555; }

.preview-area { flex: 1; display: flex; align-items: center; justify-content: center; background: #111; position: relative; }
.preview-area img { max-width: 100%; max-height: 100vh; object-fit: contain; display: block; }
.preview-placeholder { color: #333; font-size: 16px; }
.spinner { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); }
.spinner.show { display: block; }
@keyframes spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
.spinner svg { animation: spin 1s linear infinite; }

.drop-zone { border: 2px dashed #3a3a3a; border-radius: 8px; padding: 14px; text-align: center; color: #555; font-size: 13px; cursor: pointer; transition: border-color .2s, color .2s; }
.drop-zone.dragover { border-color: #4A8FA0; color: #4A8FA0; }
.section { display: none; flex-direction: column; gap: 18px; }
.section.active { display: flex; }
</style>
</head>
<body>
<div class="layout">
  <div class="sidebar">
    <h1>Cover Maker</h1>

    <!-- 模式切换 -->
    <div>
      <label>模式</label>
      <div class="mode-tabs">
        <button class="mode-tab active" onclick="switchMode('tutorial', this)">HowToTips</button>
        <button class="mode-tab" onclick="switchMode('pdfagile', this)">Templates</button>
        <button class="mode-tab" onclick="switchMode('howtotips2', this)">HowToTips 2</button>
      </div>
    </div>

    <!-- 图片（共用） -->
    <div>
      <label>图片</label>
      <div class="drop-zone" id="dropZone">拖入图片 或 点击选择</div>
      <input type="file" id="fileInput" accept="image/*" style="display:none">
    </div>

    <!-- 标题（共用） -->
    <div>
      <label>标题</label>
      <textarea id="titleInput" placeholder="How to Add Slide Numbers..."></textarea>
    </div>

    <!-- 教程封面专属：颜色 -->
    <div class="section active" id="section-tutorial">
      <div>
        <label>背景颜色</label>
        <div class="color-grid" id="colorGrid"></div>
        <div style="margin-top:8px; font-size:12px; color:#666" id="colorLabel">Teal #4A8FA0</div>
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

    <!-- PDF Agile 专属：无额外参数，背景固定 -->
    <div class="section" id="section-pdfagile">
      <div style="font-size:12px; color:#555; line-height:1.6">
        背景使用 PDF Agile 品牌模板<br>上传模板截图 + 填标题即可生成
      </div>
    </div>

    <!-- HowToTips 2 专属：暖黄背景色选择 -->
    <div class="section" id="section-howtotips2">
      <div>
        <label>背景颜色</label>
        <div class="color-grid" id="colorGrid2"></div>
        <div style="margin-top:8px; font-size:12px; color:#666" id="colorLabel2">#ffbe4c</div>
      </div>
      <div>
        <label>自定义颜色</label>
        <div class="hex-row">
          <span class="hex-prefix">#</span>
          <input type="text" id="hexInput2" placeholder="ffbe4c" maxlength="6">
          <button class="btn-sm" onclick="applyHex2()">应用</button>
        </div>
      </div>
    </div>

    <button class="btn-main" id="genBtn" onclick="generate()" disabled>生成封面</button>
    <button class="btn-dl" id="downloadBtn" onclick="downloadFile()" disabled>下载封面图</button>
    <div class="status" id="status">拖入图片开始</div>
  </div>

  <div class="preview-area">
    <div class="preview-placeholder" id="placeholder">预览区</div>
    <img id="previewImg" style="display:none" alt="preview">
    <div class="spinner" id="spinner">
      <svg width="40" height="40" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="16" fill="none" stroke="#4A8FA0" stroke-width="4"
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

// 色块 (HowToTips 2)
let selectedColor2 = '#ffbe4c';
const grid2 = document.getElementById('colorGrid2');
COLORS2.forEach(([label, hex]) => {
  const s = document.createElement('div');
  s.className = 'color-swatch' + (hex === '#ffbe4c' ? ' active' : '');
  s.style.background = hex;
  s.title = label;
  s.onclick = () => selectColor2(hex, label, s);
  grid2.appendChild(s);
});

function selectColor2(hex, label, el) {
  selectedColor2 = hex;
  document.querySelectorAll('#colorGrid2 .color-swatch').forEach(s => s.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('colorLabel2').textContent = hex;
  schedulePreview();
}

function applyHex2() {
  const val = document.getElementById('hexInput2').value.trim().replace('#','');
  if (/^[0-9a-fA-F]{6}$/.test(val)) {
    selectedColor2 = '#' + val;
    document.querySelectorAll('#colorGrid2 .color-swatch').forEach(s => s.classList.remove('active'));
    document.getElementById('colorLabel2').textContent = '#' + val;
    schedulePreview();
  }
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
  document.querySelectorAll('.mode-tab').forEach(b => b.classList.remove('active'));
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
    dropZone.textContent = '✓ ' + file.name;
    dropZone.style.borderColor = '#4A8FA0';
    dropZone.style.color = '#4A8FA0';
    checkReady(); schedulePreview();
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    const img = new window.Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      let w = img.width, h = img.height;
      // 按比例缩小直到文件估算 < 2MB
      const scale = Math.sqrt(MAX_BYTES / file.size) * 0.9;
      w = Math.round(w * scale); h = Math.round(h * scale);
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      canvas.toBlob(blob => {
        selectedFile = new File([blob], file.name, { type: 'image/jpeg' });
        dropZone.textContent = '✓ ' + file.name + ' (已压缩)';
        dropZone.style.borderColor = '#4A8FA0';
        dropZone.style.color = '#4A8FA0';
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
  fd.append('color', currentMode === 'howtotips2' ? selectedColor2 : selectedColor);
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
        ("暖橙黄", "#ffbe4c"), ("浅金黄", "#ffd272"), ("深橙", "#f5a623"),
        ("奶黄", "#ffe08a"), ("中黄", "#ffcf6b"),
    ]
    return render_template_string(HTML, colors=colors, colors2=colors2)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        file       = request.files["image"]
        title      = request.form["title"]
        mode       = request.form.get("mode", "tutorial")
        color      = request.form.get("color", "teal")
        is_preview = request.form.get("preview") == "1"

        suffix = os.path.splitext(file.filename)[1] or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            file.save(tmp_in.name)
            tmp_in_path = tmp_in.name

        out_path = tempfile.mktemp(suffix=".png")
        base = os.path.splitext(file.filename)[0]

        if mode == "pdfagile":
            make_pdfagile_cover(tmp_in_path, title, output_path=out_path)
            filename = base + "_pdfagile_cover.png"
        elif mode == "howtotips2":
            make_howtotips2_cover(tmp_in_path, title, color, output_path=out_path)
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

def open_browser():
    import time; time.sleep(1)
    webbrowser.open("http://127.0.0.1:5299")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5299))
    if port == 5299:
        threading.Thread(target=open_browser, daemon=True).start()
        print("Cover Maker 启动中 → http://127.0.0.1:5299")
    app.run(host="0.0.0.0", port=port, debug=False)
