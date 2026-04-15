#!/usr/bin/env python3
"""localize_agent.py — Localization Agent 后端逻辑"""
import os, json, re
from datetime import datetime, timezone
import requests

# ── 配置 ─────────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "localize_history.json")

ENV_CONFIG = {
    "test": {
        "base": os.environ.get("CMS_BASE_TEST", "http://pdfagile-cms.aix-test-k8s.iweikan.cn"),
        "token": os.environ.get("CMS_TOKEN_TEST", ""),
    },
    "prod": {
        "base": os.environ.get("CMS_BASE_PROD", "https://cms.pdfagile.com"),
        "token": os.environ.get("CMS_TOKEN_PROD", ""),
    },
}

FE_BASE = {
    "test": "http://pdfagile-fe.aix-test-k8s.iweikan.cn",
    "prod": "https://www.pdfagile.com",
}

ALL_LOCALES = [
    "fr", "zh-Hant", "es", "de", "pt", "it",
    "ja", "ko", "ar", "id", "vi", "th",
    "ms", "tr", "pl", "nl", "ro", "hi",
]

# slug → Excel sheet 名映射（名称不一致的手动维护）
SLUG_TO_SHEET: dict = {
    "extract-data-from-pdf":     "Extract Data from PDF",
    "edit-pdf-like-powerpoint":  "Edit PDF like PowerPoint",
    "remove-watermark-from-pdf": "Watermark PDF",
    "password-protect-pdf":      "Password Protect PDF",
    "pdf-annotator":             "PDF Annotator",
    "pdf-printer":               "PDF Printer",
    "organize-pdf":              "Organize PDF",
    "adobe-acrobat-alternative": "Adobe Acrobat Alternative",
    "pdf-converter":             "PDF Converter",
    "esign-pdfs-legally":        "eSign PDFs Legally",
    "pdf-maker":                 "PDF Maker",
    "take-a-screenshot-in-pdf":  "Screenshot",
    "pdf-reader":                "PDF Reader",
}


def _env(env: str) -> dict:
    return ENV_CONFIG.get(env, ENV_CONFIG["test"])

def _headers(env: str) -> dict:
    return {"Authorization": f"Bearer {_env(env)['token']}"}

def _headers_json(env: str) -> dict:
    return {**_headers(env), "Content-Type": "application/json"}


# ── CMS pages 拉取 ────────────────────────────────────────

def _slug_to_title(slug: str) -> str:
    """把 slug 转成可读标题，如 'organize-pdf' → 'Organize PDF'"""
    return " ".join(w.upper() if w.lower() == "pdf" else w.capitalize() for w in slug.split("-"))


def fetch_pages(env: str = "test") -> list:
    """
    从 CMS 拉取所有英文版 special-topic-pages（含已有 locale 信息）。

    使用 publicationState=preview 拉取包含 draft 的英文版列表，
    再对每篇文章查询已有的 locale 版本。

    返回: [{"id": 5, "title": "Organize PDF", "slug": "organize-pdf", "locales": ["fr","de",...]}]
    """
    cfg = _env(env)
    base = cfg["base"]

    # 1. 拉取英文版（含 draft）
    url = (
        f"{base}/api/special-topic-pages"
        "?locale=en&publicationState=preview&pagination[pageSize]=100&populate=localizations"
    )
    resp = requests.get(url, headers=_headers(env), timeout=20)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    pages = []
    for item in data:
        attrs = item["attributes"]
        slug = attrs.get("slug", "")
        # title 在测试环境可能为 None，用 slug 推断
        title = attrs.get("title") or _slug_to_title(slug)

        locs_data = attrs.get("localizations", {}).get("data") or []
        existing_locales = [
            l["attributes"].get("locale", "")
            for l in locs_data
            if l["attributes"].get("locale")
        ]

        pages.append({
            "id":         item["id"],
            "title":      title,
            "slug":       slug,
            "locales":    existing_locales,
            "sheet_name": SLUG_TO_SHEET.get(slug, ""),   # 对应 Excel sheet，空=无sheet
        })

    pages.sort(key=lambda x: x["title"])
    return pages


# ── 历史记录 ─────────────────────────────────────────────

def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        return json.load(open(HISTORY_FILE, encoding="utf-8"))
    except Exception:
        return []

def save_history_entry(entry: dict):
    history = load_history()
    history.insert(0, entry)
    history = history[:200]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ── SSE helpers ───────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ── SSE runner ────────────────────────────────────────────

def run_localize_sse(
    page_id: int,
    page_title: str,
    page_slug: str,
    locales: list,
    sheet_name: str,
    excel_path: str,
    translation_mode: str,
    env: str,
    force_truncate: bool = False,
):
    """
    Generator：逐 locale 执行本地化，yield SSE 字符串。
    Flask 用 Response(stream_with_context(gen), mimetype='text/event-stream')。
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import localize_special_topic_page as lsp

    # 临时切换环境
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
                lsp.EXCEL_PATH = excel_path
                new_id = lsp.localize(
                    page_id=page_id,
                    locale=locale,
                    sheet_name=sheet_name,
                    publish=True,
                    force_truncate=force_truncate,
                )
            else:
                new_id = _run_ai_localize(page_id, locale, env, lsp)

            yield _sse({"type": "done", "locale": locale, "new_id": new_id,
                        "fe_url": f"{FE_BASE.get(env, '')}/{locale}/features/{page_slug}"})
            run_results.append({"locale": locale, "new_id": new_id, "status": "ok", "warnings": []})

        except lsp.VarcharTooLongError as e:
            yield _sse({
                "type":   "varchar_error",
                "locale": locale,
                "field":  e.field,
                "length": e.length,
                "limit":  e.limit,
                "msg":    str(e),
            })
            run_results.append({"locale": locale, "new_id": None, "status": "fail", "error": str(e)})

        except Exception as e:
            err_msg = str(e)[:200]
            yield _sse({"type": "error", "locale": locale, "msg": err_msg})
            run_results.append({"locale": locale, "new_id": None, "status": "fail", "error": err_msg})

    # 恢复环境
    lsp.CMS_BASE  = original_base
    lsp.CMS_TOKEN = original_token

    ok   = sum(1 for r in run_results if r["status"] == "ok")
    fail = total - ok
    yield _sse({"type": "finished", "total": total, "ok": ok, "fail": fail})

    save_history_entry({
        "page_id":    page_id,
        "page_title": page_title,
        "sheet_name": sheet_name,
        "env":        env,
        "run_at":     datetime.now(timezone.utc).isoformat(),
        "results":    run_results,
    })


# ── AI 翻译模式 ───────────────────────────────────────────

def _run_ai_localize(page_id: int, locale: str, env: str, lsp) -> int:
    en_attrs  = lsp.fetch_en_page(page_id)
    en_blocks = en_attrs.get("blocks", [])
    texts = _collect_en_texts(en_blocks)
    t_map = _ai_translate_batch(texts, locale)
    return lsp._localize_with_tmap(
        page_id=page_id,
        locale=locale,
        en_attrs=en_attrs,
        en_blocks=en_blocks,
        t_map=t_map,
        publish=True,
    )


def _collect_en_texts(blocks: list) -> list:
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
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                results.update(json.loads(m.group()))
        except Exception:
            pass
    return results
