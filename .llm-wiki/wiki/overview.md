---
tags: [cover-maker, flask, auto-publish, pdf-agile, python]
date: 2026-04-10
---

# Cover Maker — Project Overview

## 简介

Cover Maker 是一个 Python + Flask Web 应用，为 PDF Agile 品牌提供两项核心能力：

1. **封面图生成**：通过 Web UI 上传图片 + 填标题，批量生成三种规格的博客封面图
2. **Auto Publish**：全自动抓取热点 → AI 写文 → 生成封面 → 发布到 CMS（英文 + 法文双语）

## 技术栈

| 层 | 技术 |
|---|---|
| Web 服务 | Flask 3.x，运行于 `0.0.0.0:5299` |
| 图像处理 | Pillow + aggdraw（贝塞尔曲线） |
| AI 调用 | `dvcode` CLI（封装 Claude Sonnet / Gemini Flash） |
| 热点抓取 | Tavily API |
| CMS | Strapi REST API（pdfagile-cms） |
| 线上部署 | Vercel（仅封面生成功能） |

## 封面模式

| 模式 | 尺寸 | 文件 |
|---|---|---|
| HowToTips | 1130×860 | `make_cover.py` |
| Blog | 1200×630 | `make_howtotips2_cover.py` |
| Templates (PDF Agile) | 1200×630 | `make_pdfagile_cover.py` |

## Auto Publish 流水线

```
Tavily 抓热点
  → dvcode AI 规划选题
  → dvcode AI 生成英文文章
  → SEO 审核（cs-seo-audit skill）
  → dvcode AI 翻译法文
  → dvcode /nanobanana 生成封面右图
  → make_howtotips2_cover 合成封面
  → Strapi CMS 发布（EN + FR）
```

## 入口文件

| 文件 | 作用 |
|---|---|
| `app.py` | Flask 主服务，含 Cover Maker UI + Auto Publish UI + SSE 接口 |
| `auto_publish.py` | 全自动发布流水线逻辑 |
| `publish_article.py` | Strapi CMS REST API 客户端 |
| `启动.command` | macOS 双击启动脚本 |
| `api/index.py` | Vercel 部署入口 |

## 启动方式

```bash
# 安装依赖（首次）
/usr/bin/python3 -m pip install -r requirements.txt --user

# 启动（双击或命令行）
./启动.command
# → http://127.0.0.1:5299
# → http://127.0.0.1:5299/auto-publish
```

## 外部依赖

- `dvcode` CLI（必须在 PATH 中）
- Tavily API Key（hardcoded in `auto_publish.py`）
- CMS Bearer Token（hardcoded in `publish_article.py`）
- SEO checker：`~/.easyclaw/skills/cs-seo-audit/scripts/seo_checker.py`
