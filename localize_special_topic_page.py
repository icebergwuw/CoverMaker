#!/usr/bin/env python3
"""
localize_special_topic_page.py
将 special-topic-page 从英文版创建指定语言的 localization。

用法:
    python3 localize_special_topic_page.py <en_page_id> <locale> <excel_sheet_name>

示例:
    python3 localize_special_topic_page.py 5 fr "Organize PDF"

逻辑:
  1. 拉取英文版完整结构（含所有嵌套字段、图片 id、buttons 等）
  2. 读取 Excel 对应 sheet，提取 English → 目标语言 的翻译映射
  3. 对英文版 blocks 进行文本替换，图片/按钮/steps/faq id 等全部复用
  4. POST /api/special-topic-pages/{id}/localizations 创建新 locale
  5. PUT publishedAt 发布
"""

import os
import sys
import json
import copy
import argparse
import requests
import openpyxl

# ── 配置 ─────────────────────────────────────────────────────────────────────

CMS_TOKEN = os.environ.get(
    "CMS_TOKEN",
    "943d4d58e9c61ed7ed300b801991e19e4c0f5ff395577c340a187347b1670fcf4d9026a39eff43d63a9dae041afa582ae85db8148dcc80110db98f56a3129366df98f20ccc690264afd8f061fcee8fba747d2cc4ad13f1b59897e2bdcae1b2fb930aba1ee498f866e459905cf03b6b17f4fa955f34ea45e9f327d9b0ca7cb9d2",
)
CMS_BASE = os.environ.get("CMS_BASE", "http://pdfagile-cms.aix-test-k8s.iweikan.cn")

EXCEL_PATH = os.environ.get(
    "LOCALIZE_EXCEL",
    os.path.expanduser("~/Downloads/专题页文案与多语言本地化-更新至20260408.xlsx"),
)

# locale code → Excel 列标题映射
LOCALE_TO_EXCEL_COL = {
    "fr":      "French",
    "zh-Hant": "Traditional Chinese",
    "es":      "Spanish",
    "de":      "German",
    "pt":      "Portuguese",
    "it":      "Italian",
    "ja":      "Japanese",
    "ko":      "Korean",
    "ar":      "Arabic",
    "id":      "Indonesian",
    "vi":      "Vietnamese",
    "th":      "Thai",
    "ms":      "Malay",
    "tr":      "Turkish",
    "pl":      "Polish",
    "nl":      "Dutch",
    "ro":      "Romanian",
    "hi":      "Hindi",
}

# ── CMS helpers ───────────────────────────────────────────────────────────────

def headers():
    return {"Authorization": f"Bearer {CMS_TOKEN}"}

def headers_json():
    return {**headers(), "Content-Type": "application/json"}


def fetch_en_page(page_id: int) -> dict:
    """拉取英文版完整结构，包含 blocks 所有子字段（image、buttons、steps、faq 等）"""
    url = (
        f"{CMS_BASE}/api/special-topic-pages/{page_id}"
        "?populate[blocks][populate]=*"
        "&populate[seo][populate]=*"
        "&locale=en"
    )
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["attributes"]


# ── Excel translation map ─────────────────────────────────────────────────────

def build_translation_map(sheet_name: str, locale: str) -> dict:
    """
    读取 Excel sheet，返回 {english_text: translated_text} 映射。
    空值或无翻译的条目不加入映射（保留英文原文）。
    """
    col_name = LOCALE_TO_EXCEL_COL.get(locale)
    if not col_name:
        raise ValueError(f"不支持的 locale: {locale}，支持的有: {list(LOCALE_TO_EXCEL_COL.keys())}")

    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"找不到 Excel 文件: {EXCEL_PATH}")

    wb = openpyxl.load_workbook(EXCEL_PATH)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Excel 中找不到 sheet: '{sheet_name}'，可用的有: {wb.sheetnames}")

    ws = wb[sheet_name]
    headers_row = [cell.value for cell in ws[1]]

    # 找列索引
    try:
        en_col = headers_row.index("English")
    except ValueError:
        raise ValueError("Excel sheet 中找不到 'English' 列")
    try:
        tr_col = headers_row.index(col_name)
    except ValueError:
        raise ValueError(f"Excel sheet 中找不到 '{col_name}' 列")

    translation_map = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        en = row[en_col] if len(row) > en_col else None
        tr = row[tr_col] if len(row) > tr_col else None
        if en and tr and str(en).strip() and str(tr).strip():
            translation_map[str(en).strip()] = str(tr).strip()

    print(f"  翻译表加载完成：共 {len(translation_map)} 条翻译（sheet: {sheet_name}, locale: {locale}）")
    return translation_map


def translate(text, t_map: dict) -> str:
    """
    精确匹配翻译，找不到则返回原文。
    会做以下标准化处理再匹配：
    - 去首尾空白
    - 合并连续空格为单空格
    """
    if not text:
        return text
    import re
    key = re.sub(r'\s+', ' ', str(text).strip())
    # 同样标准化 t_map 的 key 来匹配
    for k, v in t_map.items():
        k_norm = re.sub(r'\s+', ' ', str(k).strip())
        if k_norm == key:
            return v
    return text


# ── Block 转换：文本替换，图片/按钮/关联 id 复用 ──────────────────────────────

def strip_media_to_id(field_val):
    """
    将 {"data": {"id": 123, "attributes": {...}}} 转为 123（Strapi 写入时只需要 id）。
    {"data": null} → None
    """
    if isinstance(field_val, dict):
        data = field_val.get("data")
        if data is None:
            return None
        if isinstance(data, dict):
            return data.get("id")
    return field_val


def strip_buttons(buttons: list) -> list:
    """
    将 buttons 列表转为可写入格式，保留结构，去掉只读属性。
    支持两种格式：
      - feature-hero button: {id, theme, href, label, target, isExternal, disabled}
      - cta button: {id, theme, link: {href, label, ...}}
    """
    if not buttons:
        return []
    result = []
    for btn in buttons:
        if "link" in btn:
            # cta 格式：只传 id（复用已有记录）
            result.append({"id": btn["id"], "theme": btn["theme"]})
        else:
            # feature-hero 格式
            b = {
                "theme":      btn.get("theme"),
                "href":       btn.get("href"),
                "label":      btn.get("label"),
                "target":     btn.get("target"),
                "isExternal": btn.get("isExternal", False),
                "disabled":   btn.get("disabled", False),
            }
            if btn.get("image"):
                img_id = strip_media_to_id(btn["image"])
                if img_id:
                    b["image"] = img_id
            result.append(b)
    return result


def strip_steps(steps: list, t_map: dict) -> list:
    """step-cards 的 steps 子项：翻译 customizeText，复用 media id"""
    if not steps:
        return []
    result = []
    for s in steps:
        step = {
            "layout":        s.get("layout"),
            "theme":         s.get("theme"),
            "text":          s.get("text"),
            "customizeText": s.get("customizeText"),  # step 文本不在 Excel 里，保留英文
            "title":         s.get("title"),
            "customizeTitle": s.get("customizeTitle", ""),
            "topTitle":      s.get("topTitle"),
        }
        # 复用 media
        if s.get("media"):
            mid = strip_media_to_id(s["media"])
            if mid:
                step["media"] = mid
        result.append(step)
    return result


def strip_faq(faq_items: list, t_map: dict) -> list:
    """
    faq 条目：翻译 question 和 answer。
    answer 在 Strapi 里是 HTML，Excel 里是纯文本。
    先尝试 HTML 精确匹配，再尝试去掉 <p> 标签后匹配纯文本，找不到保留英文。
    """
    if not faq_items:
        return []
    result = []
    for item in faq_items:
        q = translate(item.get("question"), t_map)
        # answer：先整体匹配 HTML，再尝试去 <p> 标签匹配纯文本
        raw_ans = item.get("answer", "")
        translated_ans = translate(raw_ans, t_map)
        if translated_ans == raw_ans:
            # 去 HTML 标签后再试
            import re
            plain = re.sub(r'<[^>]+>', '', raw_ans).strip()
            plain_tr = translate(plain, t_map)
            if plain_tr != plain:
                # 找到翻译，包回 <p>
                translated_ans = f"<p>{plain_tr}</p>"
        result.append({"question": q, "answer": translated_ans})
    return result


def strip_trusted_by(items: list) -> list:
    """trust-by 的 trustedBy 子项：直接复用（品牌 label 不翻译）"""
    if not items:
        return []
    return [{"id": item["id"], "label": item["label"]} for item in items]


def convert_block(block: dict, t_map: dict, locale: str) -> dict:
    """
    将英文版 block 转换为目标语言版本：
    - 文本字段：查翻译表，找不到保留英文
    - media/image 字段：提取 id 复用
    - buttons/steps/faq 等嵌套结构：专项处理
    - 只读字段（id）：去掉（由 Strapi 自动生成）
    """
    comp = block["__component"]
    b = {"__component": comp}

    if comp == "feature.feature-hero":
        b["topTitle"]        = translate(block.get("topTitle"), t_map)
        b["title"]           = translate(block.get("title"), t_map)
        b["subtitle"]        = translate(block.get("subtitle"), t_map)
        b["layout"]          = block.get("layout")
        b["jsonData"]        = block.get("jsonData")   # 下载链接不翻译
        b["theme"]           = block.get("theme")
        # 复用 backgroundImage
        bg_id = strip_media_to_id(block.get("backgroundImage"))
        if bg_id:
            b["backgroundImage"] = bg_id
        # 翻译 buttons 的 label，其余字段保留（不传 image 字段，避免 Strapi 校验报错）
        raw_btns = block.get("buttons", [])
        new_btns = []
        for btn in raw_btns:
            new_btn = {
                "theme":      btn.get("theme"),
                "href":       btn.get("href"),
                "label":      translate(btn.get("label"), t_map),
                "target":     btn.get("target"),
                "isExternal": btn.get("isExternal", False),
                "disabled":   btn.get("disabled", False),
            }
            new_btns.append(new_btn)
        b["buttons"] = new_btns

    elif comp == "feature.panel":
        b["layout"]          = block.get("layout")
        b["theme"]           = block.get("theme")
        b["text"]            = block.get("text")
        b["customizeText"]   = translate(
            # customizeText 带 HTML 标签，去掉后匹配
            block.get("customizeText", "").replace("<p>", "").replace("</p>", "").strip()
            if block.get("customizeText") else block.get("customizeText"),
            t_map
        )
        # 如果翻译表找到的是纯文本，包回 <p> 标签
        if b["customizeText"] and not b["customizeText"].startswith("<"):
            b["customizeText"] = f"<p>{b['customizeText']}</p>"
        b["title"]           = translate(block.get("title"), t_map)
        b["customizeTitle"]  = block.get("customizeTitle", "")
        b["topTitle"]        = translate(block.get("topTitle"), t_map)
        # 复用 media / backgroundImage / icon
        media_id = strip_media_to_id(block.get("media"))
        if media_id:
            b["media"] = media_id
        bg_id = strip_media_to_id(block.get("backgroundImage"))
        if bg_id:
            b["backgroundImage"] = bg_id
        icon_id = strip_media_to_id(block.get("icon"))
        if icon_id:
            b["icon"] = icon_id

    elif comp == "feature.specific-features":
        # subFeatures 是内嵌 component，需要翻译 title 和 text，不传 id（新建）
        subs = []
        for sf in block.get("subFeatures", []):
            sub = {
                "layout":         sf.get("layout"),
                "theme":          sf.get("theme"),
                "text":           translate(sf.get("text"), t_map),
                "customizeText":  sf.get("customizeText", ""),
                "title":          translate(sf.get("title"), t_map),
                "customizeTitle": sf.get("customizeTitle", ""),
                "topTitle":       sf.get("topTitle"),
            }
            media_id = strip_media_to_id(sf.get("media"))
            if media_id:
                sub["media"] = media_id
            subs.append(sub)
        b["subFeatures"] = subs
        if block.get("mainFeature"):
            b["mainFeature"] = block["mainFeature"]
        bg_id = strip_media_to_id(block.get("backgroundImage"))
        if bg_id:
            b["backgroundImage"] = bg_id

    elif comp == "feature.step-cards":
        b["title"]    = translate(block.get("title"), t_map)
        b["theme"]    = block.get("theme")
        b["subtitle"] = translate(block.get("subtitle"), t_map)
        b["steps"]    = strip_steps(block.get("steps", []), t_map)

    elif comp == "feature.trust-by":
        b["title"]  = translate(block.get("title"), t_map)
        b["label"]  = block.get("label")
        bg_id = strip_media_to_id(block.get("backgroundImage"))
        if bg_id:
            b["backgroundImage"] = bg_id
        # trustedBy 内嵌 component 在 POST localization 时不能传 id（报500），不传即可
        # 后续通过 patch_localization 用 PUT 补全（PUT 同样不支持），故留空

    elif comp == "blocks.faq":
        b["title"]          = translate(block.get("title"), t_map)
        b["theme"]          = block.get("theme")
        b["customizeTitle"] = block.get("customizeTitle", "")
        b["faq"]            = strip_faq(block.get("faq", []), t_map)
        bg_id = strip_media_to_id(block.get("backgroundImage"))
        if bg_id:
            b["backgroundImage"] = bg_id

    elif comp == "blocks.cta":
        b["theme"] = block.get("theme")
        b["text"]  = block.get("text")
        bg_id = strip_media_to_id(block.get("background"))
        if bg_id:
            b["background"] = bg_id
        # header：新建（不传 id，POST/PUT localization 不允许跨实体复用 component id）
        if block.get("header"):
            h = block["header"]
            b["header"] = {
                "theme":          h.get("theme"),
                "label":          h.get("label"),
                "title":          h.get("title"),
                "customizeTitle": h.get("customizeTitle", ""),
                "customizeText":  h.get("customizeText", ""),
            }
        # buttons：新建（不传 id）
        b["buttons"] = [{"theme": btn["theme"]} for btn in block.get("buttons", [])]

    else:
        # 未知 component：原样复制，去掉 id
        b.update({k: v for k, v in block.items() if k != "id"})

    return b


# ── 主流程 ────────────────────────────────────────────────────────────────────

def fetch_fr_blocks(new_id: int) -> list:
    """拉取已创建的 localization 的 blocks（带 id），用于后续 PUT 补全"""
    url = (
        f"{CMS_BASE}/api/special-topic-pages/{new_id}"
        "?populate[blocks][populate]=*"
    )
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json()["data"]["attributes"].get("blocks", [])


def build_patch_blocks(fr_blocks: list, en_blocks: list, t_map: dict) -> list:
    """
    构建 PUT 用的完整 blocks 数组：
    - 保留所有已创建 block 的 id
    - 对 feature.trust-by 补入 trustedBy（从英文版取 label 列表，新建不传 id）
    - 其他 block 只传必要字段 + id，保持不变
    """
    # 英文版 trust-by 的 trustedBy labels
    en_trusted_labels = []
    for b in en_blocks:
        if b["__component"] == "feature.trust-by":
            en_trusted_labels = [{"label": t["label"]} for t in b.get("trustedBy", [])]
            break

    result = []
    for fb in fr_blocks:
        comp = fb["__component"]
        bid = fb["id"]

        if comp == "feature.trust-by":
            entry = {
                "id":        bid,
                "__component": comp,
                "title":     fb.get("title"),
                "label":     fb.get("label"),
                "trustedBy": en_trusted_labels,  # 补入品牌列表
            }
            bg_id = strip_media_to_id(fb.get("backgroundImage"))
            if bg_id:
                entry["backgroundImage"] = bg_id
            result.append(entry)

        elif comp == "feature.specific-features":
            # subFeatures 已经在 POST 时正确创建，带 id 保留即可
            subs = []
            for sf in fb.get("subFeatures", []):
                sub = {
                    "id":            sf["id"],
                    "layout":        sf.get("layout"),
                    "theme":         sf.get("theme"),
                    "text":          sf.get("text"),
                    "customizeText": sf.get("customizeText", ""),
                    "title":         sf.get("title"),
                    "customizeTitle": sf.get("customizeTitle", ""),
                    "topTitle":      sf.get("topTitle"),
                }
                media_id = strip_media_to_id(sf.get("media"))
                if media_id:
                    sub["media"] = media_id
                subs.append(sub)
            result.append({
                "id":           bid,
                "__component":  comp,
                "subFeatures":  subs,
            })

        elif comp == "blocks.cta":
            # header 和 buttons 已在 POST 时新建，带 id 保留
            entry = {
                "id":       bid,
                "__component": comp,
                "theme":    fb.get("theme"),
                "text":     fb.get("text"),
            }
            bg_id = strip_media_to_id(fb.get("background"))
            if bg_id:
                entry["background"] = bg_id
            if fb.get("header"):
                h = fb["header"]
                entry["header"] = {
                    "id":             h["id"],
                    "theme":          h.get("theme"),
                    "label":          h.get("label"),
                    "title":          h.get("title"),
                    "customizeTitle": h.get("customizeTitle", ""),
                    "customizeText":  h.get("customizeText", ""),
                }
            entry["buttons"] = [{"id": btn["id"], "theme": btn["theme"]} for btn in fb.get("buttons", [])]
            result.append(entry)

        else:
            # 其他 block：只传 id 和 __component，保持不变
            result.append({"id": bid, "__component": comp})

    return result


def localize(page_id: int, locale: str, sheet_name: str, publish: bool = True):
    print(f"\n=== localize_special_topic_page ===")
    print(f"  page_id : {page_id}")
    print(f"  locale  : {locale}")
    print(f"  sheet   : {sheet_name}")
    print(f"  publish : {publish}")
    print()

    # 1. 拉取英文版
    print("[1/5] 拉取英文版结构...")
    en_attrs = fetch_en_page(page_id)
    en_blocks = en_attrs.get("blocks", [])
    print(f"  blocks 数量: {len(en_blocks)}")

    # 2. 读取翻译表
    print("[2/5] 读取 Excel 翻译表...")
    t_map = build_translation_map(sheet_name, locale)

    # 3. 构建 POST payload
    print("[3/5] 构建 payload...")
    new_blocks = []
    for block in en_blocks:
        converted = convert_block(block, t_map, locale)
        new_blocks.append(converted)
        print(f"  ✓ {block['__component']}  →  {converted.get('title', '')[:50] or '(no title)'}")

    payload = {
        "locale":      locale,
        "slug":        en_attrs["slug"] + f"-{locale}",
        "navbarStyle": en_attrs.get("navbarStyle"),
        "blocks":      new_blocks,
    }

    # 4. POST 创建 localization
    print(f"\n[4/5] 创建 {locale} localization...")
    url = f"{CMS_BASE}/api/special-topic-pages/{page_id}/localizations"
    resp = requests.post(url, headers=headers_json(), json=payload)
    if resp.status_code not in (200, 201):
        print(f"  ERROR {resp.status_code}: {resp.text}")
        sys.exit(1)

    result = resp.json()
    new_id = result.get("id")
    print(f"  创建成功！新 id = {new_id}, slug = {result.get('slug')}, locale = {result.get('locale')}")

    # 5. PUT 补全 trustedBy（POST 时无法传 trustedBy，需单独 PUT）
    print(f"[5/5] 补全 trustedBy 并发布...")
    fr_blocks = fetch_fr_blocks(new_id)
    patch_blocks = build_patch_blocks(fr_blocks, en_blocks, t_map)

    published_at = "2026-04-14T08:00:00.000Z" if publish else None
    patch_payload = {"data": {"blocks": patch_blocks}}
    if published_at:
        patch_payload["data"]["publishedAt"] = published_at

    patch_resp = requests.put(
        f"{CMS_BASE}/api/special-topic-pages/{new_id}",
        headers=headers_json(),
        json=patch_payload,
    )
    if patch_resp.status_code == 200:
        patch_data = patch_resp.json()["data"]["attributes"]
        print(f"  补全成功！publishedAt = {patch_data.get('publishedAt')}")
    else:
        print(f"  PATCH ERROR {patch_resp.status_code}: {patch_resp.text}")

    print(f"\n完成。")
    print(f"  CMS 后台: {CMS_BASE}/admin/content-manager/collectionType/api::special-topic-page.special-topic-page/{new_id}?plugins[i18n][locale]={locale}")
    return new_id
    return new_id


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="将 special-topic-page 英文版本地化为指定语言"
    )
    parser.add_argument("page_id",    type=int, help="英文版页面 ID（如 5）")
    parser.add_argument("locale",     type=str, help="目标语言代码（如 fr、de、es）")
    parser.add_argument("sheet_name", type=str, help="Excel sheet 名称（如 'Organize PDF'）")
    parser.add_argument("--no-publish", action="store_true", help="创建后不自动发布（保持 draft）")
    args = parser.parse_args()

    localize(
        page_id    = args.page_id,
        locale     = args.locale,
        sheet_name = args.sheet_name,
        publish    = not args.no_publish,
    )
