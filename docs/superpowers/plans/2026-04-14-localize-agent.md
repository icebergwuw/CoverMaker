# Localization Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 Flask app（:5299）新增第三个 Tab「🌐 Localize」，支持从 CMS 拉取文章列表、选择语言、批量本地化、SSE 实时日志、失败重试、历史记录。

**Architecture:** 新建 `localize_agent.py` 承载所有后端逻辑（CMS 拉取、SSE runner、history 读写、AI 翻译），`app.py` 只做路由注册和导航 tab 改动，前端 HTML 内嵌为 `LOCALIZE_HTML` 字符串常量（与现有 AUTO_PUBLISH_HTML 风格一致）。

**Tech Stack:** Python 3.9, Flask, SSE（`text/event-stream`），requests，openpyxl，现有 `localize_special_topic_page.py`

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `localize_agent.py` | 新建 | CMS pages 拉取、SSE 任务执行、history 读写、AI 翻译 |
| `app.py` | 修改 | 导航 tab + 4 个新路由注册 |
| `localize_history.json` | 新建（运行时自动创建） | 历史记录持久化 |

---

## Task 1: localize_agent.py — CMS pages 拉取 + history 读写

**Files:**
- Create: `cover-maker/localize_agent.py`

- [ ] **Step 1: 创建文件，写 fetch_pages()**

```python
#!/usr/bin/env python3
"""localize_agent.py — Localization Agent 后端逻辑"""
import os, json, re
from datetime import datetime, timezone
import requests

# ── 配置 ─────────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "localize_history.json")

ENV_CONFIG = {
    "test": {
        "base": "http://pdfagile-cms.aix-test-k8s.iweikan.cn",
        "token": os.environ.get(
            "CMS_TOKEN",
            "943d4d58e9c61ed7ed300b801991e19e4c0f5ff395577c340a187347b1670fcf4d9026a39eff43d63a9dae041afa582ae85db8148dcc80110db98f56a3129366df98f20ccc690264afd8f061fcee8fba747d2cc4ad13f1b59897e2bdcae1b2fb930aba1ee498f866e459905cf03b6b17f4fa955f34ea45e9f327d9b0ca7cb9d2",
        ),
    },
    "prod": {
        "base": "https://cms.pdfagile.com",
        "token": os.environ.get("CMS_TOKEN_PROD", ""),
    },
}

ALL_LOCALES = [
    "fr", "zh-Hant", "es", "de", "pt", "it",
    "ja", "ko", "ar", "id", "vi", "th",
    "ms", "tr", "pl", "nl", "ro", "hi",
]

def _env(env: str) -> dict:
    """返回指定环境的 {base, token}"""
    return ENV_CONFIG.get(env, ENV_CONFIG["test"])

def _headers(env: str) -> dict:
    return {"Authorization": f"Bearer {_env(env)['token']}"}

def _headers_json(env: str) -> dict:
    return {**_headers(env), "Content-Type": "application/json"}


def fetch_pages(env: str = "test") -> list:
    """
    从 CMS 拉取所有英文版 special-topic-pages。
    同时查询每篇文章已有哪些 locale 版本。
    返回: [{"id": 5, "title": "...", "slug": "...", "locales": ["fr","de",...]}]
    """
    cfg = _env(env)
    base = cfg["base"]
    resp = requests.get(
        f"{base}/api/special-topic-pages",
        params={"locale": "en", "pagination[pageSize]": 100, "fields[0]": "title", "fields[1]": "slug", "populate[localizations][fields][0]": "locale"},
        headers=_headers(env),
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    pages = []
    for item in data:
        attrs = item["attributes"]
        existing_locales = [
            loc["locale"]
            for loc in (attrs.get("localizations", {}).get("data") or [])
        ]
        pages.append({
            "id":      item["id"],
            "title":   attrs.get("title", ""),
            "slug":    attrs.get("slug", ""),
            "locales": existing_locales,
        })
    pages.sort(key=lambda x: x["title"])
    return pages
```

- [ ] **Step 2: 写 history 读写函数**

在同一文件追加：

```python
def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        return json.load(open(HISTORY_FILE, encoding="utf-8"))
    except Exception:
        return []

def save_history_entry(entry: dict):
    """追加一条 run 记录到 history 文件。"""
    history = load_history()
    history.insert(0, entry)          # 最新在前
    history = history[:200]           # 最多保留 200 条
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 3: 手动测试 fetch_pages()**

```bash
cd /Users/ice/Desktop/Project/CoverMaker\&AutoPublish/cover-maker
/usr/bin/python3 -c "
import localize_agent
pages = localize_agent.fetch_pages('test')
for p in pages[:3]:
    print(p)
"
```

期望输出：每行一个 dict，含 id/title/slug/locales。

- [ ] **Step 4: commit**

```bash
git add localize_agent.py
git commit -m "feat: add localize_agent.py with fetch_pages and history helpers"
```

---

## Task 2: localize_agent.py — SSE runner

**Files:**
- Modify: `cover-maker/localize_agent.py`

- [ ] **Step 1: 追加 SSE event 格式化函数 + run_localize_sse()**

```python
def _sse(data: dict) -> str:
    """格式化为 SSE data 行"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def run_localize_sse(
    page_id: int,
    page_title: str,
    locales: list,
    sheet_name: str,
    excel_path: str,
    translation_mode: str,   # "excel" | "ai"
    env: str,
):
    """
    Generator：逐 locale 执行 localize()，yield SSE 字符串。
    调用方用 Flask Response(stream_with_context(...), mimetype='text/event-stream')。
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import localize_special_topic_page as lsp

    # 临时替换 CMS_BASE / CMS_TOKEN（让 lsp 模块使用正确环境）
    cfg = _env(env)
    original_base  = lsp.CMS_BASE
    original_token = lsp.CMS_TOKEN
    lsp.CMS_BASE  = cfg["base"]
    lsp.CMS_TOKEN = cfg["token"]

    run_results = []
    total = len(locales)

    yield _sse({"type": "batch_start", "total": total})

    for i, locale in enumerate(locales):
        yield _sse({"type": "start", "locale": locale, "index": i + 1, "total": total})

        try:
            if translation_mode == "excel":
                if not excel_path or not os.path.exists(excel_path):
                    raise FileNotFoundError(f"Excel 文件不存在: {excel_path}")
                # 临时覆盖 EXCEL_PATH
                lsp.EXCEL_PATH = excel_path
                new_id = lsp.localize(
                    page_id=page_id,
                    locale=locale,
                    sheet_name=sheet_name,
                    publish=True,
                )
            else:
                # AI 翻译模式
                new_id = _run_ai_localize(page_id, locale, env, lsp)

            yield _sse({"type": "done", "locale": locale, "new_id": new_id})
            run_results.append({"locale": locale, "new_id": new_id, "status": "ok", "warnings": []})

        except Exception as e:
            err_msg = str(e)[:200]
            yield _sse({"type": "error", "locale": locale, "msg": err_msg})
            run_results.append({"locale": locale, "new_id": None, "status": "fail", "error": err_msg})

    # 恢复原始配置
    lsp.CMS_BASE  = original_base
    lsp.CMS_TOKEN = original_token

    ok   = sum(1 for r in run_results if r["status"] == "ok")
    fail = total - ok
    yield _sse({"type": "finished", "total": total, "ok": ok, "fail": fail})

    # 写入历史
    save_history_entry({
        "page_id":    page_id,
        "page_title": page_title,
        "sheet_name": sheet_name,
        "env":        env,
        "run_at":     datetime.now(timezone.utc).isoformat(),
        "results":    run_results,
    })


def _run_ai_localize(page_id: int, locale: str, env: str, lsp) -> int:
    """AI 翻译模式：用 Gemini 批量翻译英文文本，构造 t_map 后走同样流程。"""
    en_attrs  = lsp.fetch_en_page(page_id)
    en_blocks = en_attrs.get("blocks", [])

    # 收集所有需要翻译的文本
    texts = _collect_en_texts(en_blocks)
    t_map = _ai_translate_batch(texts, locale)

    # 走 localize() 同样的 POST + PUT 流程，但跳过 Excel
    # 直接调内部函数
    new_id = lsp._localize_with_tmap(
        page_id=page_id,
        locale=locale,
        en_attrs=en_attrs,
        en_blocks=en_blocks,
        t_map=t_map,
        publish=True,
    )
    return new_id


def _collect_en_texts(blocks: list) -> list:
    """从 blocks 收集所有需要翻译的文本字段（去重）。"""
    texts = set()
    TEXT_FIELDS = ("title", "text", "subtitle", "customizeText", "customizeTitle",
                   "topTitle", "question", "answer", "label")
    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in TEXT_FIELDS and isinstance(v, str) and v.strip():
                    plain = re.sub(r'<[^>]+>', '', v).strip()
                    if plain:
                        texts.add(plain)
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)
    for b in blocks:
        _walk(b)
    return list(texts)


def _ai_translate_batch(texts: list, locale: str) -> dict:
    """调 Gemini 批量翻译，返回 {en: translated} map。"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from auto_publish import gemini_ask

    LOCALE_NAMES = {
        "de": "German", "pt": "Portuguese", "it": "Italian",
        "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
        "id": "Indonesian", "vi": "Vietnamese", "th": "Thai",
        "ms": "Malay", "tr": "Turkish", "pl": "Polish",
        "nl": "Dutch", "ro": "Romanian", "hi": "Hindi",
        "fr": "French", "zh-Hant": "Traditional Chinese", "es": "Spanish",
    }
    lang_name = LOCALE_NAMES.get(locale, locale)

    # 分批，每批最多 40 条，避免 prompt 过长
    results = {}
    batch_size = 40
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_json = json.dumps(batch, ensure_ascii=False)
        prompt = f"""Translate the following PDF tool texts from English to {lang_name}.
Keep software names (PDF Agile, etc.) untranslated.
Return ONLY a JSON object mapping each English text to its translation.
No extra keys, no explanation.

English texts:
{batch_json}

Return format: {{"English text": "translated text", ...}}"""
        raw = gemini_ask(prompt, timeout=120)
        try:
            # 提取 JSON
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                results.update(json.loads(m.group()))
        except Exception:
            pass
    return results
```

- [ ] **Step 2: commit**

```bash
git add localize_agent.py
git commit -m "feat: add run_localize_sse and AI translate helpers to localize_agent"
```

---

## Task 3: localize_special_topic_page.py — 暴露 _localize_with_tmap()

AI 翻译模式需要能传入外部 t_map 跳过 Excel 读取。需要把 `localize()` 内部的核心执行逻辑抽成可复用函数。

**Files:**
- Modify: `cover-maker/localize_special_topic_page.py`

- [ ] **Step 1: 在 localize() 内找到核心执行部分，抽出 _localize_with_tmap()**

在文件末尾（`if __name__ == "__main__":` 之前）追加：

```python
def _localize_with_tmap(
    page_id: int,
    locale: str,
    en_attrs: dict,
    en_blocks: list,
    t_map: dict,
    publish: bool = True,
) -> int:
    """
    使用已构建好的 t_map 执行本地化（跳过 Excel 读取）。
    供 localize_agent.py 的 AI 翻译模式调用。
    返回新建页面的 id。
    """
    from datetime import datetime, timezone

    print(f"\n=== _localize_with_tmap ===")
    print(f"  page_id : {page_id}")
    print(f"  locale  : {locale}")
    print(f"  t_map   : {len(t_map)} 条")

    # 构建 POST payload
    blocks_payload = []
    for block in en_blocks:
        blocks_payload.append(convert_block(block, t_map))

    slug = en_attrs["slug"] + f"-{locale}"
    title_en = en_attrs.get("title", "")

    post_payload = {
        "locale": locale,
        "slug": slug,
        "title": translate(title_en, t_map),
        "blocks": blocks_payload,
    }

    # POST 创建 localization
    resp = requests.post(
        f"{CMS_BASE}/api/special-topic-pages/{page_id}/localizations",
        headers=headers_json(),
        json=post_payload,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"POST failed {resp.status_code}: {resp.text[:200]}")

    result = resp.json()
    new_id = result.get("id")
    print(f"  创建成功！新 id = {new_id}")

    # PUT 补全并发布
    fr_blocks = fetch_fr_blocks(new_id)
    patch_blocks = build_patch_blocks(fr_blocks, en_blocks, t_map)

    from datetime import datetime, timezone
    published_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z") if publish else None
    patch_payload = {"data": {"blocks": patch_blocks}}
    if published_at:
        patch_payload["data"]["publishedAt"] = published_at

    patch_resp = requests.put(
        f"{CMS_BASE}/api/special-topic-pages/{new_id}",
        headers=headers_json(),
        json=patch_payload,
    )
    if patch_resp.status_code != 200:
        raise RuntimeError(f"PUT failed {patch_resp.status_code}: {patch_resp.text[:200]}")

    print(f"  补全成功！publishedAt = {patch_resp.json()['data']['attributes'].get('publishedAt')}")

    # verify
    verify(new_id, en_blocks, locale, t_map)

    return new_id
```

- [ ] **Step 2: 手动测试（dry run，不实际 POST）**

```bash
cd /Users/ice/Desktop/Project/CoverMaker\&AutoPublish/cover-maker
/usr/bin/python3 -c "
import localize_special_topic_page as lsp
print('_localize_with_tmap exists:', hasattr(lsp, '_localize_with_tmap'))
"
```

期望：`_localize_with_tmap exists: True`

- [ ] **Step 3: commit**

```bash
git add localize_special_topic_page.py
git commit -m "feat: expose _localize_with_tmap() for AI translation mode"
```

---

## Task 4: app.py — 注册路由 + 导航 tab

**Files:**
- Modify: `cover-maker/app.py`

- [ ] **Step 1: 在 import 区新增 localize_agent 导入**

在 `app.py` 顶部 import 区（`from make_howtotips2_cover import ...` 之后）追加：

```python
import localize_agent
```

- [ ] **Step 2: 在 Cover Maker HTML 的导航里加 Localize tab 链接**

找到：
```python
<a href="/auto-publish" style="display:block;background:#2d2d2d;border:1px solid #3a3a3a;border-radius:8px;padding:10px 14px;font-size:13px;color:#4A8FA0;text-decoration:none;text-align:center;">🚀 Auto Publish — 全自动抓热点发文</a>
```

替换为：
```python
<div style="display:flex;flex-direction:column;gap:8px;">
  <a href="/auto-publish" style="display:block;background:#2d2d2d;border:1px solid #3a3a3a;border-radius:8px;padding:10px 14px;font-size:13px;color:#4A8FA0;text-decoration:none;text-align:center;">🚀 Auto Publish — 全自动抓热点发文</a>
  <a href="/localize"     style="display:block;background:#2d2d2d;border:1px solid #3a3a3a;border-radius:8px;padding:10px 14px;font-size:13px;color:#4A8FA0;text-decoration:none;text-align:center;">🌐 Localize — 多语言本地化</a>
</div>
```

- [ ] **Step 3: 在 app.py 末尾（`if __name__ == "__main__":` 之前）注册4个路由**

```python
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
    page_id          = int(request.args.get("page_id"))
    page_title       = request.args.get("page_title", "")
    locales          = request.args.get("locales", "").split(",")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")

    gen = localize_agent.run_localize_sse(
        page_id=page_id,
        page_title=page_title,
        locales=locales,
        sheet_name=sheet_name,
        excel_path=excel_path,
        translation_mode=translation_mode,
        env=env,
    )
    return Response(stream_with_context(gen), mimetype="text/event-stream")

@app.route("/api/localize/retry")
def api_localize_retry():
    from flask import Response, stream_with_context
    page_id          = int(request.args.get("page_id"))
    page_title       = request.args.get("page_title", "")
    locale           = request.args.get("locale")
    sheet_name       = request.args.get("sheet_name", "")
    excel_path       = request.args.get("excel_path", "")
    translation_mode = request.args.get("translation_mode", "excel")
    env              = request.args.get("env", "test")

    gen = localize_agent.run_localize_sse(
        page_id=page_id,
        page_title=page_title,
        locales=[locale],
        sheet_name=sheet_name,
        excel_path=excel_path,
        translation_mode=translation_mode,
        env=env,
    )
    return Response(stream_with_context(gen), mimetype="text/event-stream")
```

- [ ] **Step 4: 更新 startup 打印信息**

找到：
```python
print("Auto Publish  → http://127.0.0.1:5299/auto-publish")
```

改为：
```python
print("Auto Publish  → http://127.0.0.1:5299/auto-publish")
print("Localize      → http://127.0.0.1:5299/localize")
```

- [ ] **Step 5: commit**

```bash
git add app.py
git commit -m "feat: register localize routes and add nav link in app.py"
```

---

## Task 5: localize_html.py — 前端页面

**Files:**
- Create: `cover-maker/localize_html.py`

- [ ] **Step 1: 创建文件，写完整 LOCALIZE_HTML**

```python
"""localize_html.py — Localize Tab 前端页面 HTML"""

LOCALIZE_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Localize</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #1a1a1a; color: #f0f0f0; font-family: -apple-system, sans-serif; min-height: 100vh; }

/* ── 顶部导航 ── */
.top-nav { background: #242424; border-bottom: 1px solid #3a3a3a; padding: 0 24px; display: flex; align-items: center; gap: 0; height: 48px; }
.top-nav a { display: flex; align-items: center; height: 100%; padding: 0 16px; font-size: 13px; color: #666; text-decoration: none; border-bottom: 2px solid transparent; transition: color .15s; }
.top-nav a:hover { color: #aaa; }
.top-nav a.active { color: #4A8FA0; border-bottom-color: #4A8FA0; }

/* ── 主体布局 ── */
.page { max-width: 860px; margin: 0 auto; padding: 28px 24px; display: flex; flex-direction: column; gap: 20px; }

h1 { font-size: 20px; color: #4A8FA0; font-weight: 700; }
.section-title { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; }
label { font-size: 13px; color: #aaa; display: block; margin-bottom: 6px; }

input[type=text], select {
  width: 100%; background: #2d2d2d; border: 1px solid #3a3a3a; border-radius: 6px;
  color: #f0f0f0; padding: 8px 10px; font-size: 14px; outline: none;
}
input[type=text]:focus, select:focus { border-color: #4A8FA0; }

/* ── 卡片 ── */
.card { background: #242424; border: 1px solid #3a3a3a; border-radius: 10px; padding: 18px 20px; }

/* ── 环境切换 ── */
.env-row { display: flex; gap: 8px; }
.env-btn { flex: 1; padding: 7px; border: 1px solid #3a3a3a; border-radius: 6px; background: #2d2d2d; color: #777; font-size: 12px; font-weight: 600; cursor: pointer; }
.env-btn.active { background: #4A8FA0; color: #fff; border-color: #4A8FA0; }

/* ── 文章选择行 ── */
.page-row { display: flex; gap: 8px; align-items: center; }
.page-row select { flex: 1; }
.btn-sm { background: #2d2d2d; color: #aaa; border: 1px solid #3a3a3a; border-radius: 6px; padding: 8px 14px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-sm:hover { background: #3a3a3a; color: #f0f0f0; }

/* ── 翻译来源 ── */
.source-tabs { display: flex; gap: 6px; margin-bottom: 12px; }
.source-tab { padding: 6px 14px; border: 1px solid #3a3a3a; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; background: #2d2d2d; color: #777; }
.source-tab.active { background: #4A8FA0; color: #fff; border-color: #4A8FA0; }
.source-section { display: none; flex-direction: column; gap: 10px; }
.source-section.active { display: flex; }
.two-col { display: grid; grid-template-columns: 1fr 140px; gap: 8px; }

/* ── 语言格子 ── */
.lang-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.lang-toolbar-actions { display: flex; gap: 10px; }
.lang-toolbar-actions button { background: none; border: none; color: #4A8FA0; font-size: 12px; cursor: pointer; padding: 0; }
.lang-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 5px; }
.lang-chip {
  border: 1px solid #3a3a3a; border-radius: 5px; padding: 5px 2px;
  text-align: center; font-size: 12px; color: #666; cursor: pointer;
  background: #2d2d2d; user-select: none; transition: all .12s; position: relative;
}
.lang-chip:hover { border-color: #4A8FA0; color: #4A8FA0; }
.lang-chip.done  { background: rgba(92,184,92,.12); border-color: #3a6b3a; color: #5cb85c; cursor: default; }
.lang-chip.sel   { background: rgba(74,143,160,.18); border-color: #4A8FA0; color: #4A8FA0; }
.lang-chip.fail  { background: rgba(224,85,85,.12); border-color: #6b3a3a; color: #e05555; }
.lang-chip.running { background: rgba(74,143,160,.3); border-color: #4A8FA0; color: #fff; }
.lang-legend { font-size: 11px; color: #555; margin-top: 6px; }

/* ── 执行区 ── */
.btn-run { background: #4A8FA0; color: #fff; border: none; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; }
.btn-run:hover { background: #3a7f90; }
.btn-run:disabled { background: #2d2d2d; color: #555; cursor: not-allowed; }

.progress-wrap { display: none; flex-direction: column; gap: 5px; }
.progress-wrap.show { display: flex; }
.progress-bg { height: 4px; background: #2d2d2d; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #4A8FA0; border-radius: 2px; transition: width .3s; width: 0%; }
.progress-meta { display: flex; justify-content: space-between; font-size: 11px; color: #888; }

.log-box { display: none; background: #111; border-radius: 6px; padding: 10px 12px; font-family: 'SF Mono', 'Menlo', monospace; font-size: 12px; line-height: 1.8; max-height: 180px; overflow-y: auto; }
.log-box.show { display: block; }
.log-ok   { color: #5cb85c; }
.log-run  { color: #4A8FA0; }
.log-warn { color: #f0ad4e; }
.log-err  { color: #e05555; }
.log-dim  { color: #555; }

/* ── 失败重试 ── */
.retry-list { display: flex; flex-wrap: wrap; gap: 8px; }
.retry-item { display: flex; align-items: center; gap: 6px; background: rgba(224,85,85,.08); border: 1px solid #6b3a3a; border-radius: 6px; padding: 5px 10px; font-size: 12px; color: #e05555; }
.btn-retry { background: #2d2d2d; border: 1px solid #6b5a2d; color: #f0ad4e; border-radius: 4px; font-size: 11px; padding: 3px 8px; cursor: pointer; }
.btn-retry:hover { background: #3a3a3a; }

/* ── 历史记录 ── */
.history-list { display: flex; flex-direction: column; gap: 1px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #2d2d2d; }
.history-item:last-child { border-bottom: none; }
.history-left .h-title { font-size: 14px; font-weight: 600; }
.history-left .h-meta  { font-size: 11px; color: #555; margin-top: 2px; }
.history-langs { display: flex; flex-wrap: wrap; gap: 4px; }
.h-lang { font-size: 10px; background: rgba(92,184,92,.1); color: #5cb85c; border-radius: 3px; padding: 2px 5px; }
.h-lang.fail { background: rgba(224,85,85,.1); color: #e05555; }

.empty-state { text-align: center; color: #444; padding: 24px; font-size: 13px; }
</style>
</head>
<body>

<!-- 顶部导航 -->
<div class="top-nav">
  <a href="/">Cover Maker</a>
  <a href="/auto-publish">Auto Publish</a>
  <a href="/localize" class="active">🌐 Localize</a>
</div>

<div class="page">
  <h1>🌐 Localize</h1>

  <!-- 环境切换 -->
  <div class="card">
    <div class="section-title">环境</div>
    <div class="env-row">
      <button class="env-btn active" id="envTest" onclick="setEnv('test', this)">测试环境</button>
      <button class="env-btn" id="envProd" onclick="setEnv('prod', this)">正式环境</button>
    </div>
  </div>

  <!-- 文章选择 -->
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
      <button class="source-tab active" onclick="setSource('excel', this)">Excel</button>
      <button class="source-tab" onclick="setSource('ai', this)">AI 翻译（Gemini）</button>
    </div>
    <div class="source-section active" id="src-excel">
      <div>
        <label>Excel 文件路径</label>
        <input type="text" id="excelPath" value="/Users/ice/Downloads/专题页文案与多语言本地化-更新至20260408.xlsx" placeholder="/path/to/file.xlsx">
      </div>
      <div>
        <label>Sheet 名称</label>
        <input type="text" id="sheetName" placeholder="Organize PDF">
      </div>
    </div>
    <div class="source-section" id="src-ai">
      <div style="font-size:13px;color:#888;line-height:1.6">
        使用 Gemini API 自动翻译，无需 Excel。<br>
        适合没有翻译表的新文章。
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
    <div class="lang-legend">绿=已完成 · 蓝=已选中 · 红=上次失败 · 点击切换</div>
  </div>

  <!-- 执行 -->
  <div class="card">
    <button class="btn-run" id="runBtn" onclick="startRun()" disabled>▶ 开始本地化</button>
    <div style="height:12px"></div>
    <div class="progress-wrap" id="progressWrap">
      <div class="progress-bg"><div class="progress-fill" id="progressFill"></div></div>
      <div class="progress-meta"><span id="progressText">0 / 0</span><span id="progressCurrent"></span></div>
    </div>
    <div class="log-box" id="logBox"></div>
    <div id="retryList" class="retry-list" style="margin-top:10px"></div>
  </div>

  <!-- 历史记录 -->
  <div class="card">
    <div class="section-title">历史记录</div>
    <div id="historyList" class="history-list">
      <div class="empty-state">暂无记录</div>
    </div>
  </div>
</div>

<script>
const ALL_LOCALES = ["fr","zh-Hant","es","de","pt","it","ja","ko","ar","id","vi","th","ms","tr","pl","nl","ro","hi"];
let currentEnv = 'test';
let currentSource = 'excel';
let pages = [];
let currentPage = null;
let chipStates = {};   // locale -> 'done'|'fail'|'sel'|''
let runState = null;   // {total, done, fails:[]}
let activeSSE = null;

// ── 初始化 ──
window.onload = () => {
  buildLangGrid();
  loadPages();
  loadHistory();
};

// ── 环境 ──
function setEnv(env, btn) {
  currentEnv = env;
  document.querySelectorAll('.env-btn').forEach(b => b.classList.remove('active'));
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
  sel.innerHTML = '<option value="">-- 加载中... --</option>';
  try {
    const resp = await fetch('/api/localize/pages?env=' + currentEnv);
    pages = await resp.json();
    if (pages.error) throw new Error(pages.error);
    sel.innerHTML = '<option value="">-- 选择文章 --</option>';
    pages.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.title + '  (id=' + p.id + ')';
      opt.dataset.locales = JSON.stringify(p.locales);
      opt.dataset.title = p.title;
      sel.appendChild(opt);
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
  // 自动填 sheet 名（与 title 同名）
  document.getElementById('sheetName').value = opt.dataset.title;
  // 更新格子状态
  ALL_LOCALES.forEach(l => {
    chipStates[l] = doneLocales.includes(l) ? 'done' : '';
  });
  refreshChips();
  updateRunBtn();
}

// ── 语言格子 ──
function buildLangGrid() {
  const grid = document.getElementById('langGrid');
  grid.innerHTML = '';
  ALL_LOCALES.forEach(l => {
    const chip = document.createElement('div');
    chip.className = 'lang-chip';
    chip.id = 'chip-' + l;
    chip.textContent = l;
    chip.onclick = () => toggleChip(l);
    grid.appendChild(chip);
  });
}

function toggleChip(locale) {
  const s = chipStates[locale];
  if (s === 'done') return;  // 已完成不可切换
  chipStates[locale] = (s === 'sel') ? '' : 'sel';
  refreshChips();
  updateRunBtn();
}

function refreshChips() {
  let selCount = 0;
  ALL_LOCALES.forEach(l => {
    const chip = document.getElementById('chip-' + l);
    chip.className = 'lang-chip ' + (chipStates[l] || '');
    if (chipStates[l] === 'sel') selCount++;
  });
  document.getElementById('langCount').textContent = '已选 ' + selCount + ' 种';
}

function selectAll()     { ALL_LOCALES.forEach(l => { if (chipStates[l] !== 'done') chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }
function selectNone()    { ALL_LOCALES.forEach(l => { if (chipStates[l] === 'sel') chipStates[l] = ''; }); refreshChips(); updateRunBtn(); }
function selectPending() { ALL_LOCALES.forEach(l => { if (!chipStates[l]) chipStates[l] = 'sel'; }); refreshChips(); updateRunBtn(); }

// ── 执行按钮 ──
function updateRunBtn() {
  const selCount = ALL_LOCALES.filter(l => chipStates[l] === 'sel').length;
  const btn = document.getElementById('runBtn');
  btn.disabled = !currentPage || selCount === 0;
  btn.textContent = selCount > 0 ? '▶ 开始本地化（' + selCount + ' 种语言）' : '▶ 开始本地化';
}

// ── 执行 ──
function startRun() {
  const locales = ALL_LOCALES.filter(l => chipStates[l] === 'sel');
  if (!locales.length || !currentPage) return;

  const params = buildParams(locales);
  beginSSE('/api/localize/run?' + params, locales.length);
}

function buildParams(locales) {
  const p = new URLSearchParams({
    page_id:          currentPage.id,
    page_title:       currentPage.title,
    locales:          locales.join(','),
    sheet_name:       document.getElementById('sheetName').value.trim(),
    excel_path:       document.getElementById('excelPath').value.trim(),
    translation_mode: currentSource,
    env:              currentEnv,
  });
  return p.toString();
}

function beginSSE(url, total) {
  if (activeSSE) { activeSSE.close(); }

  document.getElementById('runBtn').disabled = true;
  document.getElementById('progressWrap').classList.add('show');
  document.getElementById('logBox').classList.add('show');
  document.getElementById('logBox').innerHTML = '';
  document.getElementById('retryList').innerHTML = '';

  runState = { total, done: 0, fails: [] };
  updateProgress(0, total, '');

  activeSSE = new EventSource(url);
  activeSSE.onmessage = e => handleSSE(JSON.parse(e.data));
  activeSSE.onerror = () => { activeSSE.close(); appendLog('连接中断', 'err'); };
}

function handleSSE(ev) {
  switch(ev.type) {
    case 'start':
      appendLog('▶ ' + ev.locale + ' (' + ev.index + '/' + ev.total + ')...', 'run');
      chipStates[ev.locale] = 'running';
      refreshChips();
      updateProgress(runState.done, runState.total, ev.locale);
      break;
    case 'progress':
      appendLog('  ' + ev.msg, 'dim');
      break;
    case 'done':
      runState.done++;
      chipStates[ev.locale] = 'done';
      refreshChips();
      appendLog('✓ ' + ev.locale + ' (id=' + ev.new_id + ')', 'ok');
      updateProgress(runState.done, runState.total, '');
      break;
    case 'error':
      runState.done++;
      runState.fails.push({locale: ev.locale, msg: ev.msg});
      chipStates[ev.locale] = 'fail';
      refreshChips();
      appendLog('✗ ' + ev.locale + ': ' + ev.msg, 'err');
      updateProgress(runState.done, runState.total, '');
      addRetryButton(ev.locale, ev.msg);
      break;
    case 'finished':
      activeSSE.close();
      document.getElementById('runBtn').disabled = false;
      appendLog('── 完成 ' + ev.ok + '/' + ev.total + ' ──', ev.fail > 0 ? 'warn' : 'ok');
      loadHistory();
      break;
  }
}

function updateProgress(done, total, current) {
  const pct = total > 0 ? Math.round(done / total * 100) : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressText').textContent = done + ' / ' + total;
  document.getElementById('progressCurrent').textContent = current ? '▶ ' + current + '...' : '';
}

function appendLog(msg, cls) {
  const box = document.getElementById('logBox');
  const line = document.createElement('div');
  line.className = 'log-' + cls;
  line.textContent = msg;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

function addRetryButton(locale, errMsg) {
  const list = document.getElementById('retryList');
  const item = document.createElement('div');
  item.className = 'retry-item';
  item.id = 'retry-' + locale;
  item.innerHTML = '<span>' + locale + ': ' + errMsg.slice(0, 40) + '</span>'
    + '<button class="btn-retry" onclick="retryLocale(\'' + locale + '\')">↺ 重试</button>';
  list.appendChild(item);
}

function retryLocale(locale) {
  chipStates[locale] = 'sel';
  document.getElementById('retry-' + locale)?.remove();
  const params = buildParams([locale]);
  beginSSE('/api/localize/retry?' + params, 1);
}

// ── 历史记录 ──
async function loadHistory() {
  const resp = await fetch('/api/localize/history');
  const history = await resp.json();
  const container = document.getElementById('historyList');
  if (!history.length) {
    container.innerHTML = '<div class="empty-state">暂无记录</div>';
    return;
  }
  container.innerHTML = history.slice(0, 20).map(entry => {
    const date = new Date(entry.run_at).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    const langTags = entry.results.map(r =>
      '<span class="h-lang ' + (r.status === 'fail' ? 'fail' : '') + '">' + r.locale + '</span>'
    ).join('');
    return '<div class="history-item">'
      + '<div class="history-left">'
      + '<div class="h-title">' + entry.page_title + '</div>'
      + '<div class="h-meta">' + date + ' · ' + entry.results.length + ' 种语言 · ' + entry.env + '</div>'
      + '</div>'
      + '<div class="history-langs">' + langTags + '</div>'
      + '</div>';
  }).join('');
}
</script>
</body>
</html>"""
```

- [ ] **Step 2: commit**

```bash
git add localize_html.py
git commit -m "feat: add localize_html.py with full Localize Tab UI"
```

---

## Task 6: 集成测试

**Files:** 无新文件

- [ ] **Step 1: 启动服务**

```bash
cd /Users/ice/Desktop/Project/CoverMaker\&AutoPublish/cover-maker
/usr/bin/python3 app.py
```

期望输出包含：
```
Cover Maker 启动中 → http://127.0.0.1:5299
Auto Publish  → http://127.0.0.1:5299/auto-publish
Localize      → http://127.0.0.1:5299/localize
```

- [ ] **Step 2: 测试 /api/localize/pages**

```bash
curl -s "http://127.0.0.1:5299/api/localize/pages?env=test" | /usr/bin/python3 -c "
import sys, json
pages = json.load(sys.stdin)
print(f'共 {len(pages)} 篇文章')
print(pages[0])
"
```

期望：打印文章数量和第一篇文章的 dict。

- [ ] **Step 3: 浏览器访问 http://127.0.0.1:5299/localize**

核对：
- 顶部三个 tab，Localize 高亮
- 文章下拉自动加载
- 语言格子 18 个，已完成的显示绿色
- 执行按钮默认禁用
- 历史记录显示（空或有数据）

- [ ] **Step 4: 用测试环境跑一个单语言验证 SSE 流**

选 Organize PDF，只勾 `hi`（印地语，已存在会报错），观察日志是否正确显示错误和重试按钮。

或者找一篇**没有 hi 版本**的文章跑一个语言，验证完整流程。

- [ ] **Step 5: commit**

```bash
git add -A
git commit -m "feat: localize agent tab complete - excel mode + SSE + history + retry"
```

---

## Task 7: 正式环境支持（明天）

**Files:**
- Modify: `cover-maker/localize_agent.py`

- [ ] **Step 1: 收到正式 token 后更新 ENV_CONFIG**

在 `localize_agent.py` 里找到：
```python
"prod": {
    "base": "https://cms.pdfagile.com",
    "token": os.environ.get("CMS_TOKEN_PROD", ""),
},
```

设置环境变量（不改代码，用 .env 或命令行）：
```bash
export CMS_TOKEN_PROD="<正式环境token>"
```

- [ ] **Step 2: 测试正式环境 pages 拉取**

```bash
CMS_TOKEN_PROD="<token>" /usr/bin/python3 -c "
import localize_agent
pages = localize_agent.fetch_pages('prod')
print(f'正式环境 {len(pages)} 篇文章')
"
```

- [ ] **Step 3: commit（仅 .env 文件，不提交 token 明文）**

```bash
# .env 加入 .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: add .env to gitignore for prod token safety"
```
