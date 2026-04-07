#!/usr/bin/env python3
"""
PDF Agile CMS 文章自动发布工具

用法：
  python3 publish_article.py

或直接调用：
  from publish_article import publish_article
  publish_article(
      title="...",
      slug="...",
      sub_title="...",
      content="<p>...</p>",
      cover_image_path="/path/to/cover.png",
      ...
  )

CMS 字段参考（固定值）：
  category:        1  = How-to & Tips
  box:             1  = yellow-pdf converter (Windows CTA)
  banners:         1  = Accelerate your PDF workflow
                   6  = Top list（alternatives/比较类文章用这个）
  tags:            1  = Edit PDF
                   15 = Convert from PDF
                   16 = Convert to PDF
                   17 = Manage PDF
                   2  = Marketing
                   21 = Troubleshoot
  relatedArticles: 传文章id列表，自动找同类文章
"""

import os, sys, json, requests

# ── 配置 ────────────────────────────────────────────────
TOKEN = "943d4d58e9c61ed7ed300b801991e19e4c0f5ff395577c340a187347b1670fcf4d9026a39eff43d63a9dae041afa582ae85db8148dcc80110db98f56a3129366df98f20ccc690264afd8f061fcee8fba747d2cc4ad13f1b59897e2bdcae1b2fb930aba1ee498f866e459905cf03b6b17f4fa955f34ea45e9f327d9b0ca7cb9d2"
BASE  = "http://pdfagile-cms.aix-test-k8s.iweikan.cn"

HEADERS     = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# ── 固定资源 ID（从CMS查询得到，不要改）────────────────
CATEGORY_HOW_TO_TIPS = 1
BOX_PDF_CONVERTER    = 1   # yellow-pdf converter
BANNER_ACCELERATE    = 1   # Accelerate your PDF workflow
BANNER_TOP_LIST      = 6   # Top list（alternatives类文章）
TAG_EDIT_PDF         = 1
TAG_MARKETING        = 2
TAG_CONVERT_FROM_PDF = 15
TAG_CONVERT_TO_PDF   = 16
TAG_MANAGE_PDF       = 17
TAG_TROUBLESHOOT     = 21


def upload_image(image_path: str, alt_text: str = "") -> int:
    """上传图片到 media library，返回 image id"""
    filename = os.path.basename(image_path)
    name     = os.path.splitext(filename)[0]
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/api/upload",
            headers=HEADERS,
            files={"files": (filename, f, "image/png")},
            data={"fileInfo": json.dumps({
                "name": name,
                "alternativeText": alt_text or name,
                "caption": alt_text or name,
            })}
        )
    resp.raise_for_status()
    image_id = resp.json()[0]["id"]
    print(f"  ✓ 图片上传成功 id={image_id}")
    return image_id


def find_related_articles(keywords: list[str], exclude_id: int = None, limit: int = 3) -> list[int]:
    """按关键词搜索相关文章，返回id列表"""
    found = []
    for kw in keywords:
        if len(found) >= limit:
            break
        resp = requests.get(
            f"{BASE}/api/articles",
            headers=HEADERS,
            params={
                "filters[title][$containsi]": kw,
                "fields[0]": "id",
                "fields[1]": "title",
                "pagination[pageSize]": 5,
            }
        )
        if resp.status_code != 200:
            continue
        for a in resp.json().get("data", []):
            aid = a["id"]
            if aid != exclude_id and aid not in found:
                found.append(aid)
                print(f"  → 相关文章 id={aid} {a['attributes']['title'][:50]}")
            if len(found) >= limit:
                break
    return found[:limit]


def publish_article(
    title: str,
    slug: str,
    content: str,
    cover_image_path: str,
    sub_title: str        = "",
    read_time: int        = 5,
    heat: int             = 50,
    category: int         = CATEGORY_HOW_TO_TIPS,
    box: int              = BOX_PDF_CONVERTER,
    banners: list         = None,
    tags: list            = None,
    related_keywords: list = None,
    related_articles: list = None,
    seo_title: str        = "",
    seo_description: str  = "",
    seo_keywords: str     = "",
) -> dict:
    """
    完整发布流程：上传封面图 → 创建文章 → 补充 relatedArticles
    返回 {"id": ..., "slug": ..., "url": ...}
    """
    print(f"\n{'='*60}")
    print(f"发布文章：{title}")
    print(f"{'='*60}")

    # 1. 上传封面图
    print("\n[1/3] 上传封面图...")
    image_id = upload_image(cover_image_path, alt_text=title)

    # 2. 创建文章
    print("\n[2/3] 创建文章...")
    payload = {
        "data": {
            "title":       title,
            "slug":        slug,
            "subTitle":    sub_title or None,
            "content":     content,
            "readTime":    read_time,
            "heat":        heat,
            "ready":       True,
            "locale":      "en",
            "image":       image_id,
            "category":    category,
            "box":         box,
            "banners":     banners  or [BANNER_TOP_LIST],
            "tags":        tags     or [TAG_MANAGE_PDF],
            "seo": {
                "metaTitle":       seo_title       or f"{title} | PDF Agile",
                "metaDescription": seo_description or sub_title or "",
                "keywords":        seo_keywords    or "",
            }
        }
    }

    resp = requests.post(f"{BASE}/api/articles", headers=HEADERS_JSON, json=payload)
    resp.raise_for_status()
    article = resp.json()["data"]
    article_id   = article["id"]
    article_slug = article["attributes"]["slug"]
    print(f"  ✓ 文章创建成功 id={article_id} slug={article_slug}")

    # 3. relatedArticles
    print("\n[3/3] 关联相关文章...")
    if related_articles is None:
        kws = related_keywords or title.split()[:3]
        related_articles = find_related_articles(kws, exclude_id=article_id)

    if related_articles:
        ra_payload = {
            "data": {
                "relatedArticles": {
                    "header": {
                        "theme": "primary",
                        "title": "Related Articles",
                        "label": None,
                        "customizeTitle": "",
                        "customizeText": ""
                    },
                    "articles": related_articles
                }
            }
        }
        resp2 = requests.put(
            f"{BASE}/api/articles/{article_id}",
            headers=HEADERS_JSON,
            json=ra_payload
        )
        resp2.raise_for_status()
        print(f"  ✓ relatedArticles 已设置: {related_articles}")

    url = f"https://www.pdfagile.com/blog/{article_slug}"
    print(f"\n{'='*60}")
    print(f"✅ 发布完成！")
    print(f"   Article ID : {article_id}")
    print(f"   URL        : {url}")
    print(f"{'='*60}\n")

    return {"id": article_id, "slug": article_slug, "url": url}


# ── 生成封面图工具函数 ───────────────────────────────────
def generate_cover(title: str, template: str = "mint", source_image: str = None) -> str:
    """
    用 make_howtotips2_cover 生成封面图，返回输出路径
    template: mint / warm / orange / teal / pink
    source_image: 右侧配图路径，不传则用纯色占位图
    """
    import tempfile
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from make_howtotips2_cover import make_howtotips2_cover

    if source_image is None:
        # 生成占位图
        img = Image.new("RGB", (800, 500), (30, 40, 80))
        draw = ImageDraw.Draw(img)
        draw.rectangle([40, 40, 760, 460], fill=(20, 30, 60))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        source_image = tmp.name

    out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    make_howtotips2_cover(source_image, title, template=template, output_path=out)
    return out


# ── CLI 示例入口 ─────────────────────────────────────────
if __name__ == "__main__":
    # ── 修改下面这些参数来发布新文章 ──────────────────────

    TITLE      = "The 8 Best Adobe Acrobat Alternatives to Use in 2026"
    SLUG       = "the-best-adobe-acrobat-alternatives-to-use"
    SUB_TITLE  = "Compare the top Adobe Acrobat alternatives for 2026 — from free tools to professional editors — and find the right PDF solution for your needs."
    READ_TIME  = 7
    TEMPLATE   = "teal"   # mint / warm / orange / teal / pink
    SOURCE_IMG = None     # 传本地图片路径，或 None 用占位图

    CONTENT = """<p><span style="color:#0E101A;">Adobe Acrobat has long been the industry standard for PDF management — but its steep subscription pricing, resource-heavy desktop client, and locked-down feature gating have pushed many users to seek better alternatives. Whether you're a student, freelancer, or enterprise team, there are now powerful tools that match or exceed Acrobat's capabilities at a fraction of the cost.</span></p>
<p><span style="color:#0E101A;">This guide reviews the 8 best Adobe Acrobat alternatives in 2026, evaluated across editing depth, conversion accuracy, pricing, privacy, and platform support.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>1. PDF Agile — The Best Overall Adobe Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">PDF Agile is the most complete desktop alternative to Adobe Acrobat for Windows users. It delivers professional-grade PDF editing, AI-enhanced OCR, batch processing, and secure offline management — all under a one-time license with no recurring subscription fees.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;"><strong>Full PDF Editing:</strong> Modify text, images, links, and page layouts directly.<br/><strong>AI-Enhanced OCR:</strong> Convert scanned documents with 22-language support.<br/><strong>Batch Conversion:</strong> Process multiple files simultaneously.<br/><strong>Offline Processing:</strong> All files stay local — zero cloud exposure.<br/><strong>40+ Tools:</strong> Merge, split, compress, annotate, sign, and more.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">One-time license pricing. No usage caps or file size limits. Complete data privacy. Superior performance on large documents.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Windows only.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Power users and professionals who want Acrobat-level capabilities without the subscription cost or privacy trade-offs.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>2. PDFelement — The Best Feature-for-Feature Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">Wondershare PDFelement is purpose-built as a direct Acrobat replacement, offering a near-identical feature set with a cleaner interface and significantly lower pricing. It covers the full spectrum of PDF work: editing, conversion, OCR, forms, signatures, and AI-powered document analysis.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Full-featured PDF editor with text, image, and page editing. AI assistant for document summarization and translation. Advanced form creation and data extraction. Batch processing for high-volume workflows. Cross-platform: Windows, Mac, iOS, Android.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Closest feature parity to Acrobat. Intuitive, modern interface. Affordable annual and perpetual licensing. Strong AI feature set.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Subscription required for cloud features. Heavier than lightweight alternatives.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Teams and individuals migrating from Acrobat who want a familiar workflow at lower cost.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>3. Foxit PDF Editor — The Best Enterprise Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">Foxit PDF Editor has served enterprise customers as an Acrobat alternative for over two decades. Its robust security features, Active Directory integration, and centralized management console make it the preferred choice for IT-managed deployments.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Enterprise-grade security with RMS and AD RMS support. Centralized policy management for IT administrators. Full PDF editing and advanced form handling. ConnectedPDF technology for document tracking. Cross-platform desktop and cloud access.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Proven enterprise reliability. Strong compliance and security features. Lighter footprint than Acrobat. Competitive volume licensing.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Interface feels dated compared to newer tools. Advanced features have a learning curve.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">IT departments and large organizations requiring centralized PDF management with enterprise security controls.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>4. PDF Expert — The Best Acrobat Alternative for Mac Users</strong></h2>
<p><span style="color:#0E101A;">For Mac, iPad, and iPhone users, PDF Expert by Readdle is the definitive Acrobat alternative. Native Apple Silicon performance, seamless iCloud sync, and deep Apple Pencil integration deliver an experience that feels far more natural than Acrobat on Apple hardware.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Precision text and image editing. Seamless iCloud Handoff between Mac, iPad, and iPhone. Apple Pencil annotation support. Smart redaction and content extraction. Enhanced reading mode with custom layouts.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Unrivaled speed on Apple Silicon. Award-winning interface. Privacy-first local processing. Tight Apple ecosystem integration.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Apple only. Premium annual pricing.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Mac and iPad users who want a polished, high-performance PDF tool deeply integrated with Apple's ecosystem.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>5. Smallpdf — The Best Browser-Based Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">Smallpdf brings the core of Acrobat's toolset to the browser — no installation, no setup, no platform lock-in. For users who primarily need conversion, compression, merging, and basic editing, Smallpdf covers everything with a clean, accessible interface.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">21+ PDF tools including convert, compress, merge, split, and e-sign. Desktop app for offline access. Google Drive and Dropbox integration. Team collaboration features on Pro plan.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Zero installation required. Works on any device with a browser. Reliable conversion accuracy. Clean, beginner-friendly design.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Free tier limited to 2 tasks per hour. No deep editing capabilities. Cloud processing raises privacy concerns.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Users who need occasional PDF tasks without software installation — students, remote workers, and light business users.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>6. PDFgear — The Best Free Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">PDFgear is the most capable free Adobe Acrobat alternative available today. Unlike other "free" tools that gate key features behind paywalls, PDFgear is genuinely unlimited — full editing, OCR, conversion, and an AI document copilot, all at zero cost.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Complete PDF editing with text, images, and annotations. AI copilot for summarization, translation, and Q&amp;A. Unrestricted file conversion and compression. Built-in OCR. No account or registration required.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">100% free, no hidden limits. Cross-platform (Windows, Mac, iOS, Android). Strong AI features. Privacy-first local processing.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Fewer enterprise features. Simpler interface than dedicated professional tools.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Budget-conscious individuals, students, and small teams who need comprehensive PDF capabilities without any cost.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>7. Nitro PDF Pro — The Best Acrobat Alternative for Windows Teams</strong></h2>
<p><span style="color:#0E101A;">Nitro PDF Pro targets Windows-based business teams with a familiar Microsoft Office-style ribbon interface, strong conversion accuracy, and a productivity-focused feature set. Its volume licensing and analytics dashboard make it an attractive choice for mid-market organizations.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Full PDF editing and creation. High-accuracy Word, Excel, and PowerPoint conversion. Advanced e-signature workflows. Nitro Analytics for usage tracking. Centralized license management.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Familiar Office-style interface reduces training time. Strong conversion accuracy. Team analytics and management. Competitive volume pricing.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Windows only. Less capable than Acrobat for complex document manipulation.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Windows-based business teams needing a managed, scalable PDF solution with usage analytics.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>8. LibreOffice Draw — The Best Free Open-Source Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;">LibreOffice Draw is often overlooked as a PDF editor, but it offers surprisingly capable PDF manipulation for users who prioritize open-source software and zero licensing cost. It handles text editing, annotation, and basic page management without any subscription.</span></p>
<h3><strong>Key Features</strong></h3>
<p><span style="color:#0E101A;">Open PDF files for direct editing. Basic text and image modification. Page manipulation and reordering. Export back to PDF. Cross-platform: Windows, Mac, Linux.</span></p>
<h3><strong>Pros</strong></h3>
<p><span style="color:#0E101A;">Completely free and open-source. No usage limits. Works on Linux (rare among PDF editors). No account or telemetry.</span></p>
<h3><strong>Cons</strong></h3>
<p><span style="color:#0E101A;">Limited editing precision. No OCR. No form creation or e-signatures. Interface not optimized for PDF work.</span></p>
<h3><strong>Best For</strong></h3>
<p><span style="color:#0E101A;">Linux users and open-source advocates who need basic PDF editing without any commercial software dependency.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<h2><strong>How to Choose the Right Adobe Acrobat Alternative</strong></h2>
<p><span style="color:#0E101A;"><strong>Budget:</strong> For zero cost, PDFgear (feature-rich) or LibreOffice Draw (open-source). For a one-time purchase, PDF Agile. For subscription, PDFelement or Foxit offer the best Acrobat parity.<br/><strong>Platform:</strong> PDF Expert for Apple; PDF Agile or Nitro for Windows; Smallpdf for any browser; LibreOffice for Linux.<br/><strong>Editing Depth:</strong> For true document editing, PDF Agile (Windows) or PDFelement. For basic tasks, Smallpdf or PDFgear.<br/><strong>Privacy:</strong> Offline-first tools like PDF Agile, PDF24, or LibreOffice for sensitive documents.</span></p>
<p><span style="color:#0E101A;">&nbsp;</span></p>
<p><span style="color:#0E101A;">Adobe Acrobat remains a capable tool, but it's no longer the only choice — or even the best one for most users. The alternatives above cover every use case, budget, and platform. Match your workflow to the right tool, and you'll likely find something faster, cheaper, and better suited to how you actually work with PDFs.</span></p>"""

    SEO_TITLE = "The 8 Best Adobe Acrobat Alternatives to Use in 2026 | PDF Agile"
    SEO_DESC  = "Compare the 8 best Adobe Acrobat alternatives for 2026 — from free tools to enterprise editors. Find the right PDF solution for your workflow, budget, and platform."
    SEO_KW    = "Adobe Acrobat alternatives, PDF editor, best PDF software 2026, PDF tools, Acrobat replacement"

    # 生成封面图
    print("生成封面图...")
    cover_path = generate_cover(TITLE, template=TEMPLATE, source_image=SOURCE_IMG)
    print(f"  ✓ 封面图: {cover_path}")

    # 发布
    result = publish_article(
        title              = TITLE,
        slug               = SLUG,
        sub_title          = SUB_TITLE,
        content            = CONTENT,
        cover_image_path   = cover_path,
        read_time          = READ_TIME,
        heat               = 50,
        banners            = [BANNER_TOP_LIST],
        tags               = [TAG_MANAGE_PDF],
        related_keywords   = ["PDF", "convert", "edit"],
        seo_title          = SEO_TITLE,
        seo_description    = SEO_DESC,
        seo_keywords       = SEO_KW,
    )
