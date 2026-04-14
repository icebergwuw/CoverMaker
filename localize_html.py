"""localize_html.py — Localize Tab 前端页面 HTML"""

LOCALIZE_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Localize</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #1a1a1a; color: #f0f0f0; font-family: -apple-system, sans-serif; min-height: 100vh; }

.top-nav { background: #242424; border-bottom: 1px solid #3a3a3a; padding: 0 24px; display: flex; align-items: center; height: 48px; }
.top-nav a { display: flex; align-items: center; height: 100%; padding: 0 16px; font-size: 13px; color: #666; text-decoration: none; border-bottom: 2px solid transparent; transition: color .15s; }
.top-nav a:hover { color: #aaa; }
.top-nav a.active { color: #4A8FA0; border-bottom-color: #4A8FA0; }

.page { max-width: 860px; margin: 0 auto; padding: 28px 24px; display: flex; flex-direction: column; gap: 20px; }
h1 { font-size: 20px; color: #4A8FA0; font-weight: 700; }
.section-title { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; }
label { font-size: 13px; color: #aaa; display: block; margin-bottom: 6px; }

input[type=text], select {
  width: 100%; background: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 6px;
  color: #f0f0f0; padding: 8px 10px; font-size: 14px; outline: none;
}
input[type=text]:focus, select:focus { border-color: #4A8FA0; }

.card { background: #242424; border: 1px solid #3a3a3a; border-radius: 10px; padding: 18px 20px; }

.env-row { display: flex; gap: 8px; }
.env-btn { flex: 1; padding: 7px; border: 1px solid #3a3a3a; border-radius: 6px; background: #2d2d2d; color: #777; font-size: 12px; font-weight: 600; cursor: pointer; transition: all .12s; }
.env-btn.active { background: #4A8FA0; color: #fff; border-color: #4A8FA0; }

.page-row { display: flex; gap: 8px; align-items: center; }
.page-row select { flex: 1; }
.btn-sm { background: #2d2d2d; color: #aaa; border: 1px solid #3a3a3a; border-radius: 6px; padding: 8px 14px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-sm:hover { background: #3a3a3a; color: #f0f0f0; }

.source-tabs { display: flex; gap: 6px; margin-bottom: 12px; }
.source-tab { padding: 6px 14px; border: 1px solid #3a3a3a; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; background: #2d2d2d; color: #777; }
.source-tab.active { background: #4A8FA0; color: #fff; border-color: #4A8FA0; }
.source-section { display: none; flex-direction: column; gap: 10px; }
.source-section.active { display: flex; }

.lang-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.lang-toolbar-actions { display: flex; gap: 10px; }
.lang-toolbar-actions button { background: none; border: none; color: #4A8FA0; font-size: 12px; cursor: pointer; padding: 0; }
.lang-toolbar-actions button:hover { text-decoration: underline; }
.lang-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 5px; }
.lang-chip {
  border: 1px solid #3a3a3a; border-radius: 5px; padding: 6px 2px;
  text-align: center; font-size: 12px; color: #666; cursor: pointer;
  background: #2d2d2d; user-select: none; transition: all .12s;
}
.lang-chip:hover:not(.done) { border-color: #4A8FA0; color: #4A8FA0; }
.lang-chip.done    { background: rgba(92,184,92,.12);  border-color: #3a6b3a; color: #5cb85c; cursor: default; }
.lang-chip.sel     { background: rgba(74,143,160,.18); border-color: #4A8FA0; color: #4A8FA0; }
.lang-chip.fail    { background: rgba(224,85,85,.12);  border-color: #6b3a3a; color: #e05555; }
.lang-chip.running { background: rgba(74,143,160,.35); border-color: #4A8FA0; color: #fff; animation: pulse .8s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:.65 } }
.lang-legend { font-size: 11px; color: #555; margin-top: 6px; }

.btn-run { background: #4A8FA0; color: #fff; border: none; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; transition: background .15s; }
.btn-run:hover:not(:disabled) { background: #3a7f90; }
.btn-run:disabled { background: #2d2d2d; color: #555; cursor: not-allowed; }

.progress-wrap { display: none; flex-direction: column; gap: 6px; margin-top: 14px; }
.progress-wrap.show { display: flex; }
.progress-bg { height: 4px; background: #2d2d2d; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #4A8FA0; border-radius: 2px; transition: width .3s; width: 0%; }
.progress-meta { display: flex; justify-content: space-between; font-size: 11px; color: #888; }

.log-box { display: none; background: #111; border-radius: 6px; padding: 10px 12px; font-family: 'SF Mono', Menlo, monospace; font-size: 12px; line-height: 1.9; max-height: 200px; overflow-y: auto; margin-top: 10px; }
.log-box.show { display: block; }
.log-ok   { color: #5cb85c; }
.log-run  { color: #4A8FA0; }
.log-warn { color: #f0ad4e; }
.log-err  { color: #e05555; }
.log-dim  { color: #555; }

.retry-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.retry-item { display: flex; align-items: center; gap: 6px; background: rgba(224,85,85,.08); border: 1px solid #6b3a3a; border-radius: 6px; padding: 5px 10px; font-size: 12px; color: #e05555; }
.btn-retry { background: #2d2d2d; border: 1px solid #6b5a2d; color: #f0ad4e; border-radius: 4px; font-size: 11px; padding: 3px 8px; cursor: pointer; }
.btn-retry:hover { background: #3a3a3a; }

.history-list { display: flex; flex-direction: column; }
.history-item { display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #2a2a2a; gap: 12px; }
.history-item:last-child { border-bottom: none; }
.h-title { font-size: 14px; font-weight: 600; }
.h-meta  { font-size: 11px; color: #555; margin-top: 3px; }
.history-langs { display: flex; flex-wrap: wrap; gap: 4px; justify-content: flex-end; max-width: 360px; }
.h-lang { font-size: 10px; background: rgba(92,184,92,.1); color: #5cb85c; border-radius: 3px; padding: 2px 5px; }
.h-lang.fail { background: rgba(224,85,85,.1); color: #e05555; }
.empty-state { text-align: center; color: #444; padding: 24px; font-size: 13px; }
</style>
</head>
<body>

<div class="top-nav">
  <a href="/">Cover Maker</a>
  <a href="/auto-publish">Auto Publish</a>
  <a href="/localize" class="active">🌐 Localize</a>
</div>

<div class="page">
  <h1>🌐 Localize</h1>

  <!-- 环境 -->
  <div class="card">
    <div class="section-title">环境</div>
    <div class="env-row">
      <button class="env-btn active" onclick="setEnv('test',this)">测试环境</button>
      <button class="env-btn" onclick="setEnv('prod',this)">正式环境</button>
    </div>
  </div>

  <!-- 文章 -->
  <div class="card">
    <div class="section-title">文章</div>
    <div class="page-row">
      <select id="pageSelect" onchange="onPageChange()">
        <option value="">-- 加载中... --</option>
      </select>
      <button class="btn-sm" onclick="loadPages()">刷新</button>
    </div>
  </div>

  <!-- 翻译来源 -->
  <div class="card">
    <div class="section-title">翻译来源</div>
    <div class="source-tabs">
      <button class="source-tab active" onclick="setSource('excel',this)">Excel</button>
      <button class="source-tab" onclick="setSource('ai',this)">AI 翻译（Gemini）</button>
    </div>
    <div class="source-section active" id="src-excel">
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
    <div class="source-section" id="src-ai">
      <div style="font-size:13px;color:#888;line-height:1.7">
        使用 Gemini API 自动翻译，无需 Excel。<br>适合没有翻译表的新文章。
      </div>
    </div>
  </div>

  <!-- 语言选择 -->
  <div class="card">
    <div class="section-title">目标语言</div>
    <div class="lang-toolbar">
      <span style="font-size:12px;color:#888" id="langCount">已选 0 种</span>
      <div class="lang-toolbar-actions">
        <button onclick="selectAll()">全选</button>
        <button onclick="selectNone()">清空</button>
        <button onclick="selectPending()">未做过的</button>
      </div>
    </div>
    <div class="lang-grid" id="langGrid"></div>
    <div class="lang-legend">绿=已完成 · 蓝=已选中 · 红=上次失败 · 点击切换选中</div>
  </div>

  <!-- 执行 -->
  <div class="card">
    <button class="btn-run" id="runBtn" onclick="startRun()" disabled>▶ 开始本地化</button>
    <div class="progress-wrap" id="progressWrap">
      <div class="progress-bg"><div class="progress-fill" id="progressFill"></div></div>
      <div class="progress-meta">
        <span id="progressText">0 / 0</span>
        <span id="progressCurrent"></span>
      </div>
    </div>
    <div class="log-box" id="logBox"></div>
    <div class="retry-list" id="retryList"></div>
  </div>

  <!-- 历史 -->
  <div class="card">
    <div class="section-title">历史记录</div>
    <div id="historyList" class="history-list">
      <div class="empty-state">暂无记录</div>
    </div>
  </div>
</div>

<script>
const ALL_LOCALES = ["fr","zh-Hant","es","de","pt","it","ja","ko","ar","id","vi","th","ms","tr","pl","nl","ro","hi"];
let currentEnv    = 'test';
let currentSource = 'excel';
let currentPage   = null;   // {id, title}
let chipStates    = {};     // locale -> '' | 'done' | 'sel' | 'fail' | 'running'
let runState      = null;
let activeSSE     = null;

window.onload = () => { buildLangGrid(); loadPages(); loadHistory(); };

// ── 环境 ──────────────────────────────────────────────
function setEnv(env, btn) {
  currentEnv = env;
  document.querySelectorAll('.env-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadPages();
}

// ── 翻译来源 ──────────────────────────────────────────
function setSource(src, btn) {
  currentSource = src;
  document.querySelectorAll('.source-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.source-section').forEach(s => s.classList.remove('active'));
  document.getElementById('src-' + src).classList.add('active');
}

// ── 文章列表 ──────────────────────────────────────────
async function loadPages() {
  const sel = document.getElementById('pageSelect');
  sel.innerHTML = '<option value="">-- 加载中... --</option>';
  try {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 15000);
    const r = await fetch('/api/localize/pages?env=' + currentEnv, {signal: ctrl.signal});
    clearTimeout(tid);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const pages = await r.json();
    if (pages.error) throw new Error(pages.error);
    if (!Array.isArray(pages) || pages.length === 0) {
      sel.innerHTML = '<option value="">-- 无文章（检查环境连接）--</option>';
      return;
    }
    sel.innerHTML = '<option value="">-- 选择文章 --</option>';
    pages.forEach(p => {
      const o = document.createElement('option');
      o.value = p.id;
      o.textContent = p.title + '  (id=' + p.id + ')';
      o.dataset.locales    = JSON.stringify(p.locales);
      o.dataset.title      = p.title;
      o.dataset.sheet_name = p.sheet_name || '';
      sel.appendChild(o);
    });
  } catch(e) {
    sel.innerHTML = '<option value="">-- 加载失败: ' + e.message + ' --</option>';
  }
}

function onPageChange() {
  const sel = document.getElementById('pageSelect');
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !opt.value) { currentPage = null; updateRunBtn(); return; }
  currentPage = { id: parseInt(opt.value), title: opt.dataset.title };
  const doneLocales = JSON.parse(opt.dataset.locales || '[]');
  const sheetName   = opt.dataset.sheet_name || '';

  // 自动填 sheet 名
  document.getElementById('sheetName').value = sheetName;

  // 无对应 sheet → 自动切换到 AI 翻译模式并提示
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

// ── 语言格子 ──────────────────────────────────────────
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
  document.getElementById('langCount').textContent = '已选 ' + cnt + ' 种';
}
function selectAll()     { ALL_LOCALES.forEach(l => { if (chipStates[l] !== 'done') chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }
function selectNone()    { ALL_LOCALES.forEach(l => { if (chipStates[l] === 'sel')  chipStates[l] = '';    }); refreshChips(); updateRunBtn(); }
function selectPending() { ALL_LOCALES.forEach(l => { if (!chipStates[l])           chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }

// ── 按钮状态 ──────────────────────────────────────────
function updateRunBtn() {
  const cnt = ALL_LOCALES.filter(l => chipStates[l] === 'sel').length;
  const btn = document.getElementById('runBtn');
  btn.disabled = !currentPage || cnt === 0;
  btn.textContent = cnt > 0 ? '▶ 开始本地化（' + cnt + ' 种语言）' : '▶ 开始本地化';
}

// ── 执行 ──────────────────────────────────────────────
function buildParams(locales) {
  return new URLSearchParams({
    page_id: currentPage.id, page_title: currentPage.title,
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
    case 'done':
      runState.done++;
      chipStates[ev.locale] = 'done'; refreshChips();
      log('✓ ' + ev.locale + ' (id=' + ev.new_id + ')', 'ok');
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
  document.getElementById('progressCurrent').textContent = cur ? '▶ ' + cur + '...' : '';
}

function log(msg, cls) {
  const b = document.getElementById('logBox');
  const d = document.createElement('div');
  d.className = 'log-' + cls; d.textContent = msg;
  b.appendChild(d); b.scrollTop = b.scrollHeight;
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

// ── 历史 ──────────────────────────────────────────────
async function loadHistory() {
  const r = await fetch('/api/localize/history');
  const hist = await r.json();
  const el = document.getElementById('historyList');
  if (!hist.length) { el.innerHTML = '<div class="empty-state">暂无记录</div>'; return; }
  el.innerHTML = hist.slice(0, 20).map(e => {
    const d = new Date(e.run_at).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    const tags = e.results.map(r =>
      '<span class="h-lang ' + (r.status==='fail'?'fail':'') + '">' + r.locale + '</span>'
    ).join('');
    return '<div class="history-item">'
      + '<div><div class="h-title">' + e.page_title + '</div>'
      + '<div class="h-meta">' + d + ' · ' + e.results.length + ' 种 · ' + e.env + '</div></div>'
      + '<div class="history-langs">' + tags + '</div>'
      + '</div>';
  }).join('');
}
</script>
</body>
</html>"""
