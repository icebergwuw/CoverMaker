"""
auto_publish.py — 热点抓取 + AI 写文 + 发布 CMS 核心逻辑

依赖：
  pip install tavily-python requests pillow
  npm install -g deepv-code（已登录）
"""

import os, re, json, subprocess, tempfile
import requests

# ── 常量 ─────────────────────────────────────────────────
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "TAVILY_KEY_REMOVED")
DVCODE_MODEL   = "claude-sonnet-4-6"

CMS_TOKEN = "943d4d58e9c61ed7ed300b801991e19e4c0f5ff395577c340a187347b1670fcf4d9026a39eff43d63a9dae041afa582ae85db8148dcc80110db98f56a3129366df98f20ccc690264afd8f061fcee8fba747d2cc4ad13f1b59897e2bdcae1b2fb930aba1ee498f866e459905cf03b6b17f4fa955f34ea45e9f327d9b0ca7cb9d2"
CMS_BASE  = "http://pdfagile-cms.aix-test-k8s.iweikan.cn"

# ── Step 1: Tavily 热点抓取 ───────────────────────────────

def fetch_trends(topic: str = "PDF tools alternatives 2026") -> list[dict]:
    """
    用 Tavily 搜索热门 PDF 工具话题，返回候选列表。
    每条: {title, url, snippet, score}
    """
    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_API_KEY)

    queries = [
        f"best {topic} site:reddit.com OR site:producthunt.com",
        f"{topic} review comparison 2026",
        f"alternatives to popular PDF tools 2026",
    ]

    seen_urls = set()
    results = []
    for q in queries:
        resp = client.search(q, max_results=5, search_depth="basic")
        for r in resp.get("results", []):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r["url"],
                    "snippet": r.get("content", "")[:300],
                    "score":   r.get("score", 0),
                })

    # 按 score 降序，取前10
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


# ── Step 2: dvcode AI 调用 ────────────────────────────────

def dvcode_ask(prompt: str, model: str = DVCODE_MODEL) -> str:
    """
    调用 dvcode CLI，返回 assistant 的完整文字回复。
    """
    proc = subprocess.run(
        ["dvcode", "-m", model, "--output-format", "stream-json", "--yolo", prompt],
        capture_output=True, text=True, timeout=120
    )
    output = proc.stdout + proc.stderr

    # 从 stream-json 中提取 assistant content
    lines = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("type") == "message" and d.get("role") == "assistant":
                lines.append(d.get("content", ""))
        except Exception:
            pass

    return "\n".join(lines).strip()


# ── Step 3: AI 生成文章结构 ───────────────────────────────

def generate_article_plan(trends: list[dict]) -> dict:
    """
    根据热点数据，让 AI 决定写哪篇文章，返回完整计划。
    返回: {title, slug, sub_title, keywords, seo_title, seo_description, topic_keyword}
    """
    def clean(s):
        return re.sub(r'[\x00-\x1f]', ' ', s)

    trends_text = "\n".join(
        f"- {clean(r['title'])} ({r['url']}): {clean(r['snippet'][:150])}"
        for r in trends[:8]
    )

    prompt = f"""你是 PDF Agile 博客编辑。根据以下热点搜索结果，选择一个最适合写"best alternatives"类文章的主题。

热点数据：
{trends_text}

要求：
1. 选一个竞品工具（如 iLovePDF、Smallpdf、Adobe Acrobat 等），写 "The X Best [工具名] Alternatives to Use in 2026"
2. 不能和已有文章重复（iLovePDF、Acrobat 已写过）
3. 输出严格的 JSON，不要任何其他文字，格式：

{{
  "title": "The 7 Best [Tool] Alternatives to Use in 2026",
  "slug": "the-best-[tool]-alternatives-to-use",
  "sub_title": "副标题，SEO优化，160字符以内",
  "seo_title": "The 7 Best [Tool] Alternatives to Use in 2026 | PDF Agile",
  "seo_description": "SEO meta description，155字符以内",
  "keywords": "keyword1, keyword2, keyword3, keyword4",
  "topic_keyword": "[Tool]",
  "read_time": 7
}}"""

    raw = dvcode_ask(prompt)

    # 提取并清洗 JSON（处理 markdown 代码块和控制字符）
    raw = re.sub(r'```(?:json)?\s*', '', raw)
    raw = re.sub(r'```', '', raw)
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError(f"AI 未返回有效 JSON：{raw[:200]}")
    json_str = match.group()
    # 把 JSON 字符串值内的字面换行变成空格（JSON不允许字段值含未转义换行）
    # 方法：在引号内的换行替换为空格
    json_str = re.sub(r'(?<=.)\n(?=.)', ' ', json_str)
    # 清除所有剩余控制字符（保留换行供结构使用）
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
    return json.loads(json_str)


def generate_article_content(plan: dict, trends: list[dict]) -> str:
    """
    根据计划生成完整文章 HTML 正文。
    """
    title    = plan["title"]
    tool     = plan["topic_keyword"]
    sub      = plan["sub_title"]

    # 提取相关参考内容
    refs = "\n".join(
        f"- {r['title']}: {r['snippet'][:200]}"
        for r in trends[:6]
    )

    prompt = f"""你是 PDF Agile 的 SEO 博客撰稿人，擅长写英文"best alternatives"类博客。

任务：为以下标题写一篇完整的博客文章正文。

标题：{title}
副标题：{sub}
竞品工具：{tool}

参考资料（热点内容）：
{refs}

写作要求：
1. 开头两段介绍为什么需要 {tool} 的替代品
2. 列出 7 个替代工具，每个包含：
   - H2 标题（序号 + 工具名 + 一句话定位）
   - Key Features（3-4条）
   - Pros / Cons
   - Best For
   - PDF Agile 必须是第一个，定位为最佳整体替代品
3. 结尾一段总结如何选择
4. 全程英文，专业但易读
5. 输出纯 HTML，只包含内容标签（p/h2/h3/strong/ul/li），每个标签加 style="color:#0E101A;"
6. 不要输出任何代码块标记（不要```html）

直接输出 HTML："""

    return dvcode_ask(prompt, model=DVCODE_MODEL)


# ── Step 4: 生成封面图 ────────────────────────────────────

def generate_cover_for_article(title: str, template: str = "mint") -> str:
    """
    生成封面图，返回本地临时文件路径。
    使用纯色占位图作为右侧图片。
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from make_howtotips2_cover import make_howtotips2_cover
    from PIL import Image, ImageDraw

    # 生成深色占位图
    img = Image.new("RGB", (800, 500), (15, 25, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 770, 470], fill=(10, 18, 40))
    tmp_src = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp_src.name)
    tmp_src.close()

    out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    out.close()
    make_howtotips2_cover(tmp_src.name, title, template=template, output_path=out.name)
    os.unlink(tmp_src.name)
    return out.name


# ── Step 5: 发布到 CMS ────────────────────────────────────

def publish_to_cms(plan: dict, content: str, cover_path: str) -> dict:
    """
    封装 publish_article.py 的逻辑，直接发布，返回 {id, slug, url}
    """
    from publish_article import publish_article

    return publish_article(
        title            = plan["title"],
        slug             = plan["slug"],
        sub_title        = plan.get("sub_title", ""),
        content          = content,
        cover_image_path = cover_path,
        read_time        = plan.get("read_time", 6),
        heat             = 99,
        banners          = [6],   # Top list
        tags             = [17],  # Manage PDF
        related_keywords = [plan["topic_keyword"], "PDF", "alternative"],
        seo_title        = plan.get("seo_title", ""),
        seo_description  = plan.get("seo_description", ""),
        seo_keywords     = plan.get("keywords", ""),
    )


# ── 完整流水线（供 Flask 调用）────────────────────────────

def run_pipeline(
    topic: str = "PDF tools alternatives 2026",
    template: str = "mint",
    progress_cb=None,
) -> dict:
    """
    完整执行：抓热点 → AI规划 → AI写文 → 生成封面 → 发布CMS
    progress_cb(step: str, detail: str) 用于 SSE 推送进度
    返回 {id, slug, url, title}
    """
    def log(step, detail=""):
        print(f"[{step}] {detail}")
        if progress_cb:
            progress_cb(step, detail)

    log("trends", "正在抓取热点...")
    trends = fetch_trends(topic)
    log("trends_done", f"找到 {len(trends)} 条热点")

    log("plan", "AI 规划文章...")
    plan = generate_article_plan(trends)
    log("plan_done", f"标题：{plan['title']}")

    log("content", "AI 写文章正文...")
    content = generate_article_content(plan, trends)
    log("content_done", f"正文长度：{len(content)} 字符")

    log("cover", "生成封面图...")
    cover_path = generate_cover_for_article(plan["title"], template=template)
    log("cover_done", f"封面：{cover_path}")

    log("publish", "发布到 CMS...")
    result = publish_to_cms(plan, content, cover_path)
    os.unlink(cover_path)
    log("done", f"发布成功：{result['url']}")

    return {**result, "title": plan["title"]}
