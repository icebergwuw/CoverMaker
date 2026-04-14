#!/usr/bin/env python3
"""Cover Maker Web GUI — python3 app.py 启动，浏览器自动打开"""

import os, sys, io, base64, threading, webbrowser, tempfile, json
from flask import Flask, request, jsonify, render_template_string
from PIL import Image

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
    <div style="display:flex;flex-direction:column;gap:8px;"><a href="/auto-publish" style="display:block;background:#2d2d2d;border:1px solid #3a3a3a;border-radius:8px;padding:10px 14px;font-size:13px;color:#4A8FA0;text-decoration:none;text-align:center;">🚀 Auto Publish — 全自动抓热点发文</a><a href="/localize" style="display:block;background:#2d2d2d;border:1px solid #3a3a3a;border-radius:8px;padding:10px 14px;font-size:13px;color:#4A8FA0;text-decoration:none;text-align:center;">🌐 Localize — 多语言本地化</a></div>

    <!-- 模式切换 -->
    <div>
      <label>模式</label>
      <div class="mode-tabs">
        <button class="mode-tab active" onclick="switchMode('tutorial', this)">HowToTips</button>
        <button class="mode-tab" onclick="switchMode('pdfagile', this)">Templates</button>
        <button class="mode-tab" onclick="switchMode('howtotips2', this)">Blog</button>
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

    <!-- HowToTips 2 专属：模板选择 -->
    <div class="section" id="section-howtotips2">
      <div>
        <label>颜色模板</label>
        <div class="color-grid" id="colorGrid2"></div>
        <div style="margin-top:8px; font-size:12px; color:#666" id="colorLabel2">青绿</div>
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
<title>Auto Publish</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #1a1a1a; color: #f0f0f0; font-family: -apple-system, sans-serif; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 48px 24px; }
.card { background: #242424; border-radius: 14px; padding: 36px 40px; width: 100%; max-width: 680px; display: flex; flex-direction: column; gap: 24px; }
h1 { font-size: 22px; color: #4A8FA0; font-weight: 700; }
.subtitle { font-size: 13px; color: #666; }
label { font-size: 13px; color: #aaa; display: block; margin-bottom: 6px; }
input[type=text], select {
  width: 100%; background: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 8px;
  color: #f0f0f0; padding: 10px 14px; font-size: 14px; outline: none; transition: border-color .2s;
}
input[type=text]:focus, select:focus { border-color: #4A8FA0; }
select option { background: #2d2d2d; }
.btn-main {
  background: #4A8FA0; color: #fff; border: none; border-radius: 10px;
  padding: 14px; font-size: 16px; font-weight: 600; cursor: pointer;
  width: 100%; transition: background .2s; display: flex; align-items: center; justify-content: center; gap: 10px;
}
.btn-main:hover { background: #3a7f90; }
.btn-main:disabled { background: #2d2d2d; color: #555; cursor: not-allowed; }

/* 进度日志 */
.log-box {
  background: #111; border-radius: 8px; padding: 16px; font-size: 12px;
  font-family: 'SF Mono', monospace; line-height: 1.8; min-height: 60px;
  max-height: 320px; overflow-y: auto; color: #666; display: none;
}
.log-box.show { display: block; }
.log-line { color: #888; }
.log-line.done  { color: #5cb85c; }
.log-line.error { color: #e05555; }
.log-line.active { color: #4A8FA0; }

/* 结果卡片 */
.result-card {
  background: #1a1a1a; border: 1px solid #2d2d2d; border-radius: 10px;
  padding: 20px 24px; display: none; flex-direction: column; gap: 12px;
}
.result-card.show { display: flex; }
.result-title { font-size: 15px; font-weight: 600; color: #f0f0f0; }
.result-url a { font-size: 13px; color: #4A8FA0; word-break: break-all; text-decoration: none; }
.result-url a:hover { text-decoration: underline; }
.badge { display: inline-block; background: #4A8FA0; color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 4px; }

/* 步骤指示器 */
.steps { display: flex; gap: 0; align-items: center; }
.step { flex: 1; text-align: center; font-size: 11px; color: #444; position: relative; padding-bottom: 20px; }
.step::after { content: ''; position: absolute; bottom: 8px; left: 50%; right: -50%; height: 2px; background: #2d2d2d; z-index: 0; }
.step:last-child::after { display: none; }
.step .dot { width: 28px; height: 28px; border-radius: 50%; background: #2d2d2d; border: 2px solid #3a3a3a; display: flex; align-items: center; justify-content: center; margin: 0 auto 6px; font-size: 11px; font-weight: 700; position: relative; z-index: 1; }
.step.active .dot { border-color: #4A8FA0; color: #4A8FA0; }
.step.active { color: #4A8FA0; }
.step.done .dot { background: #4A8FA0; border-color: #4A8FA0; color: #fff; }
.step.done { color: #5cb85c; }
.step.error .dot { background: #e05555; border-color: #e05555; color: #fff; }

/* 链接回 Cover Maker */
.back-link { font-size: 13px; color: #555; text-decoration: none; align-self: flex-start; }
.back-link:hover { color: #aaa; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.pulsing { animation: pulse 1.2s ease-in-out infinite; }
</style>
</head>
<body>
<div class="card">
  <div>
    <h1>Auto Publish</h1>
    <div class="subtitle" style="margin-top:6px">自动抓热点 → AI写文 → 生成封面 → 发布 CMS</div>
  </div>

  <a class="back-link" href="/">← 返回 Cover Maker</a>

  <!-- 步骤 -->
  <div class="steps">
    <div class="step" id="step-trends"><div class="dot">1</div>抓热点</div>
    <div class="step" id="step-plan"><div class="dot">2</div>AI规划</div>
    <div class="step" id="step-content"><div class="dot">3</div>写正文</div>
    <div class="step" id="step-seo"><div class="dot">4</div>SEO优化</div>
    <div class="step" id="step-translate"><div class="dot">5</div>法语版</div>
    <div class="step" id="step-cover"><div class="dot">6</div>生封面</div>
    <div class="step" id="step-publish"><div class="dot">7</div>发布</div>
  </div>

  <button class="btn-main" id="runBtn" onclick="startPipeline()">
    <span id="btnIcon">🚀</span>
    <span id="btnText">开始自动发布</span>
  </button>

  <!-- 日志 -->
  <div class="log-box" id="logBox"></div>

  <!-- 结果 -->
  <div class="result-card" id="resultCard">
    <div><span class="badge">已发布</span></div>
    <div class="result-title" id="resultTitle"></div>
    <div class="result-url"><a id="resultUrl" href="#" target="_blank"></a></div>
  </div>
</div>

<script>
const STEP_MAP = {
  trends:         'step-trends',
  trends_done:    'step-trends',
  plan:           'step-plan',
  plan_done:      'step-plan',
  content:        'step-content',
  content_done:   'step-content',
  seo:            'step-seo',
  seo_done:       'step-seo',
  translate:      'step-translate',
  translate_done: 'step-translate',
  cover:          'step-cover',
  cover_done:     'step-cover',
  publish_en:     'step-publish',
  publish_fr:     'step-publish',
  done:           'step-publish',
};

function setStep(step, status) {
  const id = STEP_MAP[step];
  if (!id) return;
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('active','done','error');
  if (status === 'active') el.classList.add('active');
  else if (status === 'done') el.classList.add('done');
  else if (status === 'error') el.classList.add('error');
}

function addLog(step, detail, cls='active') {
  const box = document.getElementById('logBox');
  box.classList.add('show');
  const line = document.createElement('div');
  line.className = 'log-line ' + cls;
  const icons = {trends:'🔍',trends_done:'✓',plan:'🧠',plan_done:'✓',content:'✍️',content_done:'✓',cover:'🎨',cover_done:'✓',publish:'📤',done:'✅',error:'❌'};
  line.textContent = (icons[step]||'·') + ' ' + (detail || step);
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

function startPipeline() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  document.getElementById('btnIcon').textContent = '⏳';
  document.getElementById('btnText').textContent = '处理中...';
  document.getElementById('btnText').classList.add('pulsing');
  document.getElementById('resultCard').classList.remove('show');
  document.getElementById('logBox').innerHTML = '';

  // 重置步骤
  ['step-trends','step-plan','step-content','step-seo','step-translate','step-cover','step-publish']
    .forEach(id => { const el = document.getElementById(id); el.classList.remove('active','done','error'); });

  // SSE 连接
  const url = '/api/auto-publish/run';
  const es  = new EventSource(url);

  es.onmessage = (e) => {
    const d = JSON.parse(e.data);
    const { step, detail, status } = d;

    if (status === 'done') {
      // 标记该步骤完成
      setStep(step, 'done');
      addLog(step, detail, 'done');
    } else if (status === 'error') {
      setStep(step, 'error');
      addLog(step, detail, 'error');
      btn.disabled = false;
      document.getElementById('btnIcon').textContent = '🚀';
      document.getElementById('btnText').textContent = '重新开始';
      document.getElementById('btnText').classList.remove('pulsing');
      es.close();
    } else if (status === 'active') {
      setStep(step, 'active');
      addLog(step, detail, 'active');
    } else if (step === 'result') {
      // 最终结果
      const result = JSON.parse(detail);
      document.getElementById('resultTitle').textContent = result.title;
      const urlEl = document.getElementById('resultUrl');
      const enUrl = result.en ? result.en.url : result.url;
      urlEl.href = enUrl;
      urlEl.textContent = enUrl + (result.fr ? ' + 法语版' : '');
      document.getElementById('resultCard').classList.add('show');
      btn.disabled = false;
      document.getElementById('btnIcon').textContent = '🚀';
      document.getElementById('btnText').textContent = '再发一篇';
      document.getElementById('btnText').classList.remove('pulsing');
      es.close();
    }
  };

  es.onerror = () => {
    // CONNECTING=0 表示正在自动重连，不视为真正的错误
    if (es.readyState === EventSource.CLOSED) {
      addLog('error', '连接已关闭', 'error');
      btn.disabled = false;
      document.getElementById('btnIcon').textContent = '🚀';
      document.getElementById('btnText').textContent = '重新开始';
      document.getElementById('btnText').classList.remove('pulsing');
      es.close();
    }
    // readyState === CONNECTING (0) 时浏览器在自动重连，静默等待即可
  };
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
    return LOCALIZE_HTML

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

@app.route("/api/localize/run")
def api_localize_run():
    from flask import Response, stream_with_context
    raw_id = request.args.get("page_id", "").strip()
    if not raw_id:
        return jsonify({"error": "page_id is required"}), 400
    page_id          = int(raw_id)
    page_title       = request.args.get("page_title", "")
    locales          = request.args.get("locales", "").split(",")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")
    gen = localize_agent.run_localize_sse(
        page_id=page_id, page_title=page_title, locales=locales,
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
    locale           = request.args.get("locale")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")
    gen = localize_agent.run_localize_sse(
        page_id=page_id, page_title=page_title, locales=[locale],
        sheet_name=sheet_name, excel_path=excel_path,
        translation_mode=translation_mode, env=env,
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
