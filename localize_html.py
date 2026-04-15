"""localize_html.py — Localize Tab 前端页面 HTML"""

LOCALIZE_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Localize — PDF Agile</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:           #f5f5f7;
  --surface:      #ffffff;
  --surface-2:    #f0f0f5;
  --border:       rgba(0,0,0,0.08);
  --border-focus: #0071e3;
  --text-primary: #1d1d1f;
  --text-secondary:#6e6e73;
  --text-tertiary: #a1a1a6;
  --accent:        #0071e3;
  --accent-hover:  #0077ed;
  --accent-light:  rgba(0,113,227,0.08);
  --accent-light2: rgba(0,113,227,0.14);
  --green:         #34c759;
  --green-light:   rgba(52,199,89,0.10);
  --red:           #ff3b30;
  --red-light:     rgba(255,59,48,0.10);
  --orange:        #ff9500;
  --orange-light:  rgba(255,149,0,0.10);
  --radius-sm:     8px;
  --radius-md:     12px;
  --radius-lg:     16px;
  --shadow-sm:     0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:     0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
  --shadow-lg:     0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06);
  --font-system:   -apple-system, "SF Pro Display", "SF Pro Text", BlinkMacSystemFont, "Helvetica Neue", sans-serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }

body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-system);
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.5;
}

/* ── Nav ── */
.top-nav {
  background: rgba(255,255,255,0.85);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 0 28px;
  display: flex;
  align-items: center;
  height: 52px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-logo {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  text-decoration: none;
  letter-spacing: -0.3px;
  margin-right: 8px;
}
.nav-sep { color: var(--border); margin: 0 4px; font-size: 18px; }
.top-nav a.nav-link {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 0;
  transition: color .15s;
  position: relative;
}
.top-nav a.nav-link:hover { color: var(--text-primary); }
.top-nav a.nav-link.active {
  color: var(--accent);
}
.top-nav a.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0; left: 14px; right: 14px;
  height: 2px;
  background: var(--accent);
  border-radius: 2px 2px 0 0;
}

/* ── Page layout ── */
.page {
  max-width: 820px;
  margin: 0 auto;
  padding: 32px 24px 60px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  margin-bottom: 8px;
}
.page-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text-primary);
}
.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
  font-weight: 400;
}

/* ── Card ── */
.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  overflow: hidden;
}
.card-header {
  padding: 16px 20px 0;
}
.card-body {
  padding: 16px 20px 20px;
}
.card-body + .card-body {
  padding-top: 0;
}
.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

/* ── Inputs ── */
input[type=text], select {
  width: 100%;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 9px 12px;
  font-size: 14px;
  font-family: var(--font-system);
  outline: none;
  transition: border-color .15s, box-shadow .15s;
  appearance: none;
  -webkit-appearance: none;
}
input[type=text]:focus, select:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(0,113,227,0.15);
  background: var(--surface);
}
select {
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%236e6e73' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
  cursor: pointer;
}
label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 6px;
}

/* ── Segmented control (env) ── */
.seg-ctrl {
  display: flex;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  padding: 3px;
  gap: 2px;
}
.seg-btn {
  flex: 1;
  padding: 7px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-system);
  cursor: pointer;
  transition: all .15s;
  text-align: center;
}
.seg-btn.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  font-weight: 600;
}

/* ── Page row ── */
.page-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.page-row select { flex: 1; }
.btn-ghost {
  background: var(--surface-2);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-system);
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s;
}
.btn-ghost:hover {
  background: var(--surface);
  color: var(--text-primary);
  border-color: rgba(0,0,0,0.12);
}

/* ── Source tabs ── */
.source-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}
.source-tab {
  padding: 6px 16px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-system);
  cursor: pointer;
  background: transparent;
  color: var(--text-secondary);
  transition: all .15s;
}
.source-tab.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.source-section { display: none; flex-direction: column; gap: 12px; }
.source-section.active { display: flex; }

/* ── Language chips ── */
.lang-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.lang-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.lang-count span {
  color: var(--accent);
  font-weight: 600;
}
.lang-actions {
  display: flex;
  gap: 0;
  background: var(--surface-2);
  border-radius: 20px;
  padding: 2px;
}
.lang-action-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-system);
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 18px;
  transition: all .15s;
}
.lang-action-btn:hover {
  background: var(--surface);
  color: var(--text-primary);
}

.lang-grid {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  gap: 6px;
}
.lang-chip {
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 7px 4px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  cursor: pointer;
  background: var(--surface-2);
  user-select: none;
  transition: all .15s;
  letter-spacing: -0.2px;
}
.lang-chip:hover:not(.done) {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-light);
}
.lang-chip.done {
  background: var(--green-light);
  border-color: rgba(52,199,89,0.25);
  color: #248a3d;
  cursor: default;
}
.lang-chip.sel {
  background: var(--accent-light2);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.lang-chip.fail {
  background: var(--red-light);
  border-color: rgba(255,59,48,0.25);
  color: #c41e3a;
}
.lang-chip.running {
  background: var(--accent-light2);
  border-color: var(--accent);
  color: var(--accent);
  animation: chip-pulse .9s ease-in-out infinite;
}
@keyframes chip-pulse {
  0%,100% { opacity: 1; }
  50% { opacity: .5; }
}
.lang-legend {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 8px;
  display: flex;
  gap: 12px;
}
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot {
  width: 7px; height: 7px; border-radius: 50%;
}
.legend-dot.done  { background: var(--green); }
.legend-dot.sel   { background: var(--accent); }
.legend-dot.fail  { background: var(--red); }
.legend-dot.idle  { background: var(--border); border: 1.5px solid var(--text-tertiary); }

/* ── Run button ── */
.btn-run {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  padding: 13px 20px;
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-system);
  cursor: pointer;
  width: 100%;
  letter-spacing: -0.2px;
  transition: background .15s, transform .1s, box-shadow .15s;
  box-shadow: 0 2px 8px rgba(0,113,227,0.30);
}
.btn-run:hover:not(:disabled) {
  background: var(--accent-hover);
  box-shadow: 0 4px 16px rgba(0,113,227,0.35);
  transform: translateY(-1px);
}
.btn-run:active:not(:disabled) { transform: translateY(0); }
.btn-run:disabled {
  background: var(--surface-2);
  color: var(--text-tertiary);
  cursor: not-allowed;
  box-shadow: none;
}

/* ── Progress ── */
.progress-wrap { display: none; margin-top: 14px; }
.progress-wrap.show { display: block; }
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.progress-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.progress-current {
  font-size: 12px;
  color: var(--text-secondary);
}
.progress-track {
  height: 4px;
  background: var(--surface-2);
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #34aadc);
  border-radius: 4px;
  transition: width .35s cubic-bezier(.4,0,.2,1);
  width: 0%;
}

/* ── Log box ── */
.log-box {
  display: none;
  background: #f9f9fb;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-family: "SF Mono", "Fira Code", "Menlo", monospace;
  font-size: 12px;
  line-height: 1.9;
  max-height: 220px;
  overflow-y: auto;
  margin-top: 12px;
}
.log-box.show { display: block; }
.log-ok   { color: #248a3d; }
.log-run  { color: var(--accent); }
.log-warn { color: #9a6700; }
.log-err  { color: #c41e3a; }
.log-dim  { color: var(--text-tertiary); }

/* ── Retry list ── */
.retry-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.retry-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--red-light);
  border: 1px solid rgba(255,59,48,0.2);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  font-size: 12px;
  color: #c41e3a;
}
.btn-retry {
  background: var(--surface);
  border: 1px solid rgba(255,59,48,0.25);
  color: var(--red);
  border-radius: 6px;
  font-size: 11px;
  font-family: var(--font-system);
  font-weight: 600;
  padding: 3px 10px;
  cursor: pointer;
  transition: all .15s;
}
.btn-retry:hover { background: var(--red-light); }

/* ── History ── */
.history-list { display: flex; flex-direction: column; }
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  gap: 12px;
}
.history-item:last-child { border-bottom: none; }
.h-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}
.h-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 3px;
  display: flex;
  gap: 6px;
  align-items: center;
}
.h-env-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: var(--surface-2);
  color: var(--text-secondary);
}
.history-langs {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  justify-content: flex-end;
  max-width: 360px;
}
.h-lang {
  font-size: 10px;
  font-weight: 600;
  background: var(--green-light);
  color: #248a3d;
  border-radius: 4px;
  padding: 2px 6px;
  letter-spacing: -0.1px;
}
.h-lang.fail {
  background: var(--red-light);
  color: #c41e3a;
}
.empty-state {
  text-align: center;
  color: var(--text-tertiary);
  padding: 28px 0;
  font-size: 13px;
}
.empty-icon { font-size: 28px; margin-bottom: 8px; }

/* ── Varchar error card ── */
.varchar-error-card {
  background: #fffbeb;
  border: 1px solid rgba(255,149,0,0.3);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin: 8px 0;
}
.varchar-error-title {
  font-size: 13px;
  font-weight: 600;
  color: #7c4e00;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.varchar-error-detail {
  font-size: 12px;
  color: #92591a;
  line-height: 1.65;
  margin-bottom: 10px;
}
.varchar-error-detail code {
  background: rgba(255,149,0,0.12);
  padding: 1px 5px;
  border-radius: 4px;
  font-family: "SF Mono", monospace;
  font-size: 11px;
}
.varchar-error-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-truncate {
  background: var(--orange);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-system);
  cursor: pointer;
  transition: all .15s;
}
.btn-truncate:hover { background: #e6870a; }
.btn-truncate:disabled { opacity: .5; cursor: not-allowed; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.25); }

/* ── Divider ── */
.field-group { display: flex; flex-direction: column; gap: 12px; }

/* ── AI info box ── */
.ai-info {
  background: var(--accent-light);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: 13px;
  color: #004499;
  line-height: 1.6;
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.ai-info-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
</style>
</head>
<body>

<nav class="top-nav">
  <a href="/" class="nav-logo">PDF Agile Tools</a>
  <span class="nav-sep">/</span>
  <a href="/" class="nav-link">Cover Maker</a>
  <a href="/auto-publish" class="nav-link">Auto Publish</a>
  <a href="/localize" class="nav-link active">Localize</a>
</nav>

<div class="page">

  <div class="page-header">
    <div class="page-title">Localize</div>
    <div class="page-subtitle">将专题页内容发布到多语言 CMS</div>
  </div>

  <!-- 环境 + 文章 合并为一个卡片 -->
  <div class="card">
    <div class="card-body">
      <div class="section-label">环境</div>
      <div class="seg-ctrl">
        <button class="seg-btn active" onclick="setEnv('test',this)">测试环境</button>
        <button class="seg-btn" onclick="setEnv('prod',this)">正式环境</button>
      </div>
    </div>
    <div style="height:1px;background:var(--border);margin:0 20px;"></div>
    <div class="card-body">
      <div class="section-label">文章</div>
      <div class="page-row">
        <select id="pageSelect" onchange="onPageChange()">
          <option value="">正在加载...</option>
        </select>
        <button class="btn-ghost" onclick="loadPages()">刷新</button>
      </div>
    </div>
  </div>

  <!-- 翻译来源 -->
  <div class="card">
    <div class="card-body">
      <div class="section-label">翻译来源</div>
      <div class="source-tabs">
        <button class="source-tab active" onclick="setSource('excel',this)">Excel</button>
        <button class="source-tab" onclick="setSource('ai',this)">AI 翻译（Gemini）</button>
      </div>
      <div class="source-section active" id="src-excel">
        <div class="field-group">
          <div>
            <label>Excel 文件路径</label>
            <input type="text" id="excelPath" placeholder="/path/to/file.xlsx"
                   value="/Users/ice/Downloads/专题页文案与多语言本地化-更新至20260408.xlsx">
          </div>
          <div>
            <label>Sheet 名称</label>
            <input type="text" id="sheetName" placeholder="Organize PDF">
          </div>
        </div>
      </div>
      <div class="source-section" id="src-ai">
        <div class="ai-info">
          <span class="ai-info-icon">✦</span>
          <span>使用 Gemini API 自动翻译，无需 Excel。适合没有翻译表的新文章。</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 语言选择 -->
  <div class="card">
    <div class="card-body">
      <div class="section-label">目标语言</div>
      <div class="lang-toolbar">
        <div class="lang-count">已选 <span id="langCountNum">0</span> 种</div>
        <div class="lang-actions">
          <button class="lang-action-btn" onclick="selectAll()">全选</button>
          <button class="lang-action-btn" onclick="selectNone()">清空</button>
          <button class="lang-action-btn" onclick="selectPending()">未做过的</button>
        </div>
      </div>
      <div class="lang-grid" id="langGrid"></div>
      <div class="lang-legend">
        <span class="legend-item"><span class="legend-dot done"></span>已完成</span>
        <span class="legend-item"><span class="legend-dot sel"></span>已选中</span>
        <span class="legend-item"><span class="legend-dot fail"></span>上次失败</span>
        <span class="legend-item"><span class="legend-dot idle"></span>未处理</span>
      </div>
    </div>
  </div>

  <!-- 执行 -->
  <div class="card">
    <div class="card-body">
      <button class="btn-run" id="runBtn" onclick="startRun()" disabled>开始本地化</button>
      <div class="progress-wrap" id="progressWrap">
        <div class="progress-header">
          <span class="progress-count" id="progressText">0 / 0</span>
          <span class="progress-current" id="progressCurrent"></span>
        </div>
        <div class="progress-track"><div class="progress-fill" id="progressFill"></div></div>
      </div>
      <div class="log-box" id="logBox"></div>
      <div class="retry-list" id="retryList"></div>
    </div>
  </div>

  <!-- 历史记录 -->
  <div class="card">
    <div class="card-body">
      <div class="section-label">最近记录</div>
      <div id="historyList" class="history-list">
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          暂无记录
        </div>
      </div>
    </div>
  </div>

</div>

<script>
const ALL_LOCALES = ["fr","zh-Hant","es","de","pt","it","ja","ko","ar","id","vi","th","ms","tr","pl","nl","ro","hi"];
let currentEnv    = 'test';
let currentSource = 'excel';
let currentPage   = null;
let chipStates    = {};
let runState      = null;
let activeSSE     = null;

window.onload = () => { buildLangGrid(); loadPages(); loadHistory(); };

// ── 环境 ──
function setEnv(env, btn) {
  currentEnv = env;
  document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadPages();
}

// ── 翻译来源 ──
function setSource(src, btn) {
  currentSource = src;
  document.querySelectorAll('.source-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.source-section').forEach(s => s.classList.remove('active'));
  document.getElementById('src-' + src).classList.add('active');
}

// ── 文章列表 ──
async function loadPages() {
  const sel = document.getElementById('pageSelect');
  sel.innerHTML = '<option value="">正在加载...</option>';
  try {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 15000);
    const r = await fetch('/api/localize/pages?env=' + currentEnv, {signal: ctrl.signal});
    clearTimeout(tid);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const pages = await r.json();
    if (pages.error) throw new Error(pages.error);
    if (!Array.isArray(pages) || pages.length === 0) {
      sel.innerHTML = '<option value="">无文章（检查环境连接）</option>';
      return;
    }
    sel.innerHTML = '<option value="">选择文章…</option>';
    pages.forEach(p => {
      const o = document.createElement('option');
      o.value = p.id;
      o.textContent = p.title + '  (id=' + p.id + ')';
      o.dataset.locales    = JSON.stringify(p.locales);
      o.dataset.title      = p.title;
      o.dataset.slug       = p.slug || '';
      o.dataset.sheet_name = p.sheet_name || '';
      sel.appendChild(o);
    });
  } catch(e) {
    sel.innerHTML = '<option value="">加载失败: ' + e.message + '</option>';
  }
}

function onPageChange() {
  const sel = document.getElementById('pageSelect');
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !opt.value) { currentPage = null; updateRunBtn(); return; }
  currentPage = { id: parseInt(opt.value), title: opt.dataset.title, slug: opt.dataset.slug || '' };
  const doneLocales = JSON.parse(opt.dataset.locales || '[]');
  const sheetName   = opt.dataset.sheet_name || '';

  document.getElementById('sheetName').value = sheetName;
  if (!sheetName) {
    setSource('ai', document.querySelector('.source-tab:nth-child(2)'));
    document.getElementById('sheetName').placeholder = '（无 Excel sheet，使用 AI 翻译）';
  } else {
    setSource('excel', document.querySelector('.source-tab:nth-child(1)'));
  }

  ALL_LOCALES.forEach(l => { chipStates[l] = doneLocales.includes(l) ? 'done' : ''; });
  refreshChips();
  updateRunBtn();
}

// ── 语言格子 ──
function buildLangGrid() {
  const g = document.getElementById('langGrid');
  ALL_LOCALES.forEach(l => {
    const c = document.createElement('div');
    c.className = 'lang-chip'; c.id = 'chip-' + l; c.textContent = l;
    c.onclick = () => toggleChip(l);
    g.appendChild(c);
  });
}
function toggleChip(l) {
  if (chipStates[l] === 'done') return;
  chipStates[l] = chipStates[l] === 'sel' ? '' : 'sel';
  refreshChips(); updateRunBtn();
}
function refreshChips() {
  let cnt = 0;
  ALL_LOCALES.forEach(l => {
    const c = document.getElementById('chip-' + l);
    c.className = 'lang-chip ' + (chipStates[l] || '');
    if (chipStates[l] === 'sel') cnt++;
  });
  document.getElementById('langCountNum').textContent = cnt;
}
function selectAll()     { ALL_LOCALES.forEach(l => { if (chipStates[l] !== 'done') chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }
function selectNone()    { ALL_LOCALES.forEach(l => { if (chipStates[l] === 'sel')  chipStates[l] = '';    }); refreshChips(); updateRunBtn(); }
function selectPending() { ALL_LOCALES.forEach(l => { if (!chipStates[l])           chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }

function updateRunBtn() {
  const cnt = ALL_LOCALES.filter(l => chipStates[l] === 'sel').length;
  const btn = document.getElementById('runBtn');
  btn.disabled = !currentPage || cnt === 0;
  btn.textContent = cnt > 0 ? '开始本地化（' + cnt + ' 种语言）' : '开始本地化';
}

// ── 执行 ──
function buildParams(locales) {
  return new URLSearchParams({
    page_id: currentPage.id, page_title: currentPage.title,
    page_slug: currentPage.slug || '',
    locales: locales.join(','),
    sheet_name: document.getElementById('sheetName').value.trim(),
    excel_path: document.getElementById('excelPath').value.trim(),
    translation_mode: currentSource, env: currentEnv,
  }).toString();
}

function startRun() {
  const locales = ALL_LOCALES.filter(l => chipStates[l] === 'sel');
  if (!locales.length || !currentPage) return;
  if (currentSource === 'excel' && !document.getElementById('sheetName').value.trim()) {
    alert('请填写 Sheet 名称，或切换到 AI 翻译模式');
    return;
  }
  beginSSE('/api/localize/run?' + buildParams(locales), locales.length);
}

function beginSSE(url, total) {
  if (activeSSE) activeSSE.close();
  document.getElementById('runBtn').disabled = true;
  document.getElementById('progressWrap').classList.add('show');
  document.getElementById('logBox').classList.add('show');
  document.getElementById('logBox').innerHTML = '';
  document.getElementById('retryList').innerHTML = '';
  runState = { total, done: 0 };
  updateProgress(0, total, '');
  activeSSE = new EventSource(url);
  activeSSE.onmessage = e => handleSSE(JSON.parse(e.data));
  activeSSE.onerror = () => { activeSSE.close(); log('连接中断', 'err'); };
}

function handleSSE(ev) {
  switch (ev.type) {
    case 'start':
      log('▶ ' + ev.locale + ' (' + ev.index + '/' + ev.total + ')...', 'run');
      chipStates[ev.locale] = 'running'; refreshChips();
      updateProgress(runState.done, runState.total, ev.locale);
      break;
    case 'progress':
      log('  ' + ev.msg, 'dim'); break;
    case 'varchar_error':
      runState.done++;
      chipStates[ev.locale] = 'fail'; refreshChips();
      updateProgress(runState.done, runState.total, '');
      logVarcharError(ev);
      break;
    case 'done':
      runState.done++;
      chipStates[ev.locale] = 'done'; refreshChips();
      if (ev.fe_url) {
        logLink('✓ ' + ev.locale, ev.fe_url);
      } else {
        log('✓ ' + ev.locale + ' (id=' + ev.new_id + ')', 'ok');
      }
      updateProgress(runState.done, runState.total, '');
      break;
    case 'error':
      runState.done++;
      chipStates[ev.locale] = 'fail'; refreshChips();
      log('✗ ' + ev.locale + ': ' + ev.msg, 'err');
      updateProgress(runState.done, runState.total, '');
      addRetryBtn(ev.locale, ev.msg);
      break;
    case 'finished':
      activeSSE.close();
      document.getElementById('runBtn').disabled = false;
      log('── 完成 ' + ev.ok + '/' + ev.total + ' ──', ev.fail > 0 ? 'warn' : 'ok');
      loadHistory();
      break;
  }
}

function updateProgress(done, total, cur) {
  const pct = total > 0 ? Math.round(done / total * 100) : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressText').textContent = done + ' / ' + total;
  document.getElementById('progressCurrent').textContent = cur ? '▶ ' + cur + '...' : (done === total && total > 0 ? '完成' : '');
}

function log(msg, cls) {
  const b = document.getElementById('logBox');
  const d = document.createElement('div');
  d.className = 'log-' + cls; d.textContent = msg;
  b.appendChild(d); b.scrollTop = b.scrollHeight;
}

function logLink(label, url) {
  const b = document.getElementById('logBox');
  const d = document.createElement('div');
  d.className = 'log-ok';
  const a = document.createElement('a');
  a.href = url; a.target = '_blank'; a.rel = 'noopener';
  a.textContent = url;
  a.style.cssText = 'color:#0071e3;text-decoration:underline;margin-left:6px;';
  d.textContent = label + ' ';
  d.appendChild(a);
  b.appendChild(d); b.scrollTop = b.scrollHeight;
}

function logVarcharError(ev) {
  const b = document.getElementById('logBox');
  const card = document.createElement('div');
  card.className = 'varchar-error-card';

  const title = document.createElement('div');
  title.className = 'varchar-error-title';
  title.innerHTML = '<span>⚠︎</span> ' + ev.locale + '：字段超长，已暂停';
  card.appendChild(title);

  const detail = document.createElement('div');
  detail.className = 'varchar-error-detail';
  detail.innerHTML =
    '字段 <code>' + ev.field + '</code> 翻译后长度 <strong>' + ev.length + '</strong> 字符，' +
    '超过 Strapi 数据库 VARCHAR(<strong>' + ev.limit + '</strong>) 限制。<br>' +
    '建议在 <strong>Strapi Content-Type Builder</strong> 中将该字段类型改为 <strong>Long text</strong>，重启 Strapi 后重试。';
  card.appendChild(detail);

  const actions = document.createElement('div');
  actions.className = 'varchar-error-actions';

  const btnTruncate = document.createElement('button');
  btnTruncate.className = 'btn-truncate';
  btnTruncate.textContent = '强制截断并继续';
  btnTruncate.onclick = () => {
    btnTruncate.disabled = true;
    btnTruncate.textContent = '重试中…';
    beginSSE('/api/localize/retry?' + buildParams([ev.locale]) + '&force_truncate=1', 1);
  };
  actions.appendChild(btnTruncate);

  card.appendChild(actions);
  b.appendChild(card);
  b.scrollTop = b.scrollHeight;
}

function addRetryBtn(locale, errMsg) {
  const list = document.getElementById('retryList');
  const item = document.createElement('div');
  item.className = 'retry-item'; item.id = 'retry-' + locale;
  item.innerHTML = '<span>' + locale + ': ' + errMsg.slice(0,50) + '</span>'
    + '<button class="btn-retry" onclick="retryLocale(this.dataset.locale)" data-locale="' + locale + '">↺ 重试</button>';
  list.appendChild(item);
}

function retryLocale(locale) {
  chipStates[locale] = 'sel';
  document.getElementById('retry-' + locale)?.remove();
  beginSSE('/api/localize/retry?' + buildParams([locale]), 1);
}

// ── 历史 ──
async function loadHistory() {
  const r = await fetch('/api/localize/history');
  const hist = await r.json();
  const el = document.getElementById('historyList');
  if (!hist.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div>暂无记录</div>';
    return;
  }
  el.innerHTML = hist.slice(0, 20).map(e => {
    const d = new Date(e.run_at).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    const tags = e.results.map(r =>
      '<span class="h-lang ' + (r.status==='fail'?'fail':'') + '">' + r.locale + '</span>'
    ).join('');
    const envBadge = '<span class="h-env-badge">' + e.env + '</span>';
    return '<div class="history-item">'
      + '<div><div class="h-title">' + e.page_title + '</div>'
      + '<div class="h-meta">' + d + ' · ' + e.results.length + ' 种 ' + envBadge + '</div></div>'
      + '<div class="history-langs">' + tags + '</div>'
      + '</div>';
  }).join('');
}
</script>
</body>
</html>"""
