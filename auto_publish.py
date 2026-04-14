"""
auto_publish.py — 全自动：抓热点 → AI规划 → AI写文(英+法) → AI生封面图 → 自动发布CMS

零配置，点按钮就跑。
"""

import os, re, json, subprocess, tempfile, base64, requests

# ── 常量（全部从环境变量读取，本地用 .env，线上在 Railway 里配置）────
TAVILY_API_KEY  = os.environ.get("TAVILY_API_KEY", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "sk-cp-6KWwIruCR98Euzmci7whjzcCmcVHP8gW0EXrqdw0qvk1Onz2-EIoflvD0a4oeQJ6ZZ7TcvVWs0jxKlLztKB-RHevISUk1c7RIT-2z6k2wH9takU-MXpKmIQ")
MINIMAX_BASE    = "https://api.minimaxi.com/anthropic"
MINIMAX_MODEL   = "MiniMax-M2.7"
MINIMAX_FAST    = "MiniMax-M2.7"

CMS_TOKEN = os.environ.get("CMS_TOKEN", "")
CMS_BASE  = os.environ.get("CMS_BASE", "http://pdfagile-cms.aix-test-k8s.iweikan.cn")
CMS_H     = {"Authorization": f"Bearer {CMS_TOKEN}", "Content-Type": "application/json"}

# 封面配色 — 根据关键词自动匹配
TEMPLATE_MAP = {
    "smallpdf":   "mint",
    "ilovepdf":   "teal",
    "acrobat":    "orange",
    "adobe":      "orange",
    "nitro":      "warm",
    "foxit":      "pink",
    "pdfelement": "teal",
    "updf":       "mint",
    "pdf24":      "pink",
    "default":    "mint",
}

# 已发布过的工具（持久化到本地文件，避免重复）
_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "published_tools.json")

def _load_published() -> list:
    if os.path.exists(_HISTORY_FILE):
        try:
            return json.load(open(_HISTORY_FILE, encoding="utf-8"))
        except Exception:
            pass
    return ["ilovepdf", "acrobat", "adobe acrobat"]

def _save_published(tools: list):
    with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(tools, f, ensure_ascii=False, indent=2)


# ── MiniMax API 调用 ──────────────────────────────────────

def minimax_ask(prompt: str, model: str = None, timeout: int = 180) -> str:
    """调用 MiniMax Anthropic 兼容 API，返回 assistant 完整回复。529 限流自动重试。"""
    import time
    if model is None:
        model = MINIMAX_MODEL
    headers = {
        "x-api-key": MINIMAX_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 8000,
        "thinking": {"type": "enabled", "budget_tokens": 1000},
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(5):
        resp = requests.post(
            f"{MINIMAX_BASE}/v1/messages",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        if resp.status_code == 529:
            wait = 15 * (attempt + 1)
            print(f"[minimax_ask] 529 限流，{wait}s 后重试 (attempt {attempt+1}/5)...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        # 兼容 thinking + text 两种 content block
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"].strip()
        return ""
    raise RuntimeError("MiniMax API 持续 529，已重试 5 次")


def minimax_image(prompt: str, ratio: str = "4:3") -> str:
    """
    调用 MiniMax 图片生成 API，返回本地临时文件路径。
    失败时返回 None。
    """
    # ratio 转换为具体尺寸
    size_map = {
        "4:3":  {"width": 1024, "height": 768},
        "16:9": {"width": 1280, "height": 720},
        "1:1":  {"width": 1024, "height": 1024},
        "3:4":  {"width": 768,  "height": 1024},
    }
    size = size_map.get(ratio, {"width": 1024, "height": 768})

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "image-01",
        "prompt": prompt,
        "width":  size["width"],
        "height": size["height"],
        "n": 1,
    }
    try:
        resp = requests.post(
            f"{MINIMAX_BASE}/image_generation",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # 支持 url 和 b64_json 两种返回格式
        images = data.get("data", {}).get("image_urls", []) or data.get("images", [])
        if not images:
            return None
        first = images[0]
        if isinstance(first, dict):
            url = first.get("url") or first.get("image_url")
        else:
            url = first

        if url and url.startswith("http"):
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(r.content)
            tmp.close()
            return tmp.name

        # b64 格式
        b64 = (first.get("b64_json") if isinstance(first, dict) else None)
        if b64:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(base64.b64decode(b64))
            tmp.close()
            return tmp.name

    except Exception as e:
        print(f"[minimax_image] 生图失败: {e}")
    return None


# ── Step 1: Tavily 热点抓取（全自动，不需要传 topic）────────

def fetch_trends() -> list[dict]:
    """
    真正的热点驱动：
    1. 先抓 Reddit/ProductHunt/Twitter 今天在抱怨/讨论哪些 PDF 工具
    2. 再搜这些工具的替代品需求
    返回带 source 标记的结果列表
    """
    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_API_KEY)

    # 第一轮：抓今日真实讨论（Reddit 最近帖子）
    hot_queries = [
        "pdf software frustrating slow expensive alternative reddit 2025 OR 2026",
        "switched from pdf tool better alternative reddit productHunt",
        "best pdf editor 2026 reddit recommendation",
        "pdf tool complaint cancel subscription alternative",
    ]

    seen_urls = set()
    results = []

    for q in hot_queries:
        try:
            resp = client.search(q, max_results=4, search_depth="advanced")
            for r in resp.get("results", []):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    results.append({
                        "title":   r.get("title", ""),
                        "url":     r["url"],
                        "snippet": r.get("content", "")[:400],
                        "score":   r.get("score", 0),
                        "source":  "hot",
                    })
        except Exception:
            pass

    # 第二轮：用 AI 从第一轮结果里提炼出被频繁提到的工具名，再深挖
    # 直接把 snippet 拼起来给下一步 AI 分析，这里只做数据收集
    # 补充一轮：搜具体工具名的替代品需求（基于第一轮出现频率高的词）
    tool_queries = [
        "foxit pdf editor alternative reddit 2026",
        "nitro pdf alternative cheaper reddit",
        "pdfelement vs alternatives 2026",
        "updf review alternative reddit 2026",
        "pdf24 vs pdfgear comparison reddit",
    ]

    for q in tool_queries:
        try:
            resp = client.search(q, max_results=3, search_depth="basic")
            for r in resp.get("results", []):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    results.append({
                        "title":   r.get("title", ""),
                        "url":     r["url"],
                        "snippet": r.get("content", "")[:400],
                        "score":   r.get("score", 0),
                        "source":  "tool",
                    })
        except Exception:
            pass

    # hot 来源权重翻倍，让 AI 更倾向热点
    for r in results:
        if r["source"] == "hot":
            r["score"] *= 2

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:15]


# ── Step 2: AI 规划（含自动选配色）──────────────────────────

def generate_article_plan(trends: list[dict]) -> dict:
    """AI 从真实热点讨论里分析选题，自动选配色模板。"""
    def clean(s):
        return re.sub(r'[\x00-\x1f]', ' ', str(s))

    # 把 hot 来源放在前面，让 AI 更注意
    hot   = [r for r in trends if r.get("source") == "hot"]
    other = [r for r in trends if r.get("source") != "hot"]

    hot_text = "\n".join(
        f"[热点] {clean(r['title'])}: {clean(r['snippet'][:200])}"
        for r in hot[:6]
    )
    tool_text = "\n".join(
        f"[工具讨论] {clean(r['title'])}: {clean(r['snippet'][:150])}"
        for r in other[:6]
    )

    already = ", ".join(_load_published())

    prompt = f"""你是 PDF Agile 博客编辑。下面是今天从 Reddit、ProductHunt 等平台抓取的真实用户讨论。

【今日热点讨论】
{hot_text}

【工具相关讨论】
{tool_text}

任务：
1. 仔细分析上面的讨论，找出用户最近在抱怨或主动寻求替代的 PDF 工具
2. 选一个搜索热度最高、用户痛点最明显的工具作为文章主角
3. 不能选这些已发布的工具：{already}
4. 选题逻辑要基于上面的真实讨论内容，不要凭空猜测

只输出 JSON，不要任何其他文字：

{{
  "title": "The 7 Best [Tool] Alternatives to Use in 2026",
  "slug": "the-best-[tool]-alternatives-to-use",
  "sub_title": "...",
  "seo_title": "The 7 Best [Tool] Alternatives to Use in 2026 | PDF Agile",
  "seo_description": "...",
  "keywords": "...",
  "topic_keyword": "[Tool]",
  "topic_reason": "一句话说明为什么选这个工具（基于热点数据）",
  "cover_prompt": "modern PDF software UI screenshot, clean minimal design, professional, high quality",
  "read_time": 7
}}"""

    raw = minimax_ask(prompt, model=MINIMAX_FAST)
    plan = _parse_json(raw)

    # 自动匹配配色
    tool_lower = plan.get("topic_keyword", "").lower()
    plan["template"] = next(
        (v for k, v in TEMPLATE_MAP.items() if k in tool_lower),
        TEMPLATE_MAP["default"]
    )

    return plan


# ── Step 3: AI 写英文正文 ─────────────────────────────────

def generate_article_en(plan: dict, trends: list[dict]) -> str:
    """生成英文 HTML 正文，分两段生成，内置 SEO 要求。"""
    tool    = plan["topic_keyword"]
    title   = plan["title"]
    kw      = plan.get("keywords", f"{tool} alternatives, PDF editor").split(",")[0].strip()
    refs    = "\n".join(f"- {r['title']}: {r['snippet'][:120]}" for r in trends[:4])

    seo_rules = f"""SEO requirements (strictly follow):
- First paragraph must contain the primary keyword "{kw}" naturally
- Each H2 heading must include a relevant keyword variation
- Use the primary keyword "{kw}" 3-5 times total in the article (natural density, not stuffing)
- Every image placeholder comment must have descriptive alt text in this format: <!-- img alt="descriptive alt text here" -->
- Include 2-3 mentions of PDF Agile as a link, ONLY use this exact URL: <a href="https://www.pdfagile.com" style="color:#4A8FA0;">PDF Agile</a> — do NOT invent any other URLs or subpages
- At the end, add an FAQ section with 3 questions as H2 + p pairs (helps Google rich snippets)"""

    prompt1 = f"""You are a professional SEO blog writer for PDF Agile.

Write part 1 of a blog post: "{title}"
Primary keyword: {kw}
Competing tool: {tool}
References: {refs}

{seo_rules}

Output pure HTML only (p, h2, h3, strong, ul, li — each tag with style="color:#0E101A;"). No markdown fences.

Part 1 must include:
- H1 tag with the exact title: {title}
- Two intro paragraphs mentioning "{kw}" in the first paragraph
- Tools #1–#4: H2 heading with keyword, Key Features (3-4 bullets), Pros, Cons, Best For
- PDF Agile must be #1 as the best overall alternative, with a link to https://www.pdfagile.com

Output HTML directly:"""

    prompt2 = f"""You are a professional SEO blog writer for PDF Agile.

Write part 2 of a blog post: "{title}"
Primary keyword: {kw}

{seo_rules}

Output pure HTML only (p, h2, h3, strong, ul, li — each tag with style="color:#0E101A;"). No markdown fences.

Part 2 must include:
- Tools #5, #6, #7 (real {tool} alternatives, not PDF Agile), each with H2 heading, Key Features, Pros, Cons, Best For
- A closing "How to Choose" H2 section
- An FAQ section with exactly 3 questions as H2 headings + p answer pairs:
  - "What is the best free {tool} alternative?"
  - "Is PDF Agile better than {tool}?"
  - "What {tool} alternative works on Mac?"

Output HTML directly:"""

    part1 = minimax_ask(prompt1, model=MINIMAX_FAST, timeout=300)
    part2 = minimax_ask(prompt2, model=MINIMAX_FAST, timeout=300)
    content = part1 + "\n" + part2

    # 把所有 pdfagile.com 子路径链接统一替换成主域名，防止 AI 编造不存在的 URL
    content = re.sub(
        r'href="https?://(?:www\.)?pdfagile\.com/[^"]*"',
        'href="https://www.pdfagile.com"',
        content
    )
    return content


# ── Step 3b: SEO 审查 + AI 修复 ───────────────────────────

def seo_audit_and_fix(html: str, plan: dict) -> str:
    """
    用 seo_checker.py 扫描生成的 HTML，若分数 < 80 则让 AI 修复问题后返回。
    """
    import sys as _sys
    _sys.path.insert(0, "/Users/iceberg/.easyclaw/skills/cs-seo-audit/scripts")
    try:
        from seo_checker import analyze_html, compute_overall_score
    except ImportError:
        return html  # 找不到 seo_checker 就跳过

    results = analyze_html(html)
    score   = compute_overall_score(results)

    # 收集不通过的项
    issues = []
    for key, r in results.items():
        if not r.get("pass"):
            issues.append(f"- {key}: {r['note']}")

    if score >= 80 or not issues:
        return html

    issues_text = "\n".join(issues)
    kw = plan.get("keywords", plan.get("topic_keyword", "PDF")).split(",")[0].strip()

    fix_prompt = f"""You are an SEO expert. Fix the following issues in this HTML blog post.

Primary keyword: "{kw}"

SEO issues found (score: {score}/100):
{issues_text}

Rules:
- Fix ONLY the listed issues, do not rewrite the entire article
- Keep all existing content and structure
- Keep all style="color:#0E101A;" attributes
- No markdown fences
- Output the complete fixed HTML directly

HTML to fix:
{html[:6000]}"""

    fixed = minimax_ask(fix_prompt, model=MINIMAX_FAST, timeout=300)
    return fixed if fixed.strip().startswith("<") else html


# ── Step 4: AI 写法文正文 ─────────────────────────────────

def generate_article_fr(plan: dict, en_content: str) -> tuple[dict, str]:
    """根据英文版生成法文版，分两段翻译避免超时。"""
    tool = plan["topic_keyword"]
    mid  = len(en_content) // 2

    prompt1 = f"""Tu es un rédacteur SEO professionnel pour PDF Agile. Traduis ce contenu HTML en français naturel et professionnel.

Règles strictes :
- Garde tous les noms de logiciels en anglais (PDF Agile, {tool}, etc.)
- Conserve exactement les balises HTML avec style="color:#0E101A;"
- Pas de balises markdown

Contenu à traduire (partie 1) :
{en_content[:mid]}

Sortie HTML directement :"""

    prompt2 = f"""Tu es un rédacteur SEO professionnel pour PDF Agile. Traduis ce contenu HTML en français naturel et professionnel.

Règles strictes :
- Garde tous les noms de logiciels en anglais (PDF Agile, {tool}, etc.)
- Conserve exactement les balises HTML avec style="color:#0E101A;"
- Pas de balises markdown

Contenu à traduire (partie 2) :
{en_content[mid:]}

Sortie HTML directement :"""

    fr1 = minimax_ask(prompt1, model=MINIMAX_FAST, timeout=300)
    fr2 = minimax_ask(prompt2, model=MINIMAX_FAST, timeout=300)
    fr_html = fr1 + "\n" + fr2

    fr_plan = {
        **plan,
        "title":           f"Les 7 meilleures alternatives à {tool} en 2026",
        "slug":            plan["slug"] + "-fr",
        "seo_title":       f"Les 7 meilleures alternatives à {tool} en 2026 | PDF Agile",
        "seo_description": plan["seo_description"],
        "keywords":        plan["keywords"],
        "locale":          "fr",
    }
    return fr_plan, fr_html


# ── Step 5: 生成封面图 ────────────────────────────────────

def generate_cover(title: str, cover_prompt: str, template: str) -> str:
    """
    优先用 nanobanana AI 生图作为封面右侧图；
    失败则降级用纯色占位图。
    返回最终封面文件路径。
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from make_howtotips2_cover import make_howtotips2_cover
    from PIL import Image, ImageDraw

    # 尝试 AI 生图
    src_image = minimax_image(cover_prompt, ratio="4:3")

    # 降级：纯色占位图
    if not src_image:
        img = Image.new("RGB", (800, 600), (15, 25, 50))
        ImageDraw.Draw(img).rectangle([30, 30, 770, 570], fill=(10, 18, 40))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        tmp.close()
        src_image = tmp.name
        ai_generated = False
    else:
        ai_generated = True

    out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    out.close()
    make_howtotips2_cover(src_image, title, template=template, output_path=out.name)

    if ai_generated:
        os.unlink(src_image)

    return out.name


# ── Step 6: 发布到 CMS ────────────────────────────────────

def publish_to_cms(plan: dict, content: str, cover_path: str) -> dict:
    from publish_article import publish_article
    return publish_article(
        title            = plan["title"],
        slug             = plan["slug"],
        sub_title        = plan.get("sub_title", ""),
        content          = content,
        cover_image_path = cover_path,
        read_time        = plan.get("read_time", 7),
        heat             = 99,
        banners          = [6],
        tags             = [17],
        related_keywords = [plan.get("topic_keyword", "PDF"), "PDF", "alternative"],
        seo_title        = plan.get("seo_title", ""),
        seo_description  = plan.get("seo_description", ""),
        seo_keywords     = plan.get("keywords", ""),
    )


def publish_localization_to_cms(en_id: int, plan: dict, content: str, cover_path: str, locale: str = "fr") -> dict:
    from publish_article import publish_localization
    return publish_localization(
        en_article_id    = en_id,
        title            = plan["title"],
        slug             = plan["slug"],
        content          = content,
        cover_image_path = cover_path,
        locale           = locale,
        sub_title        = plan.get("sub_title", ""),
        read_time        = plan.get("read_time", 7),
        heat             = 99,
        seo_title        = plan.get("seo_title", ""),
        seo_description  = plan.get("seo_description", ""),
        seo_keywords     = plan.get("keywords", ""),
    )


# ── 工具函数 ──────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    raw = re.sub(r'```(?:json)?\s*', '', raw)
    raw = re.sub(r'```', '', raw)
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError(f"AI 未返回有效 JSON：{raw[:200]}")
    js = match.group()
    js = re.sub(r'(?<=.)\n(?=.)', ' ', js)
    js = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', js)
    return json.loads(js)


# ── 完整流水线 ────────────────────────────────────────────

def run_pipeline(progress_cb=None) -> dict:
    """
    全自动：无需任何参数，点按钮就跑。
    返回 {en: {id, slug, url}, fr: {id, slug, url}, title}
    """
    def log(step, detail="", status="active"):
        print(f"[{step}] {detail}")
        if progress_cb:
            progress_cb(step, detail, status)

    # 1. 抓热点
    log("trends", "搜索热门 PDF 工具趋势...")
    trends = fetch_trends()
    log("trends", f"找到 {len(trends)} 条热点", "done")

    # 2. AI 规划
    log("plan", "AI 分析热点，决定文章选题...")
    plan = generate_article_plan(trends)
    reason = plan.get("topic_reason", "")
    log("plan", f"选题：{plan['title']}" + (f"（{reason}）" if reason else ""), "done")

    # 3. AI 写英文
    log("content", "AI 写英文正文...")
    en_content = generate_article_en(plan, trends)
    log("content", f"英文正文完成（{len(en_content)} 字符）", "done")

    # 3b. SEO 审查 + 修复
    log("seo", "SEO 审查中...")
    en_content = seo_audit_and_fix(en_content, plan)
    log("seo", "SEO 审查完成", "done")

    # 4. AI 写法文
    log("translate", "AI 翻译法文版...")
    fr_plan, fr_content = generate_article_fr(plan, en_content)
    log("translate", "法文版完成", "done")

    # 5. 生成封面（英法共用同一张）
    log("cover", "AI 生成封面图...")
    cover_path = generate_cover(
        title         = plan["title"],
        cover_prompt  = plan.get("cover_prompt", "modern PDF software interface, clean design"),
        template      = plan["template"],
    )
    log("cover", f"封面生成完成（配色：{plan['template']}）", "done")

    # 6. 发布英文版
    log("publish_en", "发布英文版到 CMS...")
    en_result = publish_to_cms(plan, en_content, cover_path)
    log("publish_en", f"英文版已发布：{en_result['url']}", "done")

    # 7. 法语版挂在英文版同一 id 下
    log("publish_fr", "发布法文版到 CMS（同一文章，fr locale）...")
    fr_result = publish_localization_to_cms(en_result["id"], fr_plan, fr_content, cover_path, locale="fr")
    log("publish_fr", f"法文版已发布：{fr_result['url']}", "done")

    # 记录已发布工具，避免下次重复选题
    published = _load_published()
    tool_lower = plan.get("topic_keyword", "").lower()
    if tool_lower and tool_lower not in published:
        published.append(tool_lower)
        _save_published(published)

    # 清理封面临时文件
    try:
        os.unlink(cover_path)
    except Exception:
        pass

    log("done", f"全部完成！英文：{en_result['url']}", "done")

    return {
        "title":  plan["title"],
        "en":     en_result,
        "fr":     fr_result,
        "template": plan["template"],
    }
