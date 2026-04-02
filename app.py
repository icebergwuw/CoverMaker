#!/usr/bin/env python3
"""Cover Maker Web GUI — python3 app.py 启动，浏览器自动打开"""

import os, sys, io, base64, threading, webbrowser, tempfile
from flask import Flask, request, jsonify, send_file, render_template_string
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_cover import make_cover, PRESETS

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

/* 左侧控制栏 */
.sidebar { width: 300px; min-width: 300px; background: #242424; padding: 28px 24px; display: flex; flex-direction: column; gap: 20px; }
.sidebar h1 { font-size: 22px; color: #4A8FA0; font-weight: 700; }
label { font-size: 13px; color: #aaa; display: block; margin-bottom: 6px; }
input[type=text], textarea {
  width: 100%; background: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 6px;
  color: #f0f0f0; padding: 8px 10px; font-size: 14px; outline: none;
  transition: border-color .2s;
}
input[type=text]:focus, textarea:focus { border-color: #4A8FA0; }
textarea { resize: vertical; min-height: 80px; font-family: inherit; }

/* 图片区 */
.img-row { display: flex; gap: 8px; }
.img-row input { flex: 1; }
.btn-sm { background: #3a3a3a; color: #f0f0f0; border: none; border-radius: 6px; padding: 8px 14px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-sm:hover { background: #4a4a4a; }

/* 颜色格 */
.color-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.color-swatch {
  width: 36px; height: 36px; border-radius: 6px; cursor: pointer;
  border: 2px solid transparent; transition: border-color .15s, transform .1s;
}
.color-swatch:hover { transform: scale(1.1); }
.color-swatch.active { border-color: #fff; }

/* hex输入 */
.hex-row { display: flex; gap: 8px; align-items: center; }
.hex-prefix { color: #aaa; font-size: 14px; }
.hex-row input { width: 90px; }

/* 生成按钮 */
.btn-main {
  background: #4A8FA0; color: #fff; border: none; border-radius: 8px;
  padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%;
  transition: background .2s;
}
.btn-main:hover { background: #3a7f90; }
.btn-main:disabled { background: #3a3a3a; color: #777; cursor: not-allowed; }

.btn-reveal { background: #2d2d2d; color: #aaa; border: none; border-radius: 8px; padding: 9px; font-size: 13px; cursor: pointer; width: 100%; }
.btn-reveal:hover { background: #3a3a3a; color: #f0f0f0; }
.btn-reveal:disabled { opacity: .4; cursor: not-allowed; }

.status { font-size: 12px; color: #666; line-height: 1.5; min-height: 36px; }
.status.ok  { color: #5cb85c; }
.status.err { color: #e05555; }

/* 右侧预览 */
.preview-area {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: #111; position: relative;
}
.preview-area img { max-width: 100%; max-height: 100vh; object-fit: contain; display: block; }
.preview-placeholder { color: #333; font-size: 16px; }
.spinner { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); }
.spinner.show { display: block; }
@keyframes spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
.spinner svg { animation: spin 1s linear infinite; }

/* 拖拽区 */
.drop-zone {
  border: 2px dashed #3a3a3a; border-radius: 8px; padding: 16px;
  text-align: center; color: #555; font-size: 13px; cursor: pointer;
  transition: border-color .2s, color .2s;
}
.drop-zone.dragover { border-color: #4A8FA0; color: #4A8FA0; }
</style>
</head>
<body>
<div class="layout">

  <!-- 左侧 -->
  <div class="sidebar">
    <h1>Cover Maker</h1>

    <!-- 图片 -->
    <div>
      <label>图片</label>
      <div class="drop-zone" id="dropZone">拖入图片 或 点击选择</div>
      <input type="file" id="fileInput" accept="image/*" style="display:none">
    </div>

    <!-- 标题 -->
    <div>
      <label>标题</label>
      <textarea id="titleInput" placeholder="How to Add Slide Numbers..."></textarea>
    </div>

    <!-- 颜色 -->
    <div>
      <label>背景颜色</label>
      <div class="color-grid" id="colorGrid"></div>
      <div style="margin-top:8px; font-size:12px; color:#666" id="colorLabel">Teal #4A8FA0</div>
    </div>

    <!-- 自定义HEX -->
    <div>
      <label>自定义颜色</label>
      <div class="hex-row">
        <span class="hex-prefix">#</span>
        <input type="text" id="hexInput" placeholder="3D7A8A" maxlength="6">
        <button class="btn-sm" onclick="applyHex()">应用</button>
      </div>
    </div>

    <!-- 按钮 -->
    <button class="btn-main" id="genBtn" onclick="generate()" disabled>生成封面</button>
    <button class="btn-reveal" id="revealBtn" onclick="revealFile()" disabled>在 Finder 中显示</button>

    <div class="status" id="status">拖入图片开始</div>
  </div>

  <!-- 右侧预览 -->
  <div class="preview-area" id="previewArea">
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
let selectedColor = 'teal';
let selectedFile = null;
let outputPath = null;
let previewTimer = null;

// 生成色块
const grid = document.getElementById('colorGrid');
COLORS.forEach(([label, key, hex]) => {
  const s = document.createElement('div');
  s.className = 'color-swatch' + (key === 'teal' ? ' active' : '');
  s.style.background = hex;
  s.title = label;
  s.dataset.key = key;
  s.onclick = () => selectColor(key, label, hex, s);
  grid.appendChild(s);
});

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

// 拖拽
const dropZone = document.getElementById('dropZone');
dropZone.onclick = () => document.getElementById('fileInput').click();
dropZone.ondragover = e => { e.preventDefault(); dropZone.classList.add('dragover'); };
dropZone.ondragleave = () => dropZone.classList.remove('dragover');
dropZone.ondrop = e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) loadFile(file);
};
document.getElementById('fileInput').onchange = e => {
  if (e.target.files[0]) loadFile(e.target.files[0]);
};

function loadFile(file) {
  selectedFile = file;
  dropZone.textContent = '✓ ' + file.name;
  dropZone.style.borderColor = '#4A8FA0';
  dropZone.style.color = '#4A8FA0';
  checkReady();
  schedulePreview();
}

document.getElementById('titleInput').oninput = () => { checkReady(); schedulePreview(); };

function checkReady() {
  const ready = selectedFile && document.getElementById('titleInput').value.trim();
  document.getElementById('genBtn').disabled = !ready;
}

// 预览（防抖600ms）
function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(doPreview, 600);
}

function doPreview() {
  if (!selectedFile || !document.getElementById('titleInput').value.trim()) return;
  const fd = new FormData();
  fd.append('image', selectedFile);
  fd.append('title', document.getElementById('titleInput').value.trim());
  fd.append('color', selectedColor);
  fd.append('preview', '1');
  showSpinner(true);
  fetch('/generate', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      showSpinner(false);
      if (d.preview) {
        document.getElementById('placeholder').style.display = 'none';
        const img = document.getElementById('previewImg');
        img.src = 'data:image/png;base64,' + d.preview;
        img.style.display = 'block';
      }
    })
    .catch(() => showSpinner(false));
}

function generate() {
  if (!selectedFile || !document.getElementById('titleInput').value.trim()) return;
  const btn = document.getElementById('genBtn');
  btn.disabled = true; btn.textContent = '生成中…';
  setStatus('正在生成…', '');

  const fd = new FormData();
  fd.append('image', selectedFile);
  fd.append('title', document.getElementById('titleInput').value.trim());
  fd.append('color', selectedColor);

  fetch('/generate', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      btn.disabled = false; btn.textContent = '生成封面';
      if (d.error) { setStatus('失败：' + d.error, 'err'); return; }
      outputPath = d.output;
      document.getElementById('revealBtn').disabled = false;
      setStatus('✓ 已保存：' + d.filename, 'ok');
      // 更新预览
      if (d.preview) {
        document.getElementById('placeholder').style.display = 'none';
        const img = document.getElementById('previewImg');
        img.src = 'data:image/png;base64,' + d.preview;
        img.style.display = 'block';
      }
    })
    .catch(e => {
      btn.disabled = false; btn.textContent = '生成封面';
      setStatus('请求失败：' + e, 'err');
    });
}

function revealFile() {
  if (outputPath) fetch('/reveal?path=' + encodeURIComponent(outputPath));
}

function setStatus(msg, cls) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status ' + cls;
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
    return render_template_string(HTML, colors=colors)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        file      = request.files["image"]
        title     = request.form["title"]
        color     = request.form.get("color", "teal")
        is_preview = request.form.get("preview") == "1"

        # 保存上传图片到临时文件
        suffix = os.path.splitext(file.filename)[1] or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            file.save(tmp_in.name)
            tmp_in_path = tmp_in.name

        # 输出路径
        if is_preview:
            out_path = tempfile.mktemp(suffix=".png")
        else:
            base = os.path.splitext(file.filename)[0]
            dl_dir = os.path.expanduser("~/Downloads")
            out_path = os.path.join(dl_dir, base + "_cover.png")

        make_cover(tmp_in_path, title, color, output_path=out_path)
        os.unlink(tmp_in_path)

        # 生成 base64 预览
        img = Image.open(out_path)
        img.thumbnail((800, 600), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        if is_preview:
            os.unlink(out_path)
            return jsonify({"preview": b64})

        return jsonify({
            "output":   out_path,
            "filename": os.path.basename(out_path),
            "preview":  b64,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reveal")
def reveal():
    path = request.args.get("path", "")
    if os.path.exists(path):
        os.system(f'open -R "{path}"')
    return "", 204

def open_browser():
    import time; time.sleep(1)
    webbrowser.open("http://127.0.0.1:5299")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("Cover Maker 启动中 → http://127.0.0.1:5299")
    app.run(port=5299, debug=False)
